# Phase-wise Implementation Plan

## Phase 1: Project Setup & Core Structure
**Goal**: Establish the foundational environment and data structures.
- Create the virtual environment and `requirements.txt`.
- Define the standardized `Job` data model in `models.py`.
- Create the directory structure (`scrapers/`, etc.).

## Phase 2: RemoteOK Scraper (API)
**Goal**: Implement the easiest and most reliable data source first.
- Create `scrapers/remoteok_scraper.py`.
- Implement a function to hit the `remoteok.com/api` endpoint with the job title.
- Map the JSON response to the `Job` data model.
- Test the scraper independently.

## Phase 3: Naukri Scraper (HTML)
**Goal**: Implement the HTML scraping logic.
- Create `scrapers/naukri_scraper.py`.
- Formulate the search URL based on the job title.
- Use `requests` to fetch the HTML.
- Use `BeautifulSoup` to extract title, company, location, salary, and link.
- Map extracted data to the `Job` data model.
- Handle potential missing fields gracefully.
- Test the scraper independently.

## Phase 4: Wellfound Scraper (Firecrawl)
**Goal**: Implement the scraper using Firecrawl to bypass bot protections.
- Create `scrapers/wellfound_scraper.py`.
- Ensure Firecrawl API key is loaded via environment variables.
- Use the Firecrawl Python SDK (or REST API) to crawl the Wellfound search page.
- Extract the necessary job details from the crawled data.
- Map the data to the `Job` data model.
- Test the scraper independently.

## Phase 5: Orchestrator & CLI (`main.py`)
**Goal**: Tie everything together into a usable command-line tool.
- Create `main.py`.
- Implement CLI argument parsing (e.g., using `argparse`) to accept the job title.
- Import and execute the `fetch_jobs` function from all three scrapers.
- Aggregate the resulting lists of `Job` objects into a single list.
- Implement the CSV writing logic to export the aggregated list to `jobs.csv`.

## Phase 6: End-to-End Testing & Refinement
**Goal**: Ensure the entire system works cohesively.
- Run the full CLI with various job titles (e.g., "Python Developer", "Data Scientist").
- Verify that `jobs.csv` is generated correctly and contains data from all successful sources.
- Add error logging to the orchestrator to handle cases where a specific scraper fails without crashing the whole application.
- Add brief inline documentation and type hints where necessary.

## Phase 7: Production Hardening — Retry, Pagination & Rate Limiting
**Goal**: Make the system resilient and complete enough to fetch real-world job data reliably.

### Retry Mechanism
- Add a utility module (`scrapers/retry.py`) with:
  - Configurable retry count (default: 3)
  - Exponential backoff with jitter
  - Retry-on specific exceptions (Timeout, HTTP 429, HTTP 5xx)
  - Logging at each retry attempt
- Wrap all scraper network calls with the retry helper.
- Tests: verify retry count, backoff delay behavior, and exhaustion fallback.

### Pagination
- Update `fetch_jobs` signature to accept optional `max_pages` parameter (default: 5).
- **RemoteOK**: Loop through pages using `?page=N` until empty or max pages reached.
- **Naukri**: Scrape consecutive pages using URL-based page patterns.
- **Wellfound**: Use Firecrawl's crawl/extract capabilities for multi-page fetching.
- Tests: mock multi-page responses and verify aggregation.

### Rate Limiting / Throttling
- Add a utility module (`scrapers/throttle.py`) with:
  - Per-domain request delay tracking
  - Global configurable delay between scrapers
- Integrate into each scraper's fetch loop and the orchestrator's scraper sequence.
- Tests: verify delay timing and request sequencing.

### Deliverables
- Retry utility module with tests
- Pagination support in all three scrapers with tests
- Rate limiting utility module with tests
- Updated orchestrator to coordinate throttled scraper execution
- Updated documentation reflecting the new capabilities
