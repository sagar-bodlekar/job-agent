import unittest
from unittest.mock import patch, MagicMock
import os

from scrapers.wellfound_scraper import fetch_jobs


class TestWellfoundScraper(unittest.TestCase):

    @patch.dict(os.environ, {"FIRECRAWL_API_KEY": "test_key"})
    @patch("scrapers.wellfound_scraper.FirecrawlApp")
    def test_fetch_jobs_success(self, MockFirecrawlApp):
        mock_app = MagicMock()
        MockFirecrawlApp.return_value = mock_app

        mock_app.extract.return_value = {
            "data": {
                "jobs": [
                    {
                        "title": "Python Developer",
                        "company": "Startup Inc",
                        "location": "Remote",
                        "link": "https://wellfound.com/job/1",
                        "salary": "$100k - $120k",
                    },
                    {
                        "title": "Backend Engineer",
                        "company": "Another Startup",
                        "location": "New York",
                        "link": "https://wellfound.com/job/2",
                        "salary": None,
                    },
                ]
            }
        }

        jobs = fetch_jobs("Python")

        self.assertEqual(len(jobs), 2)
        self.assertEqual(jobs[0].title, "Python Developer")
        self.assertEqual(jobs[0].company, "Startup Inc")
        self.assertEqual(jobs[1].title, "Backend Engineer")
        self.assertIsNone(jobs[1].salary)

    @patch.dict(os.environ, clear=True)
    def test_missing_api_key(self):
        jobs = fetch_jobs("Python")
        self.assertEqual(len(jobs), 0)

    @patch.dict(os.environ, {"FIRECRAWL_API_KEY": "test_key"})
    @patch("scrapers.wellfound_scraper.FirecrawlApp")
    def test_empty_output(self, MockFirecrawlApp):
        mock_app = MagicMock()
        MockFirecrawlApp.return_value = mock_app

        mock_app.extract.return_value = {
            "data": {
                "jobs": []
            }
        }

        jobs = fetch_jobs("Python")
        self.assertEqual(len(jobs), 0)

    @patch.dict(os.environ, {"FIRECRAWL_API_KEY": "test_key"})
    @patch("scrapers.wellfound_scraper.FirecrawlApp")
    def test_firecrawl_exception(self, MockFirecrawlApp):
        mock_app = MagicMock()
        MockFirecrawlApp.return_value = mock_app

        mock_app.extract.side_effect = Exception("Timeout or invalid key")

        jobs = fetch_jobs("Python")
        self.assertEqual(len(jobs), 0)

    @patch.dict(os.environ, {"FIRECRAWL_API_KEY": "test_key"})
    @patch("scrapers.wellfound_scraper.FirecrawlApp")
    def test_pagination_sends_multiple_urls(self, MockFirecrawlApp):
        """Verify that max_pages > 1 sends multiple URLs in the extract call."""
        mock_app = MagicMock()
        MockFirecrawlApp.return_value = mock_app
        mock_app.extract.return_value = {"data": {"jobs": []}}

        fetch_jobs("Python", max_pages=3)

        # The extract call should include 3 URLs (one per page)
        call_kwargs = mock_app.extract.call_args.kwargs
        urls = call_kwargs.get("urls", [])
        self.assertEqual(len(urls), 3)
        # Page 1 should use /role/ without ?page=
        self.assertIn("role/python", urls[0])
        self.assertNotIn("/l/", urls[0])
        self.assertNotIn("?page=", urls[0])
        # Page 2 should have ?page=2
        self.assertIn("role/python", urls[1])
        self.assertIn("?page=2", urls[1])
        # Page 3 should have ?page=3
        self.assertIn("role/python", urls[2])
        self.assertIn("?page=3", urls[2])

    @patch.dict(os.environ, {"FIRECRAWL_API_KEY": "test_key"})
    @patch("scrapers.wellfound_scraper.FirecrawlApp")
    def test_respects_max_pages(self, MockFirecrawlApp):
        """max_pages parameter controls number of URLs sent."""
        mock_app = MagicMock()
        MockFirecrawlApp.return_value = mock_app
        mock_app.extract.return_value = {"data": {"jobs": []}}

        fetch_jobs("Python", max_pages=1)
        call_kwargs = mock_app.extract.call_args.kwargs
        self.assertEqual(len(call_kwargs.get("urls", [])), 1)

        fetch_jobs("Python", max_pages=10)
        call_kwargs = mock_app.extract.call_args.kwargs
        self.assertEqual(len(call_kwargs.get("urls", [])), 10)


if __name__ == '__main__':
    unittest.main()
