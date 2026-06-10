# Edge Case & Testing Strategy

This document outlines the edge cases that must be tested upon the completion of each implementation phase to ensure the system is robust and resilient.

## Phase 1: Project Setup & Core Structure
- **Missing Data**: Instantiating the `Job` model with missing optional fields (e.g., salary is None or empty).
- **Data Types**: Ensuring string constraints and type safety if strict typing is used.
- **Extremely Long Strings**: Handling unusually long URLs, job titles, or company names in the data model.

## Phase 2: RemoteOK Scraper (API)
- **Empty Results**: The API returns an empty array when searching for a highly obscure job title.
- **Malformed JSON / Missing Keys**: The API response structure changes slightly or omits expected keys (e.g., `company` is missing).
- **Rate Limiting**: Simulating or handling HTTP 429 Too Many Requests.
- **URL Encoding**: Searching for job titles with special characters (e.g., "C++ Developer", "C#", or spaces).
- **API Down**: Handling HTTP 5xx errors gracefully without crashing the app.

## Phase 3: Naukri Scraper (HTML)
- **Bot Protection/Captcha**: Handling scenarios where Naukri returns a captcha page or Cloudflare block instead of job listings.
- **HTML Structure Changes**: The CSS classes used for scraping change, resulting in `None` when trying to find elements.
- **Partial Data**: Listings that lack a salary, location, or company name.
- **Pagination Limits**: Scraper behavior when there is only 1 page of results vs. 100 pages.
- **Timeout**: The website takes too long to respond.

## Phase 4: Wellfound Scraper (Firecrawl)
- **Invalid API Key**: Firecrawl authentication fails.
- **Timeout / Slow Rendering**: Firecrawl takes too long to render the dynamic React/Next.js page.
- **Schema Mismatch**: The extracted data structure returned by Firecrawl doesn't match the expected schema.
- **Empty Output**: The crawler succeeds but fails to identify any job cards on the page.

## Phase 5: Orchestrator & CLI (`main.py`)
- **Missing Arguments**: User runs `python main.py` without providing a job title.
- **Partial Failure**: One or two scrapers fail (e.g., Naukri blocked, Firecrawl fails), but the orchestrator should still output results from the successful scrapers (e.g., RemoteOK).
- **Total Failure**: All scrapers fail. The application should exit cleanly and output an empty CSV with headers, or log a clear user-facing error.
- **File System Errors**: `jobs.csv` is currently open in another program (like Excel) causing a `PermissionError` during write.

## Phase 6: End-to-End Testing & Refinement
- **Cross-Platform Aggregation**: Ensuring jobs with the exact same title from different platforms are all present and distinguishable in the final CSV.
- **Special Character Search**: Running an E2E test with "UI/UX Designer" or "Node.js Developer" to ensure all three providers handle the encoding.
- **Performance**: Monitoring memory and time taken when aggregating a very large number of jobs across all three platforms.
