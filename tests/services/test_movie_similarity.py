import uuid
from unittest.mock import AsyncMock

import pytest

from filmcortex.models.external_metadata import ExternalMetadata
from filmcortex.models.movie import MediaType, Movie
from filmcortex.services.movie_similarity import MovieSimilarityService


def _row(title: str, score: float) -> tuple[Movie, ExternalMetadata, float]:
    movie = Movie(id=uuid.uuid4(), canonical_title=title, media_type=MediaType.FILM)
    metadata = ExternalMetadata(
        id=uuid.uuid4(),
        movie_id=movie.id,
        provider="tmdb",
        provider_id="123",
        payload={},
        payload_version="2",
        is_active=True,
    )
    return movie, metadata, score


@pytest.fixture
def service() -> MovieSimilarityService:
    return MovieSimilarityService(embedding_repository=AsyncMock())


@pytest.mark.asyncio
async def test_returns_none_when_source_has_no_embedding(
    service: MovieSimilarityService,
) -> None:
    service._embedding_repository.get_by_movie_id.return_value = None

    result = await service.find_similar(uuid.uuid4())

    assert result is None
    service._embedding_repository.find_similar.assert_not_awaited()


@pytest.mark.asyncio
async def test_maps_rows_without_scores_by_default(service: MovieSimilarityService) -> None:
    service._embedding_repository.get_by_movie_id.return_value = object()
    service._embedding_repository.find_similar.return_value = [
        _row("Se7en", 0.87),
        _row("Zodiac", 0.81),
    ]

    result = await service.find_similar(uuid.uuid4())

    assert result is not None
    assert [m.canonical_title for m in result] == ["Se7en", "Zodiac"]
    assert all(m.similarity_score is None for m in result)


@pytest.mark.asyncio
async def test_includes_scores_when_requested(service: MovieSimilarityService) -> None:
    service._embedding_repository.get_by_movie_id.return_value = object()
    service._embedding_repository.find_similar.return_value = [_row("Se7en", 0.8712345678)]

    result = await service.find_similar(uuid.uuid4(), include_scores=True)

    assert result is not None
    assert result[0].similarity_score == 0.871235


@pytest.mark.asyncio
async def test_passes_limit_to_repository(service: MovieSimilarityService) -> None:
    service._embedding_repository.get_by_movie_id.return_value = object()
    service._embedding_repository.find_similar.return_value = []

    await service.find_similar(uuid.uuid4(), limit=5)

    service._embedding_repository.find_similar.assert_awaited_once()
    assert service._embedding_repository.find_similar.await_args.kwargs["limit"] == 5
