import uuid

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

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

    async def find_similar(
        self,
        movie_id: uuid.UUID,
        limit: int = 10,
    ) -> list[tuple[Movie, ExternalMetadata, float]]:
        source = await self._session.get(MovieEmbedding, movie_id)
        if source is None:
            return []

        distance = MovieEmbedding.embedding.cosine_distance(source.embedding).label("distance")
        result = await self._session.execute(
            select(Movie, ExternalMetadata, distance)
            .join(MovieEmbedding, MovieEmbedding.movie_id == Movie.id)
            .join(ExternalMetadata, ExternalMetadata.movie_id == Movie.id)
            .where(
                MovieEmbedding.movie_id != movie_id,
                ExternalMetadata.is_active.is_(True),
                ExternalMetadata.provider == TMDB_PROVIDER,
            )
            .order_by(distance)
            .limit(limit)
        )
        return [(movie, metadata, 1.0 - distance) for movie, metadata, distance in result.all()]

    async def count(self) -> int:
        result = await self._session.execute(select(func.count()).select_from(MovieEmbedding))
        return int(result.scalar_one())

    async def count_movies_without_embeddings(self) -> int:
        result = await self._session.execute(
            select(func.count())
            .select_from(Movie)
            .join(ExternalMetadata, ExternalMetadata.movie_id == Movie.id)
            .outerjoin(MovieEmbedding, MovieEmbedding.movie_id == Movie.id)
            .where(
                ExternalMetadata.is_active.is_(True),
                ExternalMetadata.provider == TMDB_PROVIDER,
                MovieEmbedding.movie_id.is_(None),
            )
        )
        return int(result.scalar_one())

    async def list_movies_without_embeddings(
        self,
        *,
        limit: int | None = None,
    ) -> list[tuple[Movie, ExternalMetadata]]:
        stmt = (
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
        if limit is not None:
            stmt = stmt.limit(limit)
        result = await self._session.execute(stmt)
        return list(result.all())
