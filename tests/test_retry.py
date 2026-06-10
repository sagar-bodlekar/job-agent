import unittest
from unittest.mock import patch, MagicMock
import time
import requests

from scrapers.retry import retry_request, retry_call


class TestRetryRequest(unittest.TestCase):

    @patch("scrapers.retry.requests.request")
    def test_success_first_attempt(self, mock_request):
        """Request succeeds on the first attempt."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_request.return_value = mock_response

        response = retry_request("GET", "https://example.com", max_retries=3)
        self.assertEqual(response.status_code, 200)
        mock_request.assert_called_once()

    @patch("scrapers.retry.requests.request")
    def test_retry_on_timeout_then_success(self, mock_request):
        """Request times out twice, succeeds on third attempt."""
        mock_response = MagicMock()
        mock_response.status_code = 200

        mock_request.side_effect = [
            requests.exceptions.Timeout("timeout"),
            requests.exceptions.Timeout("timeout"),
            mock_response,
        ]

        response = retry_request("GET", "https://example.com", max_retries=3, base_delay=0.01)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(mock_request.call_count, 3)

    @patch("scrapers.retry.requests.request")
    def test_retry_exhausted_timeout(self, mock_request):
        """All retries exhausted on timeout."""
        mock_request.side_effect = requests.exceptions.Timeout("timeout")

        with self.assertRaises(requests.exceptions.Timeout):
            retry_request("GET", "https://example.com", max_retries=2, base_delay=0.01)

        self.assertEqual(mock_request.call_count, 3)  # initial + 2 retries

    @patch("scrapers.retry.requests.request")
    def test_retry_on_429_then_success(self, mock_request):
        """First response is 429, second succeeds."""
        mock_success = MagicMock()
        mock_success.status_code = 200

        mock_429 = MagicMock()
        mock_429.status_code = 429
        mock_429.headers = {}

        mock_request.side_effect = [mock_429, mock_success]

        response = retry_request("GET", "https://example.com", max_retries=2, base_delay=0.01)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(mock_request.call_count, 2)

    @patch("scrapers.retry.requests.request")
    def test_retry_on_500_then_success(self, mock_request):
        """First response is 500, second succeeds."""
        mock_success = MagicMock()
        mock_success.status_code = 200

        mock_500 = MagicMock()
        mock_500.status_code = 500

        mock_request.side_effect = [mock_500, mock_success]

        response = retry_request("GET", "https://example.com", max_retries=2, base_delay=0.01)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(mock_request.call_count, 2)

    @patch("scrapers.retry.requests.request")
    def test_no_retry_on_404(self, mock_request):
        """4xx errors other than 429 should not be retried."""
        mock_404 = MagicMock()
        mock_404.status_code = 404
        mock_404.raise_for_status.side_effect = requests.exceptions.HTTPError(response=mock_404)

        mock_request.return_value = mock_404

        with self.assertRaises(requests.exceptions.HTTPError):
            retry_request("GET", "https://example.com", max_retries=3, base_delay=0.01)

        self.assertEqual(mock_request.call_count, 1)

    @patch("scrapers.retry.requests.request")
    def test_retry_429_respects_retry_after(self, mock_request):
        """429 response with Retry-After header uses that value for delay."""
        mock_success = MagicMock()
        mock_success.status_code = 200

        mock_429 = MagicMock()
        mock_429.status_code = 429
        mock_429.headers = {"Retry-After": "0.01"}

        mock_request.side_effect = [mock_429, mock_success]

        response = retry_request("GET", "https://example.com", max_retries=2, base_delay=10.0)
        self.assertEqual(response.status_code, 200)

    @patch("scrapers.retry.requests.request")
    def test_non_retryable_exception(self, mock_request):
        """Non-retryable exceptions (e.g., InvalidURL) raise immediately."""
        mock_request.side_effect = requests.exceptions.InvalidURL("bad url")

        with self.assertRaises(requests.exceptions.InvalidURL):
            retry_request("GET", "bad-url", max_retries=3)

        self.assertEqual(mock_request.call_count, 1)


class TestRetryCall(unittest.TestCase):

    def test_success_first_attempt(self):
        """Callable succeeds on first attempt."""
        def my_func():
            return "success"

        result = retry_call(my_func, max_retries=3)
        self.assertEqual(result, "success")

    def test_retry_then_success(self):
        """Callable fails twice, succeeds on third."""
        call_count = [0]

        def my_func():
            call_count[0] += 1
            if call_count[0] < 3:
                raise TimeoutError("timeout")
            return "success"

        result = retry_call(my_func, max_retries=3, base_delay=0.01,
                           retryable_exceptions=(TimeoutError,))
        self.assertEqual(result, "success")
        self.assertEqual(call_count[0], 3)

    def test_retry_exhausted(self):
        """All retries exhausted on persistent failure."""
        def my_func():
            raise TimeoutError("always fails")

        with self.assertRaises(TimeoutError):
            retry_call(my_func, max_retries=2, base_delay=0.01,
                      retryable_exceptions=(TimeoutError,))

    def test_non_retryable_exception_raises_immediately(self):
        """Non-retryable exceptions raise immediately without retry."""
        call_count = [0]

        def my_func():
            call_count[0] += 1
            raise ValueError("non-retryable")

        with self.assertRaises(ValueError):
            retry_call(my_func, max_retries=3, base_delay=0.01,
                      retryable_exceptions=(TimeoutError,))

        self.assertEqual(call_count[0], 1)


if __name__ == '__main__':
    unittest.main()
