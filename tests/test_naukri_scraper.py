import unittest
from unittest.mock import patch, MagicMock
import os

from scrapers.naukri_scraper import fetch_jobs


class TestNaukriScraper(unittest.TestCase):

    @patch.dict(os.environ, {"FIRECRAWL_API_KEY": "test_key"})
    @patch("scrapers.naukri_scraper.FirecrawlApp")
    def test_fetch_jobs_success(self, MockFirecrawlApp):
        """Successful extraction returns the correct jobs."""
        mock_app = MagicMock()
        MockFirecrawlApp.return_value = mock_app

        mock_app.extract.return_value = {
            "data": {
                "jobs": [
                    {
                        "title": "Python Developer",
                        "company": "Tech Corp India",
                        "location": "Bangalore",
                        "salary": "10-15 Lacs PA",
                        "link": "https://naukri.com/job/1",
                    },
                    {
                        "title": "Data Scientist",
                        "company": "Another Corp",
                        "location": "Remote",
                        "salary": None,
                        "link": "https://naukri.com/job/2",
                    },
                ]
            }
        }

        jobs = fetch_jobs("Python")

        self.assertEqual(len(jobs), 2)
        self.assertEqual(jobs[0].title, "Python Developer")
        self.assertEqual(jobs[0].company, "Tech Corp India")
        self.assertEqual(jobs[0].location, "Bangalore")
        self.assertEqual(jobs[0].salary, "10-15 Lacs PA")
        self.assertEqual(jobs[0].link, "https://naukri.com/job/1")
        self.assertEqual(jobs[0].source_platform, "Naukri")

        self.assertEqual(jobs[1].title, "Data Scientist")
        self.assertEqual(jobs[1].company, "Another Corp")
        self.assertIsNone(jobs[1].salary)
        self.assertEqual(jobs[1].location, "Remote")

    @patch.dict(os.environ, clear=True)
    def test_missing_api_key(self):
        """Without API key, scraper returns empty list."""
        jobs = fetch_jobs("Python")
        self.assertEqual(len(jobs), 0)

    @patch.dict(os.environ, {"FIRECRAWL_API_KEY": "test_key"})
    @patch("scrapers.naukri_scraper.FirecrawlApp")
    def test_empty_output(self, MockFirecrawlApp):
        """Firecrawl returns empty data."""
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
    @patch("scrapers.naukri_scraper.FirecrawlApp")
    def test_firecrawl_exception(self, MockFirecrawlApp):
        """Firecrawl exception is caught gracefully."""
        mock_app = MagicMock()
        MockFirecrawlApp.return_value = mock_app

        mock_app.extract.side_effect = Exception("Timeout or invalid key")

        jobs = fetch_jobs("Python")
        self.assertEqual(len(jobs), 0)

    @patch.dict(os.environ, {"FIRECRAWL_API_KEY": "test_key"})
    @patch("scrapers.naukri_scraper.FirecrawlApp")
    def test_pagination_sends_multiple_urls(self, MockFirecrawlApp):
        """Verify that max_pages > 1 sends multiple URLs to Firecrawl."""
        mock_app = MagicMock()
        MockFirecrawlApp.return_value = mock_app
        mock_app.extract.return_value = {"data": {"jobs": []}}

        fetch_jobs("Python", max_pages=3)

        call_kwargs = mock_app.extract.call_args.kwargs
        urls = call_kwargs.get("urls", [])
        self.assertEqual(len(urls), 3)
        # Page 1 should use the base URL
        self.assertIn("/python-jobs", urls[0])
        self.assertNotIn("?", urls[0])
        # Page 2+ should have page suffix
        self.assertIn("python-jobs-2", urls[1])
        self.assertIn("python-jobs-3", urls[2])

    @patch.dict(os.environ, {"FIRECRAWL_API_KEY": "test_key"})
    @patch("scrapers.naukri_scraper.FirecrawlApp")
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

    @patch.dict(os.environ, {"FIRECRAWL_API_KEY": "test_key"})
    @patch("scrapers.naukri_scraper.FirecrawlApp")
    def test_missing_data_key_in_response(self, MockFirecrawlApp):
        """Response without 'data' key should return empty."""
        mock_app = MagicMock()
        MockFirecrawlApp.return_value = mock_app

        mock_app.extract.return_value = {
            "extract": {"jobs": []}  # 'extract' not 'data'
        }

        jobs = fetch_jobs("Python")
        self.assertEqual(len(jobs), 0)


if __name__ == '__main__':
    unittest.main()
