import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from filmcortex.api.deps import get_movie_similarity_service
from filmcortex.main import app
from filmcortex.schemas.movie import SimilarMovie
from filmcortex.services.movie_similarity import MovieSimilarityService


class FakeMovieSimilarityService(MovieSimilarityService):
    def __init__(self) -> None:
        pass

    async def find_similar(
        self,
        movie_id: uuid.UUID,
        limit: int = 10,
        include_scores: bool = False,
    ) -> list[SimilarMovie] | None:
        if movie_id == uuid.UUID(int=0):
            return None
        return [
            SimilarMovie(
                id=uuid.uuid4(),
                canonical_title="Se7en",
                provider="tmdb",
                provider_id="807",
                similarity_score=0.871235 if include_scores else None,
            ),
            SimilarMovie(
                id=uuid.uuid4(),
                canonical_title="Zodiac",
                provider="tmdb",
                provider_id="1944",
                similarity_score=0.812345 if include_scores else None,
            ),
        ]


@pytest.fixture
def client():
    app.dependency_overrides[get_movie_similarity_service] = lambda: FakeMovieSimilarityService()
    transport = ASGITransport(app=app)
    yield AsyncClient(transport=transport, base_url="http://test")
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_list_similar_movies(client: AsyncClient) -> None:
    movie_id = uuid.uuid4()
    response = await client.get(f"/api/v1/movies/{movie_id}/similar")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["canonical_title"] == "Se7en"
    assert data[0]["provider"] == "tmdb"
    assert data[0]["provider_id"] == "807"
    assert "similarity_score" not in data[0]


@pytest.mark.asyncio
async def test_list_similar_movies_with_scores(client: AsyncClient) -> None:
    movie_id = uuid.uuid4()
    response = await client.get(f"/api/v1/movies/{movie_id}/similar?include_scores=true")

    assert response.status_code == 200
    data = response.json()
    assert data[0]["similarity_score"] == 0.871235
    assert data[1]["similarity_score"] == 0.812345


@pytest.mark.asyncio
async def test_list_similar_movies_not_found(client: AsyncClient) -> None:
    movie_id = uuid.UUID(int=0)
    response = await client.get(f"/api/v1/movies/{movie_id}/similar")

    assert response.status_code == 404
    assert response.json()["detail"] == "Movie not found or has no embedding"
