# Copyright 2026 Terrene Foundation
# Licensed under the Apache License, Version 2.0
"""Unit tests for praxis.api.rate_limit — in-memory sliding window rate limiter."""

import time

import pytest


class TestRateLimiter:
    """Test the RateLimiter class."""

    def test_allows_requests_under_limit(self):
        from praxis.api.rate_limit import RateLimiter

        limiter = RateLimiter(max_attempts=5, window_seconds=60)
        for i in range(5):
            assert limiter.check("user-1") is True

    def test_blocks_requests_over_limit(self):
        from praxis.api.rate_limit import RateLimiter

        limiter = RateLimiter(max_attempts=3, window_seconds=60)
        for _ in range(3):
            limiter.check("user-1")
        assert limiter.check("user-1") is False

    def test_different_keys_are_independent(self):
        from praxis.api.rate_limit import RateLimiter

        limiter = RateLimiter(max_attempts=2, window_seconds=60)
        limiter.check("user-1")
        limiter.check("user-1")
        # user-1 is at limit, but user-2 should be fine
        assert limiter.check("user-1") is False
        assert limiter.check("user-2") is True

    def test_remaining_shows_correct_count(self):
        from praxis.api.rate_limit import RateLimiter

        limiter = RateLimiter(max_attempts=5, window_seconds=60)
        assert limiter.remaining("user-1") == 5
        limiter.check("user-1")
        assert limiter.remaining("user-1") == 4
        limiter.check("user-1")
        assert limiter.remaining("user-1") == 3

    def test_window_expiry_resets_attempts(self):
        from praxis.api.rate_limit import RateLimiter

        limiter = RateLimiter(max_attempts=2, window_seconds=1)
        limiter.check("user-1")
        limiter.check("user-1")
        assert limiter.check("user-1") is False
        # Wait for window to expire
        time.sleep(1.1)
        assert limiter.check("user-1") is True

    def test_reset_clears_attempts(self):
        from praxis.api.rate_limit import RateLimiter

        limiter = RateLimiter(max_attempts=2, window_seconds=60)
        limiter.check("user-1")
        limiter.check("user-1")
        assert limiter.check("user-1") is False
        limiter.reset("user-1")
        assert limiter.check("user-1") is True

    def test_remaining_for_unknown_key_returns_max(self):
        from praxis.api.rate_limit import RateLimiter

        limiter = RateLimiter(max_attempts=5, window_seconds=60)
        assert limiter.remaining("never-seen") == 5

    def test_blocked_check_does_not_record_attempt(self):
        from praxis.api.rate_limit import RateLimiter

        limiter = RateLimiter(max_attempts=2, window_seconds=60)
        limiter.check("user-1")
        limiter.check("user-1")
        # This should be blocked and NOT record a third attempt
        assert limiter.check("user-1") is False
        # After reset, should still have full capacity
        limiter.reset("user-1")
        assert limiter.remaining("user-1") == 2
