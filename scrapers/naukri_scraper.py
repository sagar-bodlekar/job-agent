import requests
from bs4 import BeautifulSoup
import logging
import urllib.parse
from typing import List, Optional

from models import Job
from scrapers.retry import retry_request
from scrapers.throttle import shared_limiter

logger = logging.getLogger(__name__)

DOMAIN = "naukri.com"
MAX_PAGES = 5


def _parse_page(job_title: str, page: int) -> tuple[List[Job], bool]:
    """
    Scrapes a single page of Naukri results.

    Returns:
        A tuple of (jobs_list, has_more_pages).
        has_more_pages is True if there might be additional pages.
    """
    formatted_title = urllib.parse.quote(job_title.replace(" ", "-").lower())

    # Naukri URL pattern:
    # Page 1: /{title}-jobs
    # Page 2+: /{title}-jobs-{page} (or with query param)
    if page == 1:
        url = f"https://www.naukri.com/{formatted_title}-jobs"
    else:
        url = f"https://www.naukri.com/{formatted_title}-jobs-{page}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }

    shared_limiter.wait(DOMAIN)

    jobs: List[Job] = []

    try:
        response = retry_request(
            "GET", url,
            max_retries=3,
            base_delay=1.0,
            headers=headers,
            timeout=10,
        )
    except requests.exceptions.RequestException as e:
        logger.error(f"Naukri page {page} failed after retries: {e}")
        return jobs, False

    # Bot Protection / Captcha block check
    if "Access Denied" in response.text or "Pardon Our Interruption" in response.text:
        logger.error("Bot protection triggered on Naukri. Access Denied.")
        return jobs, False

    soup = BeautifulSoup(response.text, 'html.parser')

    # Find job wrappers using a flexible lambda targeting known class variations
    job_elements = soup.find_all(
        'div', class_=lambda x: x and ('jobTuple' in x or 'srp-jobtuple-wrapper' in x or 'cust-job-tuple' in x)
    )

    if not job_elements:
        logger.warning(f"No job elements found on Naukri page {page}.")
        return jobs, False  # No results or last page

    for elem in job_elements:
        title_elem = elem.find('a', class_='title')
        title = title_elem.text.strip() if title_elem else "Unknown Title"
        link = title_elem['href'] if title_elem and title_elem.has_attr('href') else ""

        # Company name extraction
        company_elem = elem.find('a', class_=lambda x: x and 'comp-name' in x)
        company = company_elem.text.strip() if company_elem else "Unknown Company"

        # Location extraction
        loc_elem = elem.find('span', class_=lambda x: x and 'locWdth' in x)
        location = loc_elem.text.strip() if loc_elem else "Unknown Location"

        # Salary extraction
        sal_elem = elem.find('span', class_=lambda x: x and ('sal-wrap' in x or 'salary' in x.lower()))
        salary = None
        if sal_elem:
            salary = sal_elem.get('title') or sal_elem.text.strip()
            if salary and ("Not disclosed" in salary or "hidden" in salary.lower()):
                salary = None

        job = Job(
            title=title,
            company=company,
            location=location,
            link=link,
            source_platform="Naukri",
            salary=salary,
        )
        jobs.append(job)

    # Check if there's a "next" pagination link to determine if more pages exist
    has_more_pages = False
    pagination_elem = soup.find('a', class_=lambda x: x and 'next' in x.lower() if x else False)
    if pagination_elem and pagination_elem.get('href'):
        has_more_pages = True

    return jobs, has_more_pages


def fetch_jobs(job_title: str, max_pages: int = MAX_PAGES) -> List[Job]:
    """
    Fetches job listings from Naukri by scraping the HTML search results pages.

    Supports pagination across multiple pages.
    Retries on transient failures using exponential backoff.
    Respects rate limiting via the shared rate limiter.

    Args:
        job_title: The job title/keyword to search for.
        max_pages: Maximum number of result pages to fetch (default: 5).

    Returns:
        A list of Job objects.
    """
    all_jobs: List[Job] = []

    for page in range(1, max_pages + 1):
        page_jobs, has_more = _parse_page(job_title, page)
        all_jobs.extend(page_jobs)
        logger.info(f"Naukri page {page}: found {len(page_jobs)} jobs.")

        if not has_more or not page_jobs:
            break

    logger.info(f"Naukri total: {len(all_jobs)} jobs across all pages.")
    return all_jobs
