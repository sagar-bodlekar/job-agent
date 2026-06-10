# Job Agent Context

## Problem Statement
Job seekers often have to visit multiple platforms to find relevant job openings for their desired roles. Manually searching across sites like Naukri, RemoteOK, and Wellfound is time-consuming and inefficient.

## Goal
To build an automated Job Agent that:
1. Fetches job listings for a specific job title from:
   - Naukri
   - RemoteOK
   - Wellfound
2. Aggregates the results.
3. Stores the final list of jobs in a CSV file for easy access and filtering.

## Target Platforms & Methods
- **Naukri**: HTML Scraping using `BeautifulSoup`.
- **RemoteOK**: Public JSON API (`remoteok.com/api`).
- **Wellfound**: Web scraping via **Firecrawl** to handle complex dynamic content and bot protection.

## Output
- A `jobs.csv` file containing job details: Title, Company, Location, Salary, Link, and Platform.

## Scope

### In Scope
- Search jobs by role/keyword across supported platforms
- Collect job information (title, company, location, salary, link)
- Normalize data into a common `Job` data model
- Export results to CSV for easy access and filtering
- Handle scraper failures gracefully without crashing the pipeline
- Support pagination (fetching multiple pages of results)
- Support retry logic for temporary network failures
- Support rate limiting/throttling to avoid IP/API blocks
- Maintain test coverage for all components

### Out of Scope
- HR email extraction or recruiter discovery
- Cover letter generation or resume tailoring
- Resume optimization or ATS scoring
- Automated job application or email sending
- CRM functionality or candidate tracking

## Environment Setup
1. Copy `.env.example` to `.env` (or create `.env` from scratch)
2. Set `FIRECRAWL_API_KEY` — required for Wellfound scraping (get a key from firecrawl.dev)
3. Run `pip install -r requirements.txt`

> **Note**: Only Wellfound requires the Firecrawl API key. Naukri and RemoteOK work without any API keys.
