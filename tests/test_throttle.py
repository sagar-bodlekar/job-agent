import unittest
import time
from scrapers.throttle import RateLimiter, shared_limiter


class TestRateLimiter(unittest.TestCase):

    def setUp(self):
        self.limiter = RateLimiter(default_delay=0.01)

    def test_no_wait_on_first_request(self):
        """First request to a domain should not wait."""
        start = time.time()
        self.limiter.wait("example.com")
        elapsed = time.time() - start
        self.assertLess(elapsed, 0.1)  # Should be nearly instant

    def test_wait_enforces_minimum_delay(self):
        """Second request to same domain should wait at least the configured delay."""
        self.limiter.wait("example.com")
        start = time.time()
        self.limiter.wait("example.com")
        elapsed = time.time() - start
        self.assertGreaterEqual(elapsed, 0.01 - 0.005)  # Allow small timing variance

    def test_different_domains_no_wait(self):
        """Requests to different domains should not delay each other."""
        self.limiter.wait("domain-a.com")
        start = time.time()
        self.limiter.wait("domain-b.com")
        elapsed = time.time() - start
        self.assertLess(elapsed, 0.1)

    def test_per_domain_delay_override(self):
        """Per-domain delay overrides default delay."""
        limiter = RateLimiter(
            default_delay=0.01,
            per_domain_delays={"slow-domain.com": 0.02},
        )
        limiter.wait("slow-domain.com")
        start = time.time()
        limiter.wait("slow-domain.com")
        elapsed = time.time() - start
        self.assertGreaterEqual(elapsed, 0.02 - 0.005)

    def test_reset_specific_domain(self):
        """Resetting a specific domain clears its last request time."""
        self.limiter.wait("example.com")
        self.limiter.reset("example.com")
        start = time.time()
        self.limiter.wait("example.com")
        elapsed = time.time() - start
        self.assertLess(elapsed, 0.1)  # Should be nearly instant after reset

    def test_reset_all_domains(self):
        """Resetting all domains clears all tracking."""
        self.limiter.wait("domain-a.com")
        self.limiter.wait("domain-b.com")
        self.limiter.reset()
        start = time.time()
        self.limiter.wait("domain-a.com")
        self.limiter.wait("domain-b.com")
        elapsed = time.time() - start
        self.assertLess(elapsed, 0.1)

    def test_get_delay(self):
        """get_delay returns correct values for default and overridden domains."""
        limiter = RateLimiter(
            default_delay=1.0,
            per_domain_delays={"fast.com": 0.5, "slow.com": 3.0},
        )
        self.assertEqual(limiter.get_delay("unknown.com"), 1.0)  # default
        self.assertEqual(limiter.get_delay("fast.com"), 0.5)
        self.assertEqual(limiter.get_delay("slow.com"), 3.0)

    def test_shared_limiter_is_configured(self):
        """The shared module-level limiter should have sensible defaults."""
        self.assertIsNotNone(shared_limiter)
        # Should have config for the three scraper domains
        self.assertIn("naukri.com", shared_limiter.per_domain_delays)
        self.assertIn("remoteok.com", shared_limiter.per_domain_delays)
        self.assertIn("wellfound.com", shared_limiter.per_domain_delays)
        # Naukri should have a longer delay (bot protection)
        self.assertGreater(
            shared_limiter.per_domain_delays["naukri.com"],
            shared_limiter.per_domain_delays["remoteok.com"],
        )


if __name__ == '__main__':
    unittest.main()
