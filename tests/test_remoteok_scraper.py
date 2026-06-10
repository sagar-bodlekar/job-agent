import unittest
from unittest.mock import patch, MagicMock
import requests
import json

from scrapers.remoteok_scraper import fetch_jobs

class TestRemoteOKScraper(unittest.TestCase):
    
    @patch('scrapers.remoteok_scraper.requests.get')
    def test_fetch_jobs_success(self, mock_get):
        # Mocking a successful API response with realistic data
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"legal": "API usage notice"},
            {
                "id": "1",
                "position": "Python Developer",
                "company": "Tech Corp",
                "location": "Worldwide",
                "url": "https://remoteok.com/job/1",
                "salary_min": 50000,
                "salary_max": 100000
            },
            {
                "id": "2",
                "position": "Backend Engineer"
                # Simulating missing optional keys like company, location, salary
            }
        ]
        mock_get.return_value = mock_response
        
        jobs = fetch_jobs("Python")
        
        # Verify filtering of legal notice and mapping of data
        self.assertEqual(len(jobs), 2)
        self.assertEqual(jobs[0].title, "Python Developer")
        self.assertEqual(jobs[0].salary, "$50000 - $100000")
        self.assertEqual(jobs[1].title, "Backend Engineer")
        self.assertEqual(jobs[1].company, "Unknown Company") # Fallback handled

    @patch('scrapers.remoteok_scraper.requests.get')
    def test_empty_results(self, mock_get):
        # Simulating search for obscure job returning only the legal notice
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{"legal": "API usage notice"}]
        mock_get.return_value = mock_response
        
        jobs = fetch_jobs("SuperObscureJobTitle")
        self.assertEqual(len(jobs), 0)

    @patch('scrapers.remoteok_scraper.requests.get')
    def test_http_429_rate_limit(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(response=mock_response)
        mock_get.return_value = mock_response
        
        jobs = fetch_jobs("Python")
        self.assertEqual(len(jobs), 0)

    @patch('scrapers.remoteok_scraper.requests.get')
    def test_http_500_api_down(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(response=mock_response)
        mock_get.return_value = mock_response
        
        jobs = fetch_jobs("Python")
        self.assertEqual(len(jobs), 0)
        
    @patch('scrapers.remoteok_scraper.requests.get')
    def test_malformed_json(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        # Simulating ValueError raised by requests.json() when JSON is invalid
        mock_response.json.side_effect = json.JSONDecodeError("Expecting value", "", 0)
        mock_get.return_value = mock_response
        
        jobs = fetch_jobs("Python")
        self.assertEqual(len(jobs), 0)

if __name__ == '__main__':
    unittest.main()
