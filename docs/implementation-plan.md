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
