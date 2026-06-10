import argparse
import csv
import logging
import sys
from typing import List

from models import Job
from scrapers import remoteok_scraper, naukri_scraper, wellfound_scraper

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def run_scrapers(job_title: str) -> List[Job]:
    """Runs all scrapers and aggregates the results."""
    all_jobs: List[Job] = []

    logger.info(f"Searching for '{job_title}' on RemoteOK...")
    try:
        remoteok_jobs = remoteok_scraper.fetch_jobs(job_title)
        all_jobs.extend(remoteok_jobs)
        logger.info(f"Found {len(remoteok_jobs)} jobs on RemoteOK.")
    except Exception as e:
        logger.error(f"RemoteOK scraper failed: {e}")

    logger.info(f"Searching for '{job_title}' on Naukri...")
    try:
        naukri_jobs = naukri_scraper.fetch_jobs(job_title)
        all_jobs.extend(naukri_jobs)
        logger.info(f"Found {len(naukri_jobs)} jobs on Naukri.")
    except Exception as e:
        logger.error(f"Naukri scraper failed: {e}")

    logger.info(f"Searching for '{job_title}' on Wellfound...")
    try:
        wellfound_jobs = wellfound_scraper.fetch_jobs(job_title)
        all_jobs.extend(wellfound_jobs)
        logger.info(f"Found {len(wellfound_jobs)} jobs on Wellfound.")
    except Exception as e:
        logger.error(f"Wellfound scraper failed: {e}")

    return all_jobs

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
                    "source_platform": job.source_platform
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
    
    parsed_args = parser.parse_args(args)
    job_title = parsed_args.title
    
    logger.info(f"Starting Job Agent for title: '{job_title}'")
    
    jobs = run_scrapers(job_title)
    
    success = write_to_csv(jobs)
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()
