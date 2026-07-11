from __future__ import annotations

import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path

from filmcortex.config.settings import settings
from filmcortex.core.logging import configure_logging
from filmcortex.db.session import async_session_factory
from filmcortex.integrations.tmdb.client import TMDbClient
from filmcortex.repositories.external_metadata_repository import ExternalMetadataRepository
from filmcortex.repositories.movie_repository import MovieRepository
from filmcortex.services.tmdb_ingestion import IngestionStats, TMDbIngestionService


@dataclass
class JobContext:
    ingestion_service: TMDbIngestionService
    tmdb_client: TMDbClient
    export_cache_dir: Path


def require_tmdb_api_key() -> None:
    if not settings.tmdb_api_key:
        print("TMDB_API_KEY is not set", file=sys.stderr)
        sys.exit(1)


@asynccontextmanager
async def ingestion_job() -> AsyncIterator[JobContext]:
    configure_logging()
    require_tmdb_api_key()

    tmdb_client = TMDbClient(
        api_key=settings.tmdb_api_key,
        requests_per_second=settings.tmdb_requests_per_second,
    )
    export_cache_dir = Path(settings.tmdb_export_cache_dir)

    try:
        async with async_session_factory() as session:
            context = JobContext(
                ingestion_service=TMDbIngestionService(
                    tmdb_client=tmdb_client,
                    movie_repository=MovieRepository(session),
                    metadata_repository=ExternalMetadataRepository(session),
                ),
                tmdb_client=tmdb_client,
                export_cache_dir=export_cache_dir,
            )
            yield context
            await session.commit()
    finally:
        await tmdb_client.close()


def print_ingestion_stats(stats: IngestionStats, *, label: str | None = None) -> None:
    prefix = f"{label}: " if label else ""
    print(f"{prefix}Fetched {stats.fetched}")
    print(f"{prefix}Inserted {stats.inserted}")
    print(f"{prefix}Updated {stats.updated}")
    print(f"{prefix}Skipped {stats.skipped}")
    print(f"{prefix}Failed {stats.failed}")
