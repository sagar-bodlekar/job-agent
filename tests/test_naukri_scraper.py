import unittest
from unittest.mock import patch, MagicMock
import requests

from scrapers.naukri_scraper import fetch_jobs

# The scraper calls retry_request -> requests.request (imported in scrapers.retry)
MOCK_PATH = "scrapers.retry.requests.request"


class TestNaukriScraper(unittest.TestCase):

    def setUp(self):
        self.mock_html_success = """
        <html><body>
            <div class="srp-jobtuple-wrapper">
                <a class="title" href="https://naukri.com/job/1">Python Developer</a>
                <a class="comp-name">Tech Corp India</a>
                <span class="locWdth">Bangalore</span>
                <span class="sal-wrap" title="10-15 Lacs PA">10-15 Lacs PA</span>
            </div>
            <div class="jobTuple">
                <a class="title" href="https://naukri.com/job/2">Data Scientist</a>
                <!-- Missing company and salary to test partial data -->
                <span class="locWdth">Remote</span>
            </div>
        </body></html>
        """
        self.mock_html_bot_block = "<html><head><title>Access Denied</title></head><body>Pardon Our Interruption</body></html>"
        self.mock_html_changed_structure = "<html><body><div class='unknown-wrapper'><ul><li>Python Job</li></ul></div></body></html>"
        self.mock_html_with_pagination = """
        <html><body>
            <div class="jobTuple">
                <a class="title" href="https://naukri.com/job/1">Python Developer</a>
                <a class="comp-name">Tech Corp India</a>
                <span class="locWdth">Bangalore</span>
            </div>
            <a class="next-page" href="/python-developer-jobs-2">Next</a>
        </body></html>
        """

    def _make_response(self, html: str, status_code: int = 200):
        mock_response = MagicMock()
        mock_response.status_code = status_code
        mock_response.text = html
        return mock_response

    def test_fetch_jobs_success_and_partial_data(self):
        with patch(MOCK_PATH) as mock_request:
            # Only one page with results, no next page link
            mock_request.return_value = self._make_response(self.mock_html_success)

            jobs = fetch_jobs("Python", max_pages=5)

            self.assertEqual(len(jobs), 2)

            self.assertEqual(jobs[0].title, "Python Developer")
            self.assertEqual(jobs[0].company, "Tech Corp India")
            self.assertEqual(jobs[0].location, "Bangalore")
            self.assertEqual(jobs[0].salary, "10-15 Lacs PA")
            self.assertEqual(jobs[0].link, "https://naukri.com/job/1")

            self.assertEqual(jobs[1].title, "Data Scientist")
            self.assertEqual(jobs[1].company, "Unknown Company")
            self.assertIsNone(jobs[1].salary)
            self.assertEqual(jobs[1].location, "Remote")

    def test_bot_protection_block(self):
        with patch(MOCK_PATH) as mock_request:
            mock_request.return_value = self._make_response(self.mock_html_bot_block)

            jobs = fetch_jobs("Python", max_pages=5)
            self.assertEqual(len(jobs), 0)

    def test_html_structure_changed(self):
        with patch(MOCK_PATH) as mock_request:
            mock_request.return_value = self._make_response(self.mock_html_changed_structure)

            jobs = fetch_jobs("Python", max_pages=5)
            self.assertEqual(len(jobs), 0)

    def test_timeout(self):
        with patch(MOCK_PATH) as mock_request:
            mock_request.side_effect = requests.exceptions.Timeout("Connection timed out")

            jobs = fetch_jobs("Python", max_pages=5)
            self.assertEqual(len(jobs), 0)

    def test_pagination_multiple_pages(self):
        """Verify that pagination stops when there's no next-page link."""
        with patch(MOCK_PATH) as mock_request:
            page_1 = self._make_response(self.mock_html_with_pagination)
            page_2 = self._make_response(self.mock_html_success)  # page 2 has jobs but no next link

            mock_request.side_effect = [page_1, page_2]

            jobs = fetch_jobs("Python", max_pages=5)
            # Page 1 has 1 job, page 2 has 2 jobs
            self.assertEqual(len(jobs), 3)

    def test_pagination_respects_max_pages(self):
        """Should not exceed the max_pages limit."""
        with patch(MOCK_PATH) as mock_request:
            # Return 2 pages of results but only allow max_pages=1
            mock_request.return_value = self._make_response(self.mock_html_success)

            jobs = fetch_jobs("Python", max_pages=1)
            # Only the first page should be fetched
            self.assertEqual(len(jobs), 2)
            self.assertEqual(mock_request.call_count, 1)

    def test_first_page_failure_returns_empty(self):
        """If the first page fails, return empty list."""
        with patch(MOCK_PATH) as mock_request:
            mock_request.side_effect = requests.exceptions.ConnectionError("DNS failure")

            jobs = fetch_jobs("Python", max_pages=5)
            self.assertEqual(len(jobs), 0)


if __name__ == '__main__':
    unittest.main()
