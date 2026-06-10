import unittest
from unittest.mock import patch, MagicMock
import os

from scrapers.wellfound_scraper import fetch_jobs

class TestWellfoundScraper(unittest.TestCase):

    @patch.dict(os.environ, {"FIRECRAWL_API_KEY": "test_key"})
    @patch('scrapers.wellfound_scraper.FirecrawlApp')
    def test_fetch_jobs_success(self, MockFirecrawlApp):
        mock_app = MagicMock()
        MockFirecrawlApp.return_value = mock_app
        
        # Mocking the response from Firecrawl extract
        mock_app.extract.return_value = {
            "data": {
                "jobs": [
                    {
                        "title": "Python Developer",
                        "company": "Startup Inc",
                        "location": "Remote",
                        "link": "https://wellfound.com/job/1",
                        "salary": "$100k - $120k"
                    },
                    {
                        "title": "Backend Engineer",
                        "company": "Another Startup",
                        "location": "New York",
                        "link": "https://wellfound.com/job/2",
                        "salary": None
                    }
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
    @patch('scrapers.wellfound_scraper.FirecrawlApp')
    def test_empty_output(self, MockFirecrawlApp):
        mock_app = MagicMock()
        MockFirecrawlApp.return_value = mock_app
        
        mock_app.extract.return_value = {
            "extract": {
                "jobs": []
            }
        }
        
        jobs = fetch_jobs("Python")
        self.assertEqual(len(jobs), 0)

    @patch.dict(os.environ, {"FIRECRAWL_API_KEY": "test_key"})
    @patch('scrapers.wellfound_scraper.FirecrawlApp')
    def test_firecrawl_exception(self, MockFirecrawlApp):
        mock_app = MagicMock()
        MockFirecrawlApp.return_value = mock_app
        
        mock_app.extract.side_effect = Exception("Timeout or invalid key")
        
        jobs = fetch_jobs("Python")
        self.assertEqual(len(jobs), 0)

if __name__ == '__main__':
    unittest.main()
