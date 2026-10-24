"""Small, dependency-free security helpers."""
from __future__ import annotations

import threading
import time
from collections import defaultdict, deque
from collections.abc import Callable

SECURITY_HEADERS = {
    "Content-Security-Policy": (
        "default-src 'self'; img-src 'self' data:; base-uri 'none'; "
        "form-action 'self'; frame-ancestors 'none'"
    ),
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
}


class RateLimiter:
    """Sliding-window limiter: at most ``limit`` calls per ``window`` seconds per key.

    In-memory, so it protects a single process. Behind several workers or a
    proxy, enforce limits at the gateway as well (see README).
    """

    _MAX_KEYS = 10_000

    def __init__(self, limit: int, window: float = 60.0, clock: Callable[[], float] = time.monotonic) -> None:
        self._limit = limit
        self._window = window
        self._clock = clock
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def allow(self, key: str) -> bool:
        now = self._clock()
        with self._lock:
            if len(self._hits) > self._MAX_KEYS:
                self._evict(now)
            hits = self._hits[key]
            while hits and now - hits[0] >= self._window:
                hits.popleft()
            if len(hits) >= self._limit:
                return False
            hits.append(now)
            return True

    def _evict(self, now: float) -> None:
        """Drop idle keys so memory stays bounded."""
        for key in [k for k, h in self._hits.items() if not h or now - h[-1] >= self._window]:
            del self._hits[key]
