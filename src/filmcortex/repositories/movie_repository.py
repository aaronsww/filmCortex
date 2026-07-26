import uuid

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from filmcortex.models.movie import MediaType, Movie


class MovieRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, canonical_title: str, media_type: MediaType) -> Movie:
        movie = Movie(
            canonical_title=canonical_title,
            media_type=media_type,
        )
        self._session.add(movie)
        await self._session.flush()
        return movie

    async def get_by_id(self, movie_id: uuid.UUID) -> Movie | None:
        return await self._session.get(Movie, movie_id)

    async def update_title(self, movie_id: uuid.UUID, canonical_title: str) -> None:
        await self._session.execute(
            update(Movie)
            .where(Movie.id == movie_id)
            .values(canonical_title=canonical_title)
        )

    async def count(self) -> int:
        result = await self._session.execute(select(func.count()).select_from(Movie))
        return int(result.scalar_one())

    async def list_all(self) -> list[Movie]:
        result = await self._session.execute(select(Movie).order_by(Movie.canonical_title))
        return list(result.scalars().all())
