import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Literal

from filmcortex.integrations.tmdb.client import TMDbClient
from filmcortex.integrations.tmdb.constants import TMDB_PAYLOAD_VERSION, TMDB_PROVIDER
from filmcortex.models.movie import MediaType
from filmcortex.repositories.external_metadata_repository import ExternalMetadataRepository
from filmcortex.repositories.movie_repository import MovieRepository
from filmcortex.utils.payload import payload_fingerprint

logger = logging.getLogger(__name__)

IngestResult = Literal["inserted", "updated", "skipped"]


@dataclass
class IngestionStats:
    fetched: int = 0
    inserted: int = 0
    updated: int = 0
    skipped: int = 0


class TMDbIngestionService:
    def __init__(
        self,
        tmdb_client: TMDbClient,
        movie_repository: MovieRepository,
        metadata_repository: ExternalMetadataRepository,
    ) -> None:
        self._tmdb_client = tmdb_client
        self._movie_repository = movie_repository
        self._metadata_repository = metadata_repository

    async def ingest_movie(self, tmdb_id: int) -> IngestResult:
        payload = await self._tmdb_client.get_movie(tmdb_id)
        provider_id = str(payload["id"])
        title = payload.get("title") or payload.get("original_title") or "Unknown"
        fingerprint = payload_fingerprint(payload)

        existing = await self._metadata_repository.get_by_provider(
            provider=TMDB_PROVIDER,
            provider_id=provider_id,
        )

        if existing is None:
            movie = await self._movie_repository.create(
                canonical_title=title,
                media_type=MediaType.FILM,
            )
            await self._metadata_repository.create(
                movie_id=movie.id,
                provider=TMDB_PROVIDER,
                provider_id=provider_id,
                payload=payload,
                payload_version=TMDB_PAYLOAD_VERSION,
            )
            logger.info(
                "movie_inserted",
                extra={
                    "tmdb_id": tmdb_id,
                    "movie_id": str(movie.id),
                    "title": title,
                },
            )
            return "inserted"

        if existing.payload_fingerprint == fingerprint:
            logger.info(
                "movie_skipped",
                extra={
                    "tmdb_id": tmdb_id,
                    "movie_id": str(existing.movie_id),
                    "title": title,
                },
            )
            return "skipped"

        await self._movie_repository.update_title(existing.movie_id, title)
        await self._metadata_repository.update_payload(
            metadata_id=existing.id,
            payload=payload,
            payload_version=TMDB_PAYLOAD_VERSION,
            fetched_at=datetime.now(UTC),
        )
        logger.info(
            "movie_updated",
            extra={
                "tmdb_id": tmdb_id,
                "movie_id": str(existing.movie_id),
                "title": title,
            },
        )
        return "updated"

    async def ingest_popular_page(self, page: int = 1) -> IngestionStats:
        stats = IngestionStats()
        response = await self._tmdb_client.get_popular(page=page)
        results = response.get("results", [])
        stats.fetched = len(results)

        for item in results:
            tmdb_id = item["id"]
            result = await self.ingest_movie(tmdb_id)
            if result == "inserted":
                stats.inserted += 1
            elif result == "updated":
                stats.updated += 1
            else:
                stats.skipped += 1

        return stats
