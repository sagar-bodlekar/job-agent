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
- **Unicode / Non-ASCII**: Job titles or company names with emoji, CJK characters, or accented letters should not break the CSV output.

## Phase 7: Production Hardening — Retry, Pagination & Rate Limiting

### Retry Mechanism
- **Transient Failure Retry**: A timeout or HTTP 500 should trigger up to N retries with exponential backoff before returning an empty list.
- **Retry Exhaustion**: After all retries fail, log a warning and continue with results from other scrapers (don't halt the pipeline).
- **429 Retry**: HTTP 429 (Rate Limited) should retry with a longer backoff, respecting any `Retry-After` header if present.
- **Idempotency**: Ensure retrying a request does not cause duplicate job entries (each page fetch is independent).
- **Jitter**: Backoff delays should include random jitter to prevent thundering herd problems.

### Pagination
- **Max Pages Limit**: The scraper should not exceed the configured `max_pages` limit, even if more pages exist.
- **Last Page Detection**: The scraper must correctly detect the last page (empty results, 404, or no "next" link) to avoid infinite loops.
- **Off-by-One Errors**: Page numbering starts at 1, not 0. Ensure the first page is not duplicated.
- **Naukri URL Changes**: Naukri's URL schema for subsequent pages may differ from page 1. Test with real URLs.
- **Empty Middle Page**: If page 2 returns results but page 3 is empty, the scraper should stop (don't skip to page 4).
- **Very Large Result Sets**: 50+ pages of results should respect the max_pages limit and not overwhelm memory.

### Rate Limiting / Throttling
- **Per-Domain Delay**: Naukri should have a longer delay (e.g., 2-3s) than RemoteOK API (e.g., 1s) to avoid bot detection.
- **Orchestrator-Level Delay**: There should be a delay between running different scrapers (e.g., after Naukri completes, wait before starting Wellfound).
- **Concurrent Execution Safety**: If the tool is run twice simultaneously, rate limiting counters should not interfere (process-local counters are fine; no shared state needed).
- **User Configurable Delays**: Delays should be configurable so users can speed up or slow down scraping as needed.

## Cross-Cutting Edge Cases
- **Missing `.env` File**: `load_dotenv()` silently returns if `.env` doesn't exist. The system should log a warning.
- **Concurrent Writes**: Two instances of the agent running simultaneously could corrupt the CSV. Future consideration for file locking.
- **Disk Full During Write**: OS-level write errors (e.g., no space left on device) should surface a clear error and not silently corrupt data.
- **CSV Fields with Commas**: Job titles or company names containing commas must be properly quoted. Python's `csv.DictWriter` handles this, but tests should verify.
- **Salary Currency Inconsistency**: Naukri reports in INR ("10-15 Lacs PA"), RemoteOK reports in USD ("$50k - $100k"). No normalization is attempted; raw values are preserved as-is.
- **Location Format Variation**: Naukri uses city names ("Bangalore"), RemoteOK uses "Worldwide" or "Remote", Wellfound uses various formats. No normalization attempted.
- **Extremely Large CSV**: Thousands of jobs across all platforms should be handled without memory issues (streaming writes handle this).
