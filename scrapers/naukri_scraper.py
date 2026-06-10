import os
import logging
import urllib.parse
from typing import List, Optional

from pydantic import BaseModel, Field

from firecrawl import FirecrawlApp
from dotenv import load_dotenv

from models import Job
from scrapers.retry import retry_call
from scrapers.throttle import shared_limiter

load_dotenv()

logger = logging.getLogger(__name__)

DOMAIN = "naukri.com"
MAX_PAGES = 5


class NaukriJobSchema(BaseModel):
    title: str = Field(description="The job title")
    company: str = Field(description="The company name")
    location: str = Field(description="The job location")
    salary: Optional[str] = Field(description="The salary or salary range, e.g. '10-15 Lacs PA'", default=None)
    link: str = Field(description="The URL to the job listing")


class NaukriExtractSchema(BaseModel):
    jobs: List[NaukriJobSchema]


def _extract_page(app: FirecrawlApp, urls: list) -> List[Job]:
    """
    Extracts job data from Naukri for the given list of Firecrawl URLs.

    Retries on Firecrawl transient errors (timeouts, 5xx, etc.).
    Uses Firecrawl's built-in anti-bot protection and JS rendering.
    """
    jobs: List[Job] = []

    shared_limiter.wait(DOMAIN)

    try:
        response = retry_call(
            app.extract,
            kwargs={"urls": urls, "schema": NaukriExtractSchema.model_json_schema()},
            max_retries=3,
            base_delay=2.0,  # Firecrawl is slower, start with a longer delay
            retryable_exceptions=(TimeoutError, ConnectionError, IOError),
        )
    except Exception as e:
        logger.error(f"Naukri/Firecrawl failed: {e}")
        return jobs

    # Extract data from the response (handles multiple response formats)
    if hasattr(response, "data"):
        extract_data = response.data
    elif isinstance(response, dict):
        extract_data = response.get("data", response)
    else:
        extract_data = {}

    if not extract_data:
        logger.warning("No data extracted by Firecrawl for Naukri.")
        return jobs

    extracted_jobs = extract_data.get("jobs", [])
    if not extracted_jobs:
        logger.warning("Firecrawl extracted successfully but found no jobs matching the schema.")
        return jobs

    for item in extracted_jobs:
        job = Job(
            title=item.get("title", "Unknown Title"),
            company=item.get("company", "Unknown Company"),
            location=item.get("location", "Unknown Location"),
            link=item.get("link", ""),
            source_platform="Naukri",
            salary=item.get("salary"),
        )
        jobs.append(job)

    return jobs


def fetch_jobs(job_title: str, max_pages: int = MAX_PAGES) -> List[Job]:
    """
    Fetches job listings from Naukri using Firecrawl's extraction capabilities.

    Uses Firecrawl to bypass Naukri's Akamai bot protection and render
    the JavaScript-heavy page. Retries on transient failures.

    Args:
        job_title: The job title/keyword to search for.
        max_pages: Maximum number of result pages to fetch (default: 5).

    Returns:
        A list of Job objects.
    """
    api_key = os.getenv("FIRECRAWL_API_KEY")
    if not api_key:
        logger.error("FIRECRAWL_API_KEY is not set. Skipping Naukri scraper.")
        return []

    try:
        app = FirecrawlApp(api_key=api_key)
    except Exception as e:
        logger.error(f"Failed to initialize FirecrawlApp: {e}")
        return []

    formatted_title = urllib.parse.quote(job_title.replace(" ", "-").lower())

    # Build URLs for multiple pages
    # Naukri uses URL-based pagination: /{title}-jobs, /{title}-jobs-2, etc.
    urls = []
    for page in range(1, max_pages + 1):
        if page == 1:
            url = f"https://www.naukri.com/{formatted_title}-jobs"
        else:
            url = f"https://www.naukri.com/{formatted_title}-jobs-{page}"
        urls.append(url)

    logger.info(f"Naukri: requesting {len(urls)} page(s)...")
    jobs = _extract_page(app, urls)
    logger.info(f"Naukri total: {len(jobs)} jobs.")
    return jobs
