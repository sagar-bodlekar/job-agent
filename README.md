# Job Agent

A Python-based job scraping and application management tool.

## Overview
This project provides a suite of scrapers for job listings from various platforms (Naukri, RemoteOK, Wellfound) and utilities for handling applications, models, and retry logic.

## Features
- Scraping jobs from Naukri, RemoteOK, and Wellfound
- Model handling and data processing
- Retry and throttling mechanisms
- Simple CLI interface (entry point via `main.py`)

## Installation
```bash
pip install -r requirements.txt
```

## Usage
```bash
python app.py
```

## Project Structure
- `app.py` - main application entry point
- `main.py` - core logic
- `models.py` - data models
- `scrapers/` - scraper modules
- `tests/` - unit tests
- `docs/` - documentation

## Contributing
Feel free to open issues or submit pull requests.

## License
MIT