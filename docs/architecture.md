# Job Agent Architecture

## System Overview
The Job Agent is a modular Python application designed to aggregate job listings from various sources. It follows a provider-based architecture where each job source has its own specialized scraper.

## Components

### 1. Orchestrator (`main.py`)
- Acts as the entry point of the application.
- Accepts a `job_title` as a command-line argument.
- Coordinates the execution of all job scrapers.
- Aggregates the standardized results.
- Exports the data to `jobs.csv`.

### 2. Job Scrapers (`scrapers/`)
Each scraper is a dedicated module that implements a common interface: `fetch_jobs(job_title) -> List[Job]`.

> **Note**: During Phase 7 (Production Hardening), this interface will be extended with an optional `max_pages` parameter to support pagination.

- **`naukri_scraper.py`**:
  - Uses `requests` to fetch search result pages.
  - Uses `BeautifulSoup` to parse HTML and extract job details.
- **`remoteok_scraper.py`**:
  - Queries the `remoteok.com/api` endpoint.
  - Parses the JSON response directly.
- **`wellfound_scraper.py`**:
  - Utilizes the **Firecrawl API** to crawl Wellfound.
  - Leverages Firecrawl's ability to handle JavaScript rendering and bot detection.

### 3. Data Model (`models.py`)
- Defines a standardized `Job` dataclass with the following fields:
  - `title` — job title (e.g., "Python Developer")
  - `company` — employer name
  - `location` — job location (city, remote, etc.)
  - `salary` — optional salary string (e.g., "$50k - $100k" or "10-15 Lacs PA")
  - `link` — URL to the job listing
  - `source_platform` — origin platform ("Naukri", "RemoteOK", "Wellfound")
- Includes `__post_init__` type coercion to prevent downstream errors from unexpected scraper types.

### 4. Storage Engine
- CSV export logic is in `main.py` via the `write_to_csv()` function.
- Uses Python's `csv.DictWriter` for proper quoting and encoding handling.
- Handles permission errors (e.g., file open in Excel) and empty result sets gracefully.

## Data Flow
1. **Input**: User provides a search term (e.g., "Python Developer").
2. **Execution**: Orchestrator triggers `fetch_jobs` on all scrapers.
3. **Extraction**:
   - Naukri -> HTML -> List[Job]
   - RemoteOK -> API -> List[Job]
   - Wellfound -> Firecrawl -> List[Job]
4. **Aggregation**: Results are merged into a single list.
5. **Output**: List is written to `jobs.csv`.

## Error Handling
- Each scraper handles its own network errors and parsing exceptions gracefully (try/except per scraper).
- If one source fails, the orchestrator still proceeds with results from the others.
- The orchestrator wraps each scraper call in its own try/except block to isolate failures.
- Custom error messages are logged for each failure scenario (timeout, rate limit, bot block, etc.).

## Planned Enhancements

### Retry Mechanism
- All network calls should be wrapped with configurable retry logic (default: 3 attempts).
- Use exponential backoff with jitter to handle transient failures (timeouts, HTTP 429, HTTP 5xx).
- Retry exhaustion should log a warning and return gracefully (empty list, not crash).

### Pagination
- Each scraper should accept a `max_pages` parameter (default: 5) to control how many result pages to scrape.
- **RemoteOK**: Uses `?page=N` query parameter; loop until empty response or max pages.
- **Naukri**: Uses URL-based page segments; scrape consecutive pages until empty or max pages.
- **Wellfound**: Use Firecrawl's multi-page extraction capabilities or crawl mode.

### Rate Limiting / Throttling
- Add configurable delays between requests to avoid triggering bot protection or API rate limits.
- Apply per-domain delays (e.g., Naukri: 2s between requests, RemoteOK: 1s).
- Apply global delay between different scrapers in the orchestrator.
