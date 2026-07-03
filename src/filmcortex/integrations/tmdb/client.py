import httpx

from filmcortex.integrations.tmdb.constants import TMDB_BASE_URL


class TMDbClient:
    def __init__(self, api_key: str, client: httpx.AsyncClient | None = None) -> None:
        self._api_key = api_key
        self._client = client or httpx.AsyncClient(
            base_url=TMDB_BASE_URL,
            timeout=30.0,
        )
        self._owns_client = client is None

    async def close(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def get_movie(self, movie_id: int) -> dict:
        response = await self._client.get(
            f"/movie/{movie_id}",
            params={
                "api_key": self._api_key,
                "append_to_response": "credits,keywords",
            },
        )
        response.raise_for_status()
        return response.json()

    async def search_movie(self, query: str) -> dict:
        response = await self._client.get(
            "/search/movie",
            params={"api_key": self._api_key, "query": query},
        )
        response.raise_for_status()
        return response.json()

    async def get_popular(self, page: int = 1) -> dict:
        response = await self._client.get(
            "/movie/popular",
            params={"api_key": self._api_key, "page": page},
        )
        response.raise_for_status()
        return response.json()
