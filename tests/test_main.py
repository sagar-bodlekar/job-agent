import unittest
from unittest.mock import patch, MagicMock, mock_open
import csv
import sys

from models import Job
from main import run_scrapers, write_to_csv, main


class TestMainOrchestrator(unittest.TestCase):

    def setUp(self):
        self.sample_job = Job(
            title="Dev", company="C", location="L", link="http", source_platform="Test", salary="10"
        )

    @patch("main._global_delay")  # Avoid slow time.sleep calls
    @patch("main.wellfound_scraper.fetch_jobs")
    @patch("main.naukri_scraper.fetch_jobs")
    @patch("main.remoteok_scraper.fetch_jobs")
    def test_run_scrapers_partial_failure(self, mock_remote, mock_naukri, mock_wellfound, mock_delay):
        mock_remote.return_value = [self.sample_job]
        mock_naukri.side_effect = Exception("Unexpected crash")
        mock_wellfound.return_value = [self.sample_job]

        jobs = run_scrapers("Dev")

        self.assertEqual(len(jobs), 2)
        self.assertEqual(jobs[0].source_platform, "Test")

    @patch("main._global_delay")
    @patch("main.wellfound_scraper.fetch_jobs")
    @patch("main.naukri_scraper.fetch_jobs")
    @patch("main.remoteok_scraper.fetch_jobs")
    def test_run_scrapers_total_failure(self, mock_remote, mock_naukri, mock_wellfound, mock_delay):
        mock_remote.return_value = []
        mock_naukri.return_value = []
        mock_wellfound.return_value = []

        jobs = run_scrapers("Dev")
        self.assertEqual(len(jobs), 0)

    @patch("main._global_delay")
    @patch("main.wellfound_scraper.fetch_jobs")
    @patch("main.naukri_scraper.fetch_jobs")
    @patch("main.remoteok_scraper.fetch_jobs")
    def test_run_scrapers_passes_max_pages(self, mock_remote, mock_naukri, mock_wellfound, mock_delay):
        """Verify max_pages is forwarded to all scrapers."""
        mock_remote.return_value = []
        mock_naukri.return_value = []
        mock_wellfound.return_value = []

        run_scrapers("Dev", max_pages=3)

        mock_remote.assert_called_with("Dev", max_pages=3)
        mock_naukri.assert_called_with("Dev", max_pages=3)
        mock_wellfound.assert_called_with("Dev", max_pages=3)

    @patch("builtins.open", new_callable=mock_open)
    def test_write_to_csv_success(self, mock_file):
        success = write_to_csv([self.sample_job], "test.csv")
        self.assertTrue(success)
        mock_file.assert_called_once_with("test.csv", mode='w', newline='', encoding='utf-8')

    @patch("builtins.open", side_effect=PermissionError("File open in Excel"))
    def test_write_to_csv_permission_error(self, mock_file):
        success = write_to_csv([self.sample_job], "test.csv")
        self.assertFalse(success)

    @patch("main.write_to_csv")
    @patch("main.run_scrapers")
    def test_main_cli_missing_args(self, mock_run, mock_write):
        with self.assertRaises(SystemExit) as cm:
            main([])
        self.assertEqual(cm.exception.code, 2)

    @patch("main.write_to_csv", return_value=True)
    @patch("main.run_scrapers", return_value=[])
    def test_main_cli_with_max_pages(self, mock_run, mock_write):
        """--max-pages flag should be parsed and forwarded."""
        main(["Python Developer", "--max-pages", "10"])
        mock_run.assert_called_with("Python Developer", max_pages=10)

    @patch("main.write_to_csv", return_value=True)
    @patch("main.run_scrapers", return_value=[])
    def test_main_cli_default_max_pages(self, mock_run, mock_write):
        """Without --max-pages, default should be 5."""
        main(["Python Developer"])
        mock_run.assert_called_with("Python Developer", max_pages=5)


if __name__ == '__main__':
    unittest.main()
