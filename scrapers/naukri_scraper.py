import requests
from bs4 import BeautifulSoup
import logging
import urllib.parse
from typing import List

from models import Job

logger = logging.getLogger(__name__)

def fetch_jobs(job_title: str) -> List[Job]:
    """
    Fetches job listings from Naukri by scraping the HTML search results page.
    """
    # Naukri typically expects search terms separated by hyphens (e.g. python-developer-jobs)
    formatted_title = urllib.parse.quote(job_title.replace(" ", "-").lower())
    url = f"https://www.naukri.com/{formatted_title}-jobs"
    
    # Essential headers to masquerade as a real browser
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }
    
    jobs: List[Job] = []
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # 1. Edge Case: Bot Protection / Captcha block check
        # Naukri uses Akamai/Cloudflare which might return a captcha or "Access Denied" page
        if "Access Denied" in response.text or "Pardon Our Interruption" in response.text:
            logger.error("Bot protection triggered on Naukri. Access Denied.")
            return jobs
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 2. Edge Case: HTML Structure Changes
        # Find job wrappers using a flexible lambda targeting known class variations
        job_elements = soup.find_all('div', class_=lambda x: x and ('jobTuple' in x or 'srp-jobtuple-wrapper' in x or 'cust-job-tuple' in x))
        
        if not job_elements:
            logger.warning("No job elements found on Naukri. HTML structure might have changed or no results exist.")
            return jobs
            
        for elem in job_elements:
            # 3. Edge Case: Partial Data (Missing fields)
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
            # Sometimes salary is inside a title attribute if it's truncated
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
                salary=salary
            )
            jobs.append(job)
            
    except requests.exceptions.Timeout:
        logger.error("Timeout while fetching jobs from Naukri.")
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error fetching from Naukri: {e}")
        
    return jobs
