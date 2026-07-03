import os
import uuid

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from filmcortex.models.movie import MediaType
from filmcortex.repositories.external_metadata_repository import ExternalMetadataRepository
from filmcortex.repositories.movie_embedding_repository import MovieEmbeddingRepository
from filmcortex.repositories.movie_repository import MovieRepository

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


@pytest.fixture
async def session():
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        pytest.skip("DATABASE_URL is not set")

    engine = create_async_engine(database_url)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session
        await session.rollback()
    await engine.dispose()


async def _seed_movie(session) -> uuid.UUID:
    movie_repo = MovieRepository(session)
    metadata_repo = ExternalMetadataRepository(session)
    movie = await movie_repo.create(canonical_title="Seed Movie", media_type=MediaType.FILM)
    await metadata_repo.create(
        movie_id=movie.id,
        provider="tmdb",
        provider_id=f"seed-{uuid.uuid4()}",
        payload={"title": "Seed Movie"},
        payload_version="2",
    )
    await session.flush()
    return movie.id


async def test_upsert_inserts_then_updates(session) -> None:
    repo = MovieEmbeddingRepository(session)
    movie_id = await _seed_movie(session)
    dim = 384

    await repo.upsert(
        movie_id=movie_id,
        embedding=[0.0] * dim,
        embedded_text="first",
        model_name="test-model",
    )
    stored = await repo.get_by_movie_id(movie_id)
    assert stored is not None
    assert stored.embedded_text == "first"

    await repo.upsert(
        movie_id=movie_id,
        embedding=[1.0] * dim,
        embedded_text="second",
        model_name="test-model",
        model_revision="abc123",
    )
    await session.refresh(stored)
    assert stored.embedded_text == "second"
    assert stored.model_revision == "abc123"


async def test_list_movies_without_embeddings(session) -> None:
    repo = MovieEmbeddingRepository(session)
    movie_id = await _seed_movie(session)

    pending_ids = {movie.id for movie, _ in await repo.list_movies_without_embeddings()}
    assert movie_id in pending_ids

    await repo.upsert(
        movie_id=movie_id,
        embedding=[0.0] * 384,
        embedded_text="done",
        model_name="test-model",
    )
    await session.flush()

    pending_ids = {movie.id for movie, _ in await repo.list_movies_without_embeddings()}
    assert movie_id not in pending_ids
