import asyncio
import time


class AsyncRateLimiter:
    """Token-bucket rate limiter for TMDb API calls (~40 req/s)."""

    def __init__(self, requests_per_second: float = 30.0) -> None:
        self._interval = 1.0 / requests_per_second
        self._lock = asyncio.Lock()
        self._last_request_at = 0.0

    async def acquire(self) -> None:
        async with self._lock:
            now = time.monotonic()
            wait = self._interval - (now - self._last_request_at)
            if wait > 0:
                await asyncio.sleep(wait)
            self._last_request_at = time.monotonic()
