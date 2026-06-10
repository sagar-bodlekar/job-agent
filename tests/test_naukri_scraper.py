import unittest
from unittest.mock import patch, MagicMock
import requests

from scrapers.naukri_scraper import fetch_jobs

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

    @patch('scrapers.naukri_scraper.requests.get')
    def test_fetch_jobs_success_and_partial_data(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = self.mock_html_success
        mock_get.return_value = mock_response

        jobs = fetch_jobs("Python")
        
        self.assertEqual(len(jobs), 2)
        
        # Test full data mapping
        self.assertEqual(jobs[0].title, "Python Developer")
        self.assertEqual(jobs[0].company, "Tech Corp India")
        self.assertEqual(jobs[0].location, "Bangalore")
        self.assertEqual(jobs[0].salary, "10-15 Lacs PA")
        self.assertEqual(jobs[0].link, "https://naukri.com/job/1")
        
        # Test partial data mapping
        self.assertEqual(jobs[1].title, "Data Scientist")
        self.assertEqual(jobs[1].company, "Unknown Company")
        self.assertIsNone(jobs[1].salary)
        self.assertEqual(jobs[1].location, "Remote")

    @patch('scrapers.naukri_scraper.requests.get')
    def test_bot_protection_block(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.text = self.mock_html_bot_block
        # Note: If it raises 403, requests throws HTTPError. Let's mock a scenario where 
        # it returns 200 but content is blocked, OR 403.
        mock_get.return_value = mock_response
        
        jobs = fetch_jobs("Python")
        self.assertEqual(len(jobs), 0)

    @patch('scrapers.naukri_scraper.requests.get')
    def test_html_structure_changed(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = self.mock_html_changed_structure
        mock_get.return_value = mock_response
        
        jobs = fetch_jobs("Python")
        self.assertEqual(len(jobs), 0)

    @patch('scrapers.naukri_scraper.requests.get')
    def test_timeout(self, mock_get):
        mock_get.side_effect = requests.exceptions.Timeout("Connection timed out")
        
        jobs = fetch_jobs("Python")
        self.assertEqual(len(jobs), 0)

if __name__ == '__main__':
    unittest.main()
