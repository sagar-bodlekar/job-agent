"""
Job Agent Web UI - Flask Application

Provides a modern web interface for the job scraping pipeline.
Users can select platforms, enter a job title, scrape jobs,
view results in the browser, and download as CSV.
"""

import csv
import io
import logging
import os
import time
import threading
from typing import List, Optional

from flask import Flask, jsonify, render_template, request, send_file
from flask_cors import CORS

from models import Job
from scrapers import naukri_scraper, remoteok_scraper, wellfound_scraper

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# In-memory cache for latest scraped jobs
_jobs_cache: List[Job] = []
_jobs_cache_lock = threading.Lock()

CSV_FILENAME = "jobs.csv"


def _scrape_platform(platform: str, job_title: str, max_pages: int) -> List[Job]:
    """Scrape a single platform and return jobs."""
    try:
        if platform == "naukri":
            return naukri_scraper.fetch_jobs(job_title, max_pages=max_pages)
        elif platform == "remoteok":
            return remoteok_scraper.fetch_jobs(job_title, max_pages=max_pages)
        elif platform == "wellfound":
            return wellfound_scraper.fetch_jobs(job_title, max_pages=max_pages)
        else:
            logger.warning(f"Unknown platform: {platform}")
            return []
    except Exception as e:
        logger.error(f"{platform} scraper failed: {e}")
        return []


def _write_csv(jobs: List[Job], filename: str = CSV_FILENAME) -> bool:
    """Write jobs to CSV file. Returns True on success."""
    headers = ["title", "company", "location", "salary", "link", "source_platform"]
    try:
        with open(filename, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            for job in jobs:
                writer.writerow({
                    "title": job.title,
                    "company": job.company,
                    "location": job.location,
                    "salary": job.salary or "",
                    "link": job.link,
                    "source_platform": job.source_platform,
                })
        return True
    except Exception as e:
        logger.error(f"CSV write failed: {e}")
        return False


def _jobs_to_dict(jobs: List[Job]) -> List[dict]:
    """Convert Job objects to dictionaries for JSON serialization."""
    return [
        {
            "title": j.title,
            "company": j.company,
            "location": j.location,
            "salary": j.salary or "",
            "link": j.link,
            "source_platform": j.source_platform,
        }
        for j in jobs
    ]


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.route("/")
def index():
    """Serve the main UI page."""
    return render_template("index.html")


@app.route("/api/scrape", methods=["POST"])
def scrape():
    """
    Scrape jobs from selected platforms.

    Request JSON:
        job_title (str): The job title/keyword to search for.
        platforms (list[str]): Platforms to scrape, e.g. ["naukri", "remoteok"].
        max_pages (int, optional): Max pages per platform, default 2.

    Response JSON:
        success (bool): Whether the overall operation succeeded.
        jobs (list[dict]): All scraped jobs.
        total (int): Total job count.
        platforms (list[str]): Platforms that returned results.
        filename (str): CSV filename.
    """
    data = request.get_json(silent=True) or {}
    job_title: str = data.get("job_title", "").strip()
    platforms: list = data.get("platforms", [])
    max_pages: int = int(data.get("max_pages", 2))

    if not job_title:
        return jsonify({"success": False, "error": "Job title is required"}), 400
    if not platforms:
        return jsonify({"success": False, "error": "Select at least one platform"}), 400

    logger.info(f"Scraping '{job_title}' on platforms: {platforms}")

    all_jobs: List[Job] = []
    for platform in platforms:
        jobs = _scrape_platform(platform, job_title, max_pages)
        all_jobs.extend(jobs)
        # Small delay between scrapers to be polite
        time.sleep(0.5)

    # Write to CSV
    csv_ok = _write_csv(all_jobs)

    # Update cache
    with _jobs_cache_lock:
        _jobs_cache.clear()
        _jobs_cache.extend(all_jobs)

    active_platforms = list({j.source_platform for j in all_jobs})

    return jsonify({
        "success": True,
        "jobs": _jobs_to_dict(all_jobs),
        "total": len(all_jobs),
        "platforms": active_platforms,
        "filename": CSV_FILENAME,
        "csv_written": csv_ok,
    })


@app.route("/api/jobs", methods=["GET"])
def get_jobs():
    """Return the latest scraped jobs from cache."""
    with _jobs_cache_lock:
        jobs = list(_jobs_cache)
    return jsonify({
        "success": True,
        "jobs": _jobs_to_dict(jobs),
        "total": len(jobs),
    })


@app.route("/download")
def download_csv():
    """Download the latest scraped jobs as CSV."""
    with _jobs_cache_lock:
        jobs = list(_jobs_cache)

    if not jobs:
        return jsonify({"success": False, "error": "No jobs to download"}), 404

    si = io.StringIO()
    writer = csv.writer(si)
    writer.writerow(["title", "company", "location", "salary", "link", "source_platform"])
    for j in jobs:
        writer.writerow([j.title, j.company, j.location, j.salary or "", j.link, j.source_platform])

    mem = io.BytesIO()
    mem.write(si.getvalue().encode("utf-8"))
    mem.seek(0)
    si.close()

    return send_file(
        mem,
        mimetype="text/csv",
        as_attachment=True,
        download_name="jobs.csv",
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import webbrowser
    port = int(os.environ.get("PORT", 5000))
    url = f"http://127.0.0.1:{port}"
    print(f"  Job Agent UI running at: {url}")
    webbrowser.open(url)
    app.run(debug=False, host="0.0.0.0", port=port)
