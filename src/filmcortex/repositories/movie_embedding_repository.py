import uuid

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func

from filmcortex.integrations.tmdb.constants import TMDB_PROVIDER
from filmcortex.models.external_metadata import ExternalMetadata
from filmcortex.models.movie import Movie
from filmcortex.models.movie_embedding import MovieEmbedding


class MovieEmbeddingRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_movie_id(self, movie_id: uuid.UUID) -> MovieEmbedding | None:
        return await self._session.get(MovieEmbedding, movie_id)

    async def upsert(
        self,
        movie_id: uuid.UUID,
        embedding: list[float],
        embedded_text: str,
        model_name: str,
        model_revision: str | None = None,
    ) -> None:
        stmt = pg_insert(MovieEmbedding).values(
            movie_id=movie_id,
            embedding=embedding,
            embedded_text=embedded_text,
            model_name=model_name,
            model_revision=model_revision,
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=[MovieEmbedding.movie_id],
            set_={
                "embedding": stmt.excluded.embedding,
                "embedded_text": stmt.excluded.embedded_text,
                "model_name": stmt.excluded.model_name,
                "model_revision": stmt.excluded.model_revision,
                "generated_at": func.now(),
            },
        )
        await self._session.execute(stmt)

    async def list_movies_without_embeddings(self) -> list[tuple[Movie, ExternalMetadata]]:
        result = await self._session.execute(
            select(Movie, ExternalMetadata)
            .join(ExternalMetadata, ExternalMetadata.movie_id == Movie.id)
            .outerjoin(MovieEmbedding, MovieEmbedding.movie_id == Movie.id)
            .where(
                ExternalMetadata.is_active.is_(True),
                ExternalMetadata.provider == TMDB_PROVIDER,
                MovieEmbedding.movie_id.is_(None),
            )
            .order_by(Movie.canonical_title)
        )
        return list(result.all())
