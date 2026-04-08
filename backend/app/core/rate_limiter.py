"""
In-memory IP-based rate limiter.

Tracks attempts per (key, IP) and blocks when threshold is exceeded.
Entries auto-expire after the window period.

For production at scale, replace with Redis-backed limiter.
"""

import time
import threading
from collections import defaultdict

from fastapi import HTTPException, Request, status


class RateLimiter:
    """Simple sliding-window rate limiter."""

    def __init__(self, max_attempts: int, window_seconds: int):
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self._attempts: dict[str, list[float]] = defaultdict(list)
        self._lock = threading.Lock()

    def _clean_expired(self, key: str) -> None:
        """Remove expired timestamps for a key."""
        cutoff = time.time() - self.window_seconds
        self._attempts[key] = [
            ts for ts in self._attempts[key] if ts > cutoff
        ]

    def check(self, key: str) -> bool:
        """Check if the key is rate-limited. Returns True if allowed."""
        with self._lock:
            self._clean_expired(key)
            return len(self._attempts[key]) < self.max_attempts

    def record(self, key: str) -> None:
        """Record an attempt for the key."""
        with self._lock:
            self._attempts[key].append(time.time())

    def remaining(self, key: str) -> int:
        """Return remaining attempts for the key."""
        with self._lock:
            self._clean_expired(key)
            return max(0, self.max_attempts - len(self._attempts[key]))

    def check_and_record(self, key: str) -> int:
        """
        Check + record atomically.
        Returns remaining attempts, or raises 429 if exceeded.
        """
        with self._lock:
            self._clean_expired(key)
            if len(self._attempts[key]) >= self.max_attempts:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=(
                        f"Too many attempts. Maximum {self.max_attempts} "
                        f"per {self.window_seconds // 60} minutes. "
                        f"Please try again later."
                    ),
                )
            self._attempts[key].append(time.time())
            return self.max_attempts - len(self._attempts[key])


def get_client_ip(request: Request) -> str:
    """Extract client IP, respecting X-Forwarded-For behind proxy."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


# ── Pre-configured limiters ──────────────────────────────────

# Authorization code validation: 5 attempts per IP per 15 min
code_validation_limiter = RateLimiter(max_attempts=5, window_seconds=900)

# Claim submission: 3 submissions per IP per 30 min
submission_limiter = RateLimiter(max_attempts=3, window_seconds=1800)

# Member lookup: 10 attempts per IP per 15 min
member_lookup_limiter = RateLimiter(max_attempts=10, window_seconds=900)
