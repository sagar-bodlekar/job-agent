import requests
import logging
import urllib.parse
from typing import List

from models import Job

logger = logging.getLogger(__name__)

def fetch_jobs(job_title: str) -> List[Job]:
    """
    Fetches job listings from RemoteOK API based on the job title.
    """
    # Clean up the job title to be used as a tag (e.g., "Python Developer" -> "python-developer")
    tags = urllib.parse.quote(job_title.replace(" ", "-").lower())
    url = f"https://remoteok.com/api?tags={tags}"
    
    # RemoteOK frequently blocks requests without a standard User-Agent
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    jobs: List[Job] = []
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        # Ensure the response is a list as expected
        if not isinstance(data, list):
            logger.error(f"Unexpected JSON structure from RemoteOK: {type(data)}")
            return jobs
            
        for item in data:
            # RemoteOK's API always returns a legal/notice object as the first item in the list
            if item.get("legal") or not item.get("id"):
                continue
                
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
                salary=salary
            )
            jobs.append(job)
            
    except requests.exceptions.HTTPError as e:
        if response.status_code == 429:
            logger.error("Rate limited by RemoteOK API (HTTP 429).")
        elif response.status_code >= 500:
            logger.error(f"RemoteOK API is down (HTTP {response.status_code}).")
        else:
            logger.error(f"HTTP error occurred while fetching from RemoteOK: {e}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error fetching from RemoteOK: {e}")
    except ValueError:
        logger.error("Failed to parse JSON response from RemoteOK.")
        
    return jobs
