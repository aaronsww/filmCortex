import asyncio
from collections.abc import Mapping
from datetime import date
from typing import Any

import httpx

from filmcortex.integrations.tmdb.constants import TMDB_APPEND_TO_RESPONSE, TMDB_BASE_URL
from filmcortex.integrations.tmdb.rate_limit import AsyncRateLimiter


class TMDbClient:
    def __init__(
        self,
        api_key: str,
        client: httpx.AsyncClient | None = None,
        *,
        requests_per_second: float = 30.0,
        max_retries: int = 3,
        append_to_response: str = TMDB_APPEND_TO_RESPONSE,
    ) -> None:
        self._api_key = api_key
        self._append_to_response = append_to_response
        self._max_retries = max_retries
        self._rate_limiter = AsyncRateLimiter(requests_per_second=requests_per_second)
        self._client = client or httpx.AsyncClient(
            base_url=TMDB_BASE_URL,
            timeout=30.0,
        )
        self._owns_client = client is None

    async def close(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        use_auth: bool = True,
    ) -> dict:
        request_params = dict(params or {})
        if use_auth:
            request_params["api_key"] = self._api_key

        for attempt in range(self._max_retries + 1):
            await self._rate_limiter.acquire()
            response = await self._client.request(method, path, params=request_params)

            if response.status_code == 429 and attempt < self._max_retries:
                retry_after = float(response.headers.get("Retry-After", "2"))
                await asyncio.sleep(retry_after)
                continue

            response.raise_for_status()
            return response.json()

        raise RuntimeError(f"TMDb request failed after retries: {method} {path}")

    async def get_movie(self, movie_id: int) -> dict:
        return await self._request(
            "GET",
            f"/movie/{movie_id}",
            params={"append_to_response": self._append_to_response},
        )

    async def get_movie_changes(
        self,
        movie_id: int,
        *,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> dict:
        params: dict[str, str] = {}
        if start_date:
            params["start_date"] = start_date.isoformat()
        if end_date:
            params["end_date"] = end_date.isoformat()
        return await self._request("GET", f"/movie/{movie_id}/changes", params=params)

    async def search_movie(self, query: str) -> dict:
        return await self._request("GET", "/search/movie", params={"query": query})

    async def get_popular(self, page: int = 1) -> dict:
        return await self._request("GET", "/movie/popular", params={"page": page})

    async def get_top_rated(self, page: int = 1) -> dict:
        return await self._request("GET", "/movie/top_rated", params={"page": page})

    async def get_discover(self, page: int = 1, **filters: str | int | float) -> dict:
        params: dict[str, str | int | float] = {"page": page, **filters}
        return await self._request("GET", "/discover/movie", params=params)

    async def get_trending(self, time_window: str = "day", page: int = 1) -> dict:
        return await self._request(
            "GET",
            f"/trending/movie/{time_window}",
            params={"page": page},
        )

    async def get_list(self, list_id: int) -> dict:
        return await self._request("GET", f"/list/{list_id}")

    async def get_collection(self, collection_id: int) -> dict:
        return await self._request("GET", f"/collection/{collection_id}")
