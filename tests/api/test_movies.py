import uuid
from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient

from filmcortex.api.deps import get_movie_query_service
from filmcortex.main import app
from filmcortex.schemas.movie import MovieListItem, MovieListPage, MovieStats
from filmcortex.services.movie_query import MovieQueryService
from filmcortex.utils.cursor import CursorError, encode_movie_list_cursor


class FakeMovieQueryService(MovieQueryService):
    def __init__(self) -> None:
        pass

    async def list_movies(
        self,
        *,
        cursor: str | None = None,
        page_size: int = 50,
    ) -> MovieListPage:
        if cursor == "bad":
            raise CursorError("Invalid cursor")
        return MovieListPage(
            items=[
                MovieListItem(
                    id=uuid.uuid4(),
                    canonical_title="Fight Club",
                    provider="tmdb",
                    provider_id="550",
                )
            ],
            next_cursor=None,
            page_size=page_size,
        )

    async def get_stats(self) -> MovieStats:
        return MovieStats(movies=10, embeddings=7, pending_embeddings=3)


@pytest.fixture
def client():
    app.dependency_overrides[get_movie_query_service] = lambda: FakeMovieQueryService()
    transport = ASGITransport(app=app)
    yield AsyncClient(transport=transport, base_url="http://test")
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_list_movies(client: AsyncClient) -> None:
    response = await client.get("/api/v1/movies")
    assert response.status_code == 200
    data = response.json()
    assert data["page_size"] == 50
    assert data["next_cursor"] is None
    assert len(data["items"]) == 1
    assert data["items"][0]["canonical_title"] == "Fight Club"
    assert data["items"][0]["provider"] == "tmdb"
    assert data["items"][0]["provider_id"] == "550"


@pytest.mark.asyncio
async def test_list_movies_rejects_invalid_cursor(client: AsyncClient) -> None:
    response = await client.get("/api/v1/movies", params={"cursor": "bad"})
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid cursor"


@pytest.mark.asyncio
async def test_list_movies_rejects_oversized_page(client: AsyncClient) -> None:
    response = await client.get("/api/v1/movies", params={"page_size": 101})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_movie_stats(client: AsyncClient) -> None:
    response = await client.get("/api/v1/movies/stats")
    assert response.status_code == 200
    assert response.json() == {
        "movies": 10,
        "embeddings": 7,
        "pending_embeddings": 3,
    }


@pytest.mark.asyncio
async def test_list_movies_service_paginates() -> None:
    metadata_id = uuid.uuid4()
    movie = AsyncMock(id=uuid.uuid4(), canonical_title="Alien")
    metadata = AsyncMock(id=metadata_id, provider="tmdb", provider_id="348")
    extra_movie = AsyncMock(id=uuid.uuid4(), canonical_title="Blade Runner")
    extra_metadata = AsyncMock(id=uuid.uuid4(), provider="tmdb", provider_id="78")

    metadata_repo = AsyncMock()
    metadata_repo.list_active_with_movies.return_value = [
        (movie, metadata),
        (extra_movie, extra_metadata),
    ]
    service = MovieQueryService(metadata_repo, AsyncMock(), AsyncMock())

    page = await service.list_movies(page_size=1)

    metadata_repo.list_active_with_movies.assert_awaited_once_with(
        limit=2,
        after_title=None,
        after_metadata_id=None,
    )
    assert len(page.items) == 1
    assert page.items[0].canonical_title == "Alien"
    assert page.next_cursor == encode_movie_list_cursor(
        title="Alien",
        metadata_id=metadata_id,
    )

    metadata_repo.list_active_with_movies.reset_mock()
    metadata_repo.list_active_with_movies.return_value = [(extra_movie, extra_metadata)]
    page2 = await service.list_movies(cursor=page.next_cursor, page_size=1)
    metadata_repo.list_active_with_movies.assert_awaited_once_with(
        limit=2,
        after_title="Alien",
        after_metadata_id=metadata_id,
    )
    assert page2.next_cursor is None
