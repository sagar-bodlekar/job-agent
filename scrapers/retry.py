"""
Retry utility for handling transient failures in HTTP requests.

Provides:
- retry_request(): Wraps requests.get() with exponential backoff and jitter
- retry_call(): General-purpose retry wrapper for any callable
"""

import time
import random
import logging
from typing import Callable, Optional, Tuple, Type, Union

import requests

logger = logging.getLogger(__name__)

# Default retryable status codes
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}

# Default exceptions that trigger a retry
RETRYABLE_EXCEPTIONS = (
    requests.exceptions.Timeout,
    requests.exceptions.ConnectionError,
)


def _sleep_with_backoff(attempt: int, base_delay: float = 1.0, backoff_factor: float = 2.0) -> None:
    """Sleep with exponential backoff and random jitter."""
    delay = base_delay * (backoff_factor ** attempt) + random.uniform(0, 1.0)
    logger.debug(f"Waiting {delay:.1f}s before retry...")
    time.sleep(delay)


def retry_request(
    method: str,
    url: str,
    max_retries: int = 3,
    base_delay: float = 1.0,
    backoff_factor: float = 2.0,
    **kwargs,
) -> requests.Response:
    """
    Make an HTTP request with retry logic.

    Retries on:
    - Timeout and ConnectionError exceptions
    - HTTP 429 (Rate Limited) — respects Retry-After header
    - HTTP 5xx (Server errors)

    Does NOT retry on:
    - HTTP 4xx (except 429)
    - Other request exceptions (InvalidURL, etc.)

    Args:
        method: HTTP method (e.g., 'GET', 'POST')
        url: Request URL
        max_retries: Maximum number of retry attempts (default 3)
        base_delay: Initial delay in seconds before first retry (default 1.0)
        backoff_factor: Multiplier for delay on each retry (default 2.0)
        **kwargs: Additional arguments passed to requests.request()

    Returns:
        requests.Response object

    Raises:
        requests.exceptions.RequestException: If all retries are exhausted
            or on non-retryable errors.
    """
    last_exception: Optional[Exception] = None

    for attempt in range(max_retries + 1):
        try:
            response = requests.request(method, url, **kwargs)

            # Retry on 429 (Rate Limited)
            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After")
                if retry_after:
                    try:
                        delay = float(retry_after)
                    except ValueError:
                        delay = base_delay * (backoff_factor ** attempt)
                else:
                    delay = base_delay * (backoff_factor ** attempt) + random.uniform(0, 1.0)

                if attempt < max_retries:
                    logger.warning(
                        "HTTP 429 on %s. Retrying in %.1fs (attempt %d/%d)...",
                        url, delay, attempt + 1, max_retries + 1,
                    )
                    time.sleep(delay)
                    continue
                else:
                    logger.error("HTTP 429 on %s. All retries exhausted.", url)
                    response.raise_for_status()

            # Retry on 5xx (Server errors)
            if response.status_code >= 500:
                if attempt < max_retries:
                    delay = base_delay * (backoff_factor ** attempt) + random.uniform(0, 1.0)
                    logger.warning(
                        "HTTP %d on %s. Retrying in %.1fs (attempt %d/%d)...",
                        response.status_code, url, delay, attempt + 1, max_retries + 1,
                    )
                    time.sleep(delay)
                    continue
                else:
                    logger.error(
                        "HTTP %d on %s. All retries exhausted.", response.status_code, url
                    )
                    response.raise_for_status()

            # Success or non-retryable status — raise_for_status to surface any 4xx
            response.raise_for_status()
            return response

        except RETRYABLE_EXCEPTIONS as e:
            last_exception = e
            if attempt < max_retries:
                delay = base_delay * (backoff_factor ** attempt) + random.uniform(0, 1.0)
                logger.warning(
                    "Request failed on %s: %s. Retrying in %.1fs (attempt %d/%d)...",
                    url, e, delay, attempt + 1, max_retries + 1,
                )
                time.sleep(delay)
            else:
                logger.error(
                    "Request to %s failed after %d attempts: %s",
                    url, max_retries + 1, e,
                )
                raise

        except requests.exceptions.RequestException as e:
            # Non-retryable request exception (InvalidURL, etc.) — raise immediately
            logger.error("Non-retryable request error on %s: %s", url, e)
            raise

    # Should not reach here, but handle gracefully
    if last_exception:
        raise last_exception
    raise requests.exceptions.RequestException(f"Request to {url} failed for unknown reasons.")


def retry_call(
    func: Callable,
    args: tuple = (),
    kwargs: Optional[dict] = None,
    max_retries: int = 3,
    base_delay: float = 1.0,
    backoff_factor: float = 2.0,
    retryable_exceptions: Tuple[Type[Exception], ...] = RETRYABLE_EXCEPTIONS,
) -> object:
    """
    General-purpose retry wrapper for any callable.

    Useful for wrapping Firecrawl SDK calls or other non-requests functions.

    Args:
        func: The callable to retry
        args: Positional arguments for the callable
        kwargs: Keyword arguments for the callable
        max_retries: Maximum number of retry attempts (default 3)
        base_delay: Initial delay in seconds before first retry (default 1.0)
        backoff_factor: Multiplier for delay on each retry (default 2.0)
        retryable_exceptions: Tuple of exception types that trigger a retry

    Returns:
        The return value of the callable

    Raises:
        The last exception encountered if all retries are exhausted.
    """
    if kwargs is None:
        kwargs = {}

    last_exception: Optional[Exception] = None

    for attempt in range(max_retries + 1):
        try:
            return func(*args, **kwargs)
        except retryable_exceptions as e:
            last_exception = e
            if attempt < max_retries:
                delay = base_delay * (backoff_factor ** attempt) + random.uniform(0, 1.0)
                logger.warning(
                    "Call to %s failed: %s. Retrying in %.1fs (attempt %d/%d)...",
                    func.__name__, e, delay, attempt + 1, max_retries + 1,
                )
                time.sleep(delay)
            else:
                logger.error(
                    "Call to %s failed after %d attempts: %s",
                    func.__name__, max_retries + 1, e,
                )
                raise
        except Exception as e:
            # Non-retryable exception — raise immediately
            raise

    if last_exception:
        raise last_exception
    raise RuntimeError(f"Call to {func.__name__} failed for unknown reasons.")
