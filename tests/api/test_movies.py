import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from filmcortex.api.deps import get_movie_query_service
from filmcortex.main import app
from filmcortex.schemas.movie import MovieListItem
from filmcortex.services.movie_query import MovieQueryService


class FakeMovieQueryService(MovieQueryService):
    def __init__(self) -> None:
        pass

    async def list_movies(self) -> list[MovieListItem]:
        return [
            MovieListItem(
                id=uuid.uuid4(),
                canonical_title="Fight Club",
                provider="tmdb",
                provider_id="550",
            )
        ]


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
    assert len(data) == 1
    assert data[0]["canonical_title"] == "Fight Club"
    assert data[0]["provider"] == "tmdb"
    assert data[0]["provider_id"] == "550"
