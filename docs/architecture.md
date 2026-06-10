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
- Defines a standardized `Job` data structure (e.g., using a `dataclass` or `TypedDict`).
- Fields: `title`, `company`, `location`, `salary`, `link`, `source_platform`.

### 4. Storage Engine
- Simple CSV writer integrated into the orchestrator or a separate utility module (`utils/storage.py`).

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
- Each scraper should handle its own network errors and parsing exceptions gracefully.
- If one source fails, the orchestrator should still proceed with results from the others.
