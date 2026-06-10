import argparse
import csv
import logging
import sys
from typing import List

from models import Job
from scrapers import remoteok_scraper, naukri_scraper, wellfound_scraper
from scrapers.throttle import shared_limiter
from scrapers.retry import retry_request

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def run_scrapers(job_title: str, max_pages: int = 5) -> List[Job]:
    """
    Runs all scrapers with rate limiting and aggregates the results.

    A global delay is enforced between different scrapers to avoid
    overwhelming any single domain or triggering bot protection.

    Args:
        job_title: The job title/keyword to search for.
        max_pages: Maximum result pages to fetch per scraper (default: 5).

    Returns:
        A combined list of Job objects from all successful scrapers.
    """
    all_jobs: List[Job] = []

    # --- RemoteOK ---
    logger.info(f"Searching for '{job_title}' on RemoteOK...")
    try:
        remoteok_jobs = remoteok_scraper.fetch_jobs(job_title, max_pages=max_pages)
        all_jobs.extend(remoteok_jobs)
        logger.info(f"Found {len(remoteok_jobs)} jobs on RemoteOK.")
    except Exception as e:
        logger.error(f"RemoteOK scraper failed: {e}")

    # Global delay between scrapers
    _global_delay(1.0)

    # --- Naukri ---
    logger.info(f"Searching for '{job_title}' on Naukri...")
    try:
        naukri_jobs = naukri_scraper.fetch_jobs(job_title, max_pages=max_pages)
        all_jobs.extend(naukri_jobs)
        logger.info(f"Found {len(naukri_jobs)} jobs on Naukri.")
    except Exception as e:
        logger.error(f"Naukri scraper failed: {e}")

    # Global delay between scrapers
    _global_delay(1.0)

    # --- Wellfound ---
    logger.info(f"Searching for '{job_title}' on Wellfound...")
    try:
        wellfound_jobs = wellfound_scraper.fetch_jobs(job_title, max_pages=max_pages)
        all_jobs.extend(wellfound_jobs)
        logger.info(f"Found {len(wellfound_jobs)} jobs on Wellfound.")
    except Exception as e:
        logger.error(f"Wellfound scraper failed: {e}")

    return all_jobs


def _global_delay(seconds: float = 1.0) -> None:
    """Enforces a minimum delay between different scraper executions."""
    import time
    logger.debug(f"Waiting {seconds}s before next scraper...")
    time.sleep(seconds)


def write_to_csv(jobs: List[Job], filename: str = "jobs.csv") -> bool:
    """Writes the list of Job objects to a CSV file."""
    if not jobs:
        logger.warning("No jobs found across any platform. Saving empty CSV with headers.")

    headers = ["title", "company", "location", "salary", "link", "source_platform"]

    try:
        with open(filename, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=headers)
            writer.writeheader()
            for job in jobs:
                writer.writerow({
                    "title": job.title,
                    "company": job.company,
                    "location": job.location,
                    "salary": job.salary if job.salary else "",
                    "link": job.link,
                    "source_platform": job.source_platform,
                })
        logger.info(f"Successfully saved {len(jobs)} jobs to {filename}.")
        return True
    except PermissionError:
        logger.error(f"Permission denied: Unable to write to '{filename}'. The file might be open in another program (like Excel).")
        return False
    except Exception as e:
        logger.error(f"An unexpected error occurred while writing to CSV: {e}")
        return False


def main(args=None):
    parser = argparse.ArgumentParser(description="Job Agent: Aggregates job listings from multiple platforms.")
    parser.add_argument("title", type=str, help="The job title to search for (e.g., 'Python Developer')")
    parser.add_argument(
        "--max-pages", type=int, default=5,
        help="Maximum result pages to fetch per platform (default: 5)",
    )

    parsed_args = parser.parse_args(args)
    job_title = parsed_args.title
    max_pages = parsed_args.max_pages

    logger.info(f"Starting Job Agent for title: '{job_title}' (max pages: {max_pages})")

    jobs = run_scrapers(job_title, max_pages=max_pages)

    success = write_to_csv(jobs)
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
