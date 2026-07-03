import uuid
from unittest.mock import AsyncMock

import pytest

from filmcortex.models.external_metadata import ExternalMetadata
from filmcortex.models.movie import MediaType, Movie
from filmcortex.services.movie_embedding import MovieEmbeddingService


def _movie_and_metadata() -> tuple[Movie, ExternalMetadata]:
    movie = Movie(id=uuid.uuid4(), canonical_title="Fight Club", media_type=MediaType.FILM)
    metadata = ExternalMetadata(
        id=uuid.uuid4(),
        movie_id=movie.id,
        provider="tmdb",
        provider_id="550",
        payload={"title": "Fight Club", "overview": "An insomniac forms a fight club."},
        payload_version="2",
        is_active=True,
    )
    return movie, metadata


@pytest.fixture
def service() -> MovieEmbeddingService:
    repository = AsyncMock()
    svc = MovieEmbeddingService(embedding_repository=repository, model_name="test-model")
    svc.embed_text = lambda text: [0.1, 0.2, 0.3]  # type: ignore[assignment]
    return svc


@pytest.mark.asyncio
async def test_generate_for_movie_builds_text_and_upserts(
    service: MovieEmbeddingService,
) -> None:
    movie, metadata = _movie_and_metadata()

    await service.generate_for_movie(movie, metadata)

    service._repository.upsert.assert_awaited_once()
    kwargs = service._repository.upsert.await_args.kwargs
    assert kwargs["movie_id"] == movie.id
    assert kwargs["embedding"] == [0.1, 0.2, 0.3]
    assert "Fight Club" in kwargs["embedded_text"]
    assert kwargs["model_name"] == "test-model"
    assert kwargs["model_revision"] is None


@pytest.mark.asyncio
async def test_generate_all_counts_pending_and_generated(
    service: MovieEmbeddingService,
) -> None:
    pending = [_movie_and_metadata(), _movie_and_metadata()]
    service._repository.list_movies_without_embeddings.return_value = pending

    stats = await service.generate_all()

    assert stats.pending == 2
    assert stats.generated == 2
    assert stats.failed == 0
    assert service._repository.upsert.await_count == 2


@pytest.mark.asyncio
async def test_generate_all_records_failures(service: MovieEmbeddingService) -> None:
    pending = [_movie_and_metadata(), _movie_and_metadata()]
    service._repository.list_movies_without_embeddings.return_value = pending

    calls = {"n": 0}

    def flaky(_text: str) -> list[float]:
        calls["n"] += 1
        if calls["n"] == 1:
            raise RuntimeError("boom")
        return [0.1, 0.2, 0.3]

    service.embed_text = flaky  # type: ignore[assignment]

    stats = await service.generate_all()

    assert stats.pending == 2
    assert stats.generated == 1
    assert stats.failed == 1


@pytest.mark.asyncio
async def test_generate_all_with_no_pending(service: MovieEmbeddingService) -> None:
    service._repository.list_movies_without_embeddings.return_value = []

    stats = await service.generate_all()

    assert stats.pending == 0
    assert stats.generated == 0
    assert stats.failed == 0
    service._repository.upsert.assert_not_awaited()
