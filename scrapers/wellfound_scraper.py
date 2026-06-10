import os
import logging
import urllib.parse
from typing import List, Optional
from pydantic import BaseModel, Field

from firecrawl import FirecrawlApp
from dotenv import load_dotenv

from models import Job

load_dotenv()

logger = logging.getLogger(__name__)

class WellfoundJobSchema(BaseModel):
    title: str = Field(description="The job title")
    company: str = Field(description="The company name")
    location: str = Field(description="The job location")
    link: str = Field(description="The URL to the job listing")
    salary: Optional[str] = Field(description="The salary or salary range", default=None)

class WellfoundExtractSchema(BaseModel):
    jobs: List[WellfoundJobSchema]

def fetch_jobs(job_title: str) -> List[Job]:
    """
    Fetches job listings from Wellfound using Firecrawl's extraction capabilities.
    """
    jobs: List[Job] = []
    
    api_key = os.getenv("FIRECRAWL_API_KEY")
    if not api_key:
        logger.error("FIRECRAWL_API_KEY is not set. Skipping Wellfound scraper.")
        return jobs

    try:
        app = FirecrawlApp(api_key=api_key)
    except Exception as e:
        logger.error(f"Failed to initialize FirecrawlApp: {e}")
        return jobs
    
    formatted_title = urllib.parse.quote(job_title.replace(" ", "-").lower())
    url = f"https://wellfound.com/role/l/{formatted_title}"
    
    try:
        response = app.scrape_url(url, params={
            'formats': ['extract'],
            'extract': {
                'schema': WellfoundExtractSchema.model_json_schema()
            }
        })
        
        extract_data = response.get('extract', {})
        if not extract_data:
             logger.warning("No data extracted by Firecrawl for Wellfound.")
             return jobs
             
        extracted_jobs = extract_data.get('jobs', [])
        if not extracted_jobs:
             logger.warning("Firecrawl extracted successfully but found no jobs matching the schema.")
             return jobs
             
        for item in extracted_jobs:
            job = Job(
                title=item.get("title", "Unknown Title"),
                company=item.get("company", "Unknown Company"),
                location=item.get("location", "Unknown Location"),
                link=item.get("link", ""),
                source_platform="Wellfound",
                salary=item.get("salary")
            )
            jobs.append(job)

    except Exception as e:
        logger.error(f"Error occurred while fetching from Wellfound using Firecrawl: {e}")
        
    return jobs
