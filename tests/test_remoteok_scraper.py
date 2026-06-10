import unittest
from unittest.mock import patch, MagicMock
import requests
import json

from scrapers.remoteok_scraper import fetch_jobs, _get_remoteok_tag

# The scraper now calls retry_request -> requests.request (imported in scrapers.retry)
MOCK_PATH = "scrapers.retry.requests.request"


class TestRemoteOKScraper(unittest.TestCase):

    def _make_page_response(self, jobs_data: list, status_code: int = 200):
        """Helper to create a mock response with the given JSON data."""
        mock_response = MagicMock()
        mock_response.status_code = status_code
        mock_response.json.return_value = jobs_data
        return mock_response

    def test_fetch_jobs_success(self):
        with patch(MOCK_PATH) as mock_request:
            page_1_data = [
                {"legal": "API usage notice"},
                {
                    "id": "1",
                    "position": "Python Developer",
                    "company": "Tech Corp",
                    "location": "Worldwide",
                    "url": "https://remoteok.com/job/1",
                    "salary_min": 50000,
                    "salary_max": 100000,
                },
                {
                    "id": "2",
                    "position": "Backend Engineer",
                    # Simulating missing optional keys
                },
            ]
            # Page 2 is empty (just legal notice, no real jobs)
            page_2_data = [{"legal": "API usage notice"}]

            mock_request.side_effect = [
                self._make_page_response(page_1_data),
                self._make_page_response(page_2_data),
            ]

            jobs = fetch_jobs("Python", max_pages=5)

            self.assertEqual(len(jobs), 2)
            self.assertEqual(jobs[0].title, "Python Developer")
            self.assertEqual(jobs[0].salary, "$50000 - $100000")
            self.assertEqual(jobs[1].title, "Backend Engineer")
            self.assertEqual(jobs[1].company, "Unknown Company")

    def test_empty_results(self):
        with patch(MOCK_PATH) as mock_request:
            mock_request.return_value = self._make_page_response([{"legal": "API usage notice"}])

            jobs = fetch_jobs("SuperObscureJobTitle", max_pages=5)
            self.assertEqual(len(jobs), 0)

    def test_pagination_multiple_pages(self):
        """Verify aggregation across multiple non-empty pages."""
        with patch(MOCK_PATH) as mock_request:
            def make_page(items):
                return [{"legal": "notice"}] + [
                    {"id": str(i), "position": f"Job {i}", "company": "Co"}
                    for i in items
                ]

            page_1 = self._make_page_response(make_page(range(1, 4)))   # 3 jobs
            page_2 = self._make_page_response(make_page(range(4, 7)))   # 3 jobs
            page_3_data = [{"legal": "notice"}]                        # empty

            mock_request.side_effect = [page_1, page_2, self._make_page_response(page_3_data)]

            jobs = fetch_jobs("Python", max_pages=5)
            self.assertEqual(len(jobs), 6)

    def test_deduplication_across_pages(self):
        """Jobs with duplicate IDs across pages should be deduplicated."""
        with patch(MOCK_PATH) as mock_request:
            page_1 = self._make_page_response([
                {"legal": "notice"},
                {"id": "1", "position": "Job 1", "company": "Co"},
                {"id": "2", "position": "Job 2", "company": "Co"},
            ])
            # Same job IDs on page 2 (should be deduplicated)
            page_2 = self._make_page_response([
                {"legal": "notice"},
                {"id": "1", "position": "Job 1", "company": "Co"},
                {"id": "3", "position": "Job 3", "company": "Co"},
            ])
            page_3 = self._make_page_response([{"legal": "notice"}])

            mock_request.side_effect = [page_1, page_2, page_3]

            jobs = fetch_jobs("Python", max_pages=5)
            self.assertEqual(len(jobs), 3)  # 3 unique IDs

    def test_first_page_failure_returns_empty(self):
        """If the first page fails, return empty list."""
        with patch(MOCK_PATH) as mock_request:
            mock_request.side_effect = requests.exceptions.ConnectionError("DNS failure")

            jobs = fetch_jobs("Python", max_pages=5)
            self.assertEqual(len(jobs), 0)

    def test_subsequent_page_failure_returns_previous_results(self):
        """If page 2 fails after retry exhaustion, return results from page 1."""
        with patch(MOCK_PATH) as mock_request:
            page_1 = self._make_page_response([
                {"legal": "notice"},
                {"id": "1", "position": "Job 1", "company": "Co"},
            ])
            # retry_request with max_retries=3 will try 4 times (1 initial + 3 retries)
            # so we need 4 Timeout exceptions for page 2 to exhaust retries
            timeout_exc = requests.exceptions.Timeout("timeout")
            mock_request.side_effect = [page_1, timeout_exc, timeout_exc, timeout_exc, timeout_exc]

            jobs = fetch_jobs("Python", max_pages=5)
            self.assertEqual(len(jobs), 1)

    def test_http_429_rate_limit(self):
        """429 on first page should return empty after retries exhaust."""
        with patch(MOCK_PATH) as mock_request:
            mock_429 = MagicMock()
            mock_429.status_code = 429
            mock_429.headers = {}

            mock_request.return_value = mock_429

            jobs = fetch_jobs("Python", max_pages=5)
            self.assertEqual(len(jobs), 0)

    def test_malformed_json(self):
        with patch(MOCK_PATH) as mock_request:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.side_effect = json.JSONDecodeError("Expecting value", "", 0)
            mock_request.return_value = mock_response

            jobs = fetch_jobs("Python", max_pages=5)
            self.assertEqual(len(jobs), 0)



class TestRemoteOKTagHelper(unittest.TestCase):
    """Tests for the _get_remoteok_tag tag extraction helper."""

    def test_single_word_tag(self):
        """Single-word title should be used as-is."""
        tag = _get_remoteok_tag("Python")
        self.assertEqual(tag, "python")

    def test_multi_word_uses_first_word(self):
        """Multi-word title should use only the first word."""
        tag = _get_remoteok_tag("Python Developer")
        self.assertEqual(tag, "python")

    def test_senior_title_uses_first_word(self):
        """'Senior Software Engineer' should use 'senior'."""
        tag = _get_remoteok_tag("Senior Software Engineer")
        self.assertEqual(tag, "senior")

    def test_empty_title_falls_back(self):
        """Empty title should fall back to 'developer'."""
        tag = _get_remoteok_tag("")
        self.assertEqual(tag, "developer")

    def test_whitespace_title_falls_back(self):
        """Whitespace-only title should fall back to 'developer'."""
        tag = _get_remoteok_tag("   ")
        self.assertEqual(tag, "developer")

    def test_special_characters_are_encoded(self):
        """Titles with special characters should be URL-encoded."""
        tag = _get_remoteok_tag("C++ Developer")
        self.assertEqual(tag, "c%2B%2B")  # C++ encoded

    def test_title_with_numbers(self):
        """Titles starting with numbers should work."""
        tag = _get_remoteok_tag("3D Artist")
        self.assertEqual(tag, "3d")


if __name__ == '__main__':
    unittest.main()
