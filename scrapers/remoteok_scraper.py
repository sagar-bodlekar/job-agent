import requests
import logging
import urllib.parse
from typing import List

from models import Job
from scrapers.retry import retry_request
from scrapers.throttle import shared_limiter

logger = logging.getLogger(__name__)

# RemoteOK domain for rate limiting
DOMAIN = "remoteok.com"

# Maximum pages to fetch (used when no explicit arg is passed)
MAX_PAGES = 5


def _get_remoteok_tag(job_title: str) -> str:
    """
    Extract a valid RemoteOK tag from the job title.

    RemoteOK uses single-keyword tags, not multi-word phrases.
    For example: "Python Developer" -> "python", "Senior Software Engineer" -> "senior".
    Falls back to "developer" if the job title is empty.
    """
    words = job_title.lower().split()
    if not words:
        return urllib.parse.quote("developer")
    tag = words[0]
    # Log when the extracted tag is a significant truncation of the query
    if len(words) > 1:
        logger.info("RemoteOK tag '%s' extracted from query '%s'", tag, job_title)
    return urllib.parse.quote(tag)


def fetch_jobs(job_title: str, max_pages: int = MAX_PAGES) -> List[Job]:
    """
    Fetches job listings from RemoteOK API based on the job title.

    RemoteOK uses single-keyword tag filtering. The first word of the job title
    is used as the tag (e.g., "Python Developer" searches for "python").

    Supports pagination via the `?page=N` query parameter.
    Retries on transient failures using exponential backoff.
    Respects rate limiting via the shared rate limiter.

    Args:
        job_title: The job title/keyword to search for.
        max_pages: Maximum number of result pages to fetch (default: 5).

    Returns:
        A list of Job objects.
    """
    tag = _get_remoteok_tag(job_title)

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    all_jobs: List[Job] = []
    seen_ids: set = set()

    for page in range(1, max_pages + 1):
        # Only add &page=N for pages >= 2; page 1 is the default
        if page == 1:
            url = f"https://remoteok.com/api?tags={tag}"
        else:
            url = f"https://remoteok.com/api?tags={tag}&page={page}"

        shared_limiter.wait(DOMAIN)

        try:
            response = retry_request(
                "GET", url,
                max_retries=3,
                base_delay=1.0,
                headers=headers,
                timeout=10,
            )
        except requests.exceptions.RequestException as e:
            logger.error(f"RemoteOK page {page} failed after retries: {e}")
            # If the first page fails, stop entirely
            if page == 1:
                return []
            # If a subsequent page fails, we've already got some results
            break

        try:
            data = response.json()
        except ValueError:
            logger.error(f"Failed to parse JSON from RemoteOK page {page}.")
            if page == 1:
                return []
            break

        # Ensure the response is a list as expected
        if not isinstance(data, list):
            logger.error(f"Unexpected JSON structure from RemoteOK page {page}: {type(data)}")
            if page == 1:
                return []
            break

        page_jobs = 0
        for item in data:
            # RemoteOK's API always returns a legal/notice object as the first item
            if item.get("legal") or not item.get("id"):
                continue

            job_id = str(item.get("id"))
            # Deduplicate across pages (RemoteOK sometimes repeats listings)
            if job_id in seen_ids:
                continue
            seen_ids.add(job_id)

            title = item.get("position", "Unknown Title")
            company = item.get("company", "Unknown Company")
            location = item.get("location", "Remote")
            link = item.get("url", "")

            # Extract and format salary if available
            salary_min = item.get("salary_min")
            salary_max = item.get("salary_max")
            salary = None
            if salary_min and salary_max:
                salary = f"${salary_min} - ${salary_max}"
            elif salary_min:
                salary = f"${salary_min}+"
            elif salary_max:
                salary = f"Up to ${salary_max}"

            job = Job(
                title=title,
                company=company,
                location=location,
                link=link,
                source_platform="RemoteOK",
                salary=salary,
            )
            all_jobs.append(job)
            page_jobs += 1

        logger.info(f"RemoteOK page {page}: found {page_jobs} jobs.")

        # If this page returned no real jobs, we've hit the last page
        if page_jobs == 0:
            break

    logger.info(f"RemoteOK total: {len(all_jobs)} jobs across all pages.")
    return all_jobs
