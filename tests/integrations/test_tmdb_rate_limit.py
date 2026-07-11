import asyncio
import time

import pytest

from filmcortex.integrations.tmdb.rate_limit import AsyncRateLimiter


@pytest.mark.asyncio
async def test_rate_limiter_enforces_minimum_interval() -> None:
    limiter = AsyncRateLimiter(requests_per_second=10.0)

    start = time.monotonic()
    await limiter.acquire()
    await limiter.acquire()
    elapsed = time.monotonic() - start

    assert elapsed >= 0.08
