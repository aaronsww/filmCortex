from collections.abc import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from filmcortex.db.session import async_session_factory
from filmcortex.repositories.external_metadata_repository import ExternalMetadataRepository
from filmcortex.repositories.movie_embedding_repository import MovieEmbeddingRepository
from filmcortex.repositories.movie_repository import MovieRepository
from filmcortex.services.movie_query import MovieQueryService
from filmcortex.services.movie_similarity import MovieSimilarityService


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_movie_repository(
    session: AsyncSession = Depends(get_db),
) -> AsyncGenerator[MovieRepository, None]:
    yield MovieRepository(session)


async def get_external_metadata_repository(
    session: AsyncSession = Depends(get_db),
) -> AsyncGenerator[ExternalMetadataRepository, None]:
    yield ExternalMetadataRepository(session)


async def get_movie_embedding_repository(
    session: AsyncSession = Depends(get_db),
) -> AsyncGenerator[MovieEmbeddingRepository, None]:
    yield MovieEmbeddingRepository(session)


async def get_movie_query_service(
    metadata_repository: ExternalMetadataRepository = Depends(get_external_metadata_repository),
    movie_repository: MovieRepository = Depends(get_movie_repository),
    embedding_repository: MovieEmbeddingRepository = Depends(get_movie_embedding_repository),
) -> MovieQueryService:
    return MovieQueryService(metadata_repository, movie_repository, embedding_repository)


async def get_movie_similarity_service(
    embedding_repository: MovieEmbeddingRepository = Depends(get_movie_embedding_repository),
) -> MovieSimilarityService:
    return MovieSimilarityService(embedding_repository)
