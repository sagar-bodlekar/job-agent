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
- A `jobs.csv` file containing job details: Title, Company, Location, Salary, Link, HR Email(whom send to mail cover latter to apply job) and Platform.
