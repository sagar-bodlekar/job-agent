"""
Rate limiting / throttling utility for controlling request frequency.

Provides:
- RateLimiter: Tracks last request time per domain and enforces minimum delays
- Global delay helper for orchestrator-level throttling
"""

import time
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Tracks request timestamps per domain and enforces minimum inter-request delays.

    Use a single shared instance across all scrapers to coordinate throttling.

    Example:
        limiter = RateLimiter(default_delay=1.0)
        limiter.wait("naukri.com")
        response = requests.get(url)
    """

    def __init__(self, default_delay: float = 1.0, per_domain_delays: Optional[Dict[str, float]] = None):
        """
        Args:
            default_delay: Default minimum delay (seconds) between requests to any domain.
            per_domain_delays: Optional dict mapping domain -> specific delay in seconds.
                               Overrides default_delay for listed domains.
        """
        self.default_delay = default_delay
        self.per_domain_delays = per_domain_delays or {}
        self._last_request_time: Dict[str, float] = {}

    def get_delay(self, domain: str) -> float:
        """Get the configured delay for a given domain."""
        return self.per_domain_delays.get(domain, self.default_delay)

    def wait(self, domain: str) -> None:
        """
        Sleep if necessary to maintain the minimum delay since the last request
        to the given domain.
        """
        now = time.time()
        last_time = self._last_request_time.get(domain)
        delay = self.get_delay(domain)

        if last_time is not None:
            elapsed = now - last_time
            if elapsed < delay:
                sleep_time = delay - elapsed
                logger.debug("Rate limiting: waiting %.1fs before next request to %s", sleep_time, domain)
                time.sleep(sleep_time)

        self._last_request_time[domain] = time.time()

    def reset(self, domain: Optional[str] = None) -> None:
        """Reset tracking for a specific domain, or all domains if None."""
        if domain:
            self._last_request_time.pop(domain, None)
        else:
            self._last_request_time.clear()


# Module-level shared rate limiter instance
# Configured defaults: 2s for Naukri (aggressive bot detection),
# 1s for RemoteOK API, 1s for Wellfound (Firecrawl handles its own rate limits)
shared_limiter = RateLimiter(
    default_delay=1.0,
    per_domain_delays={
        "naukri.com": 2.0,
        "remoteok.com": 1.0,
        "wellfound.com": 1.0,
    },
)
