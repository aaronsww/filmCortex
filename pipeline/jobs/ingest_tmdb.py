import asyncio
import logging
import sys

from filmcortex.config.settings import settings
from filmcortex.core.logging import configure_logging
from filmcortex.db.session import async_session_factory
from filmcortex.integrations.tmdb.client import TMDbClient
from filmcortex.repositories.external_metadata_repository import ExternalMetadataRepository
from filmcortex.repositories.movie_repository import MovieRepository
from filmcortex.services.tmdb_ingestion import TMDbIngestionService

logger = logging.getLogger(__name__)


async def run() -> None:
    if not settings.tmdb_api_key:
        logger.error("TMDB_API_KEY is not set")
        sys.exit(1)

    configure_logging()
    tmdb_client = TMDbClient(api_key=settings.tmdb_api_key)

    try:
        async with async_session_factory() as session:
            ingestion_service = TMDbIngestionService(
                tmdb_client=tmdb_client,
                movie_repository=MovieRepository(session),
                metadata_repository=ExternalMetadataRepository(session),
            )
            stats = await ingestion_service.ingest_popular_page(page=1)
            await session.commit()

        print(f"Fetched {stats.fetched} movies")
        print(f"Inserted {stats.inserted}")
        print(f"Updated {stats.updated}")
        print(f"Skipped {stats.skipped}")
    finally:
        await tmdb_client.close()


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
