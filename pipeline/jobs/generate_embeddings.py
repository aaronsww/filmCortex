import asyncio
import logging

from filmcortex.core.logging import configure_logging
from filmcortex.db.session import async_session_factory
from filmcortex.repositories.movie_embedding_repository import MovieEmbeddingRepository
from filmcortex.services.movie_embedding import MovieEmbeddingService

logger = logging.getLogger(__name__)


async def run() -> None:
    configure_logging()

    async with async_session_factory() as session:
        service = MovieEmbeddingService(
            embedding_repository=MovieEmbeddingRepository(session),
        )
        stats = await service.generate_all()
        await session.commit()

    print(f"Pending {stats.pending} movies")
    print(f"Generated {stats.generated}")
    print(f"Failed {stats.failed}")


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
