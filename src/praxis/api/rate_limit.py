# Copyright 2026 Terrene Foundation
# Licensed under the Apache License, Version 2.0
"""
Simple in-memory sliding window rate limiter.

Used to protect authentication endpoints from brute-force attacks.
Tracks attempts per key (e.g., IP address or username) within a
configurable time window. No external dependencies required.
"""

from __future__ import annotations

import logging
import time
from collections import defaultdict

logger = logging.getLogger(__name__)


class RateLimiter:
    """In-memory sliding window rate limiter.

    Tracks the number of attempts per key within a configurable time window.
    When the limit is exceeded, subsequent requests are rejected until
    older attempts fall outside the window.

    Args:
        max_attempts: Maximum number of allowed attempts within the window.
        window_seconds: Duration of the sliding window in seconds.
    """

    def __init__(self, max_attempts: int = 5, window_seconds: int = 60) -> None:
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self._attempts: dict[str, list[float]] = defaultdict(list)

    def check(self, key: str) -> bool:
        """Check whether a request is allowed for the given key.

        If allowed, records the attempt. If rate limited, does NOT record
        the attempt (the caller should return 429 immediately).

        Args:
            key: The rate limit key (e.g., client IP or username).

        Returns:
            True if the request is allowed, False if rate limited.
        """
        now = time.time()
        cutoff = now - self.window_seconds

        # Remove expired attempts
        self._attempts[key] = [t for t in self._attempts[key] if t > cutoff]

        if len(self._attempts[key]) >= self.max_attempts:
            return False

        self._attempts[key].append(now)
        return True

    def remaining(self, key: str) -> int:
        """Number of attempts remaining in the current window.

        Args:
            key: The rate limit key.

        Returns:
            Number of remaining allowed attempts (>= 0).
        """
        now = time.time()
        cutoff = now - self.window_seconds
        recent = [t for t in self._attempts[key] if t > cutoff]
        return max(0, self.max_attempts - len(recent))

    def reset(self, key: str) -> None:
        """Clear all recorded attempts for a key.

        Args:
            key: The rate limit key to reset.
        """
        self._attempts.pop(key, None)
