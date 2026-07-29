import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from filmcortex.integrations.tmdb.client import TMDbClient
from filmcortex.integrations.tmdb.constants import (
    TMDB_LIST_MAX_PAGE,
    TMDB_PAYLOAD_VERSION,
    TMDB_PROVIDER,
)
from filmcortex.integrations.tmdb.exports import (
    diff_movie_ids,
    download_daily_export,
    find_previous_export,
    parse_movie_ids,
)
from filmcortex.models.movie import MediaType
from filmcortex.repositories.external_metadata_repository import ExternalMetadataRepository
from filmcortex.repositories.movie_repository import MovieRepository
from filmcortex.utils.payload import payload_fingerprint

logger = logging.getLogger(__name__)

IngestResult = Literal["inserted", "updated", "skipped", "failed"]


@dataclass
class IngestionStats:
    fetched: int = 0
    inserted: int = 0
    updated: int = 0
    skipped: int = 0
    failed: int = 0

    def merge(self, other: "IngestionStats") -> None:
        self.fetched += other.fetched
        self.inserted += other.inserted
        self.updated += other.updated
        self.skipped += other.skipped
        self.failed += other.failed


@dataclass
class PagedIngestionStats(IngestionStats):
    """Paged list crawl stats, including where the next run should resume."""

    next_page: int = 1
    pages_scanned: int = 0


@dataclass
class ExportIngestionStats:
    export_path: Path | None = None
    total_ids: int = 0
    new_ids: int = 0
    ingestion: IngestionStats = field(default_factory=IngestionStats)


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
        try:
            payload = await self._tmdb_client.get_movie(tmdb_id)
        except Exception:
            logger.exception("movie_fetch_failed", extra={"tmdb_id": tmdb_id})
            return "failed"

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

    async def ingest_ids(self, tmdb_ids: list[int]) -> IngestionStats:
        stats = IngestionStats(fetched=len(tmdb_ids))
        for tmdb_id in tmdb_ids:
            result = await self.ingest_movie(tmdb_id)
            if result == "inserted":
                stats.inserted += 1
            elif result == "updated":
                stats.updated += 1
            elif result == "skipped":
                stats.skipped += 1
            else:
                stats.failed += 1
        return stats

    async def ingest_from_paged_endpoint(
        self,
        fetch_page: Callable[[int], Awaitable[dict]],
        *,
        max_pages: int | None = None,
        max_movies: int | None = None,
        start_page: int = 1,
        skip_existing: bool = False,
        wrap: bool = False,
        max_page_number: int = TMDB_LIST_MAX_PAGE,
    ) -> PagedIngestionStats:
        stats = PagedIngestionStats()
        page = max(1, min(start_page, max_page_number))
        detail_fetches = 0

        while True:
            response = await fetch_page(page)
            results = response.get("results", [])
            stats.pages_scanned += 1

            reported_total = int(response.get("total_pages", page) or page)
            last_page = max(1, min(reported_total, max_page_number))

            if page > last_page:
                if wrap and page != 1:
                    page = 1
                    continue
                stats.next_page = 1 if wrap else last_page
                return stats

            if not results:
                stats.next_page = 1 if wrap else page
                return stats

            existing: set[str] = set()
            if skip_existing:
                provider_ids = [str(item["id"]) for item in results if "id" in item]
                existing = await self._metadata_repository.get_existing_provider_ids(
                    provider=TMDB_PROVIDER,
                    provider_ids=provider_ids,
                )

            hit_movie_limit = False
            for item in results:
                if "id" not in item:
                    continue
                tmdb_id = item["id"]
                if skip_existing and str(tmdb_id) in existing:
                    stats.skipped += 1
                    continue

                if max_movies is not None and detail_fetches >= max_movies:
                    hit_movie_limit = True
                    break

                detail_fetches += 1
                stats.fetched += 1
                result = await self.ingest_movie(tmdb_id)
                if result == "inserted":
                    stats.inserted += 1
                elif result == "updated":
                    stats.updated += 1
                elif result == "skipped":
                    stats.skipped += 1
                else:
                    stats.failed += 1

            if hit_movie_limit:
                # Resume on the same page; already-ingested IDs will be skipped next run.
                stats.next_page = page
                return stats

            if page >= last_page:
                stats.next_page = 1 if wrap else page
                return stats

            if max_pages is not None and stats.pages_scanned >= max_pages:
                stats.next_page = page + 1
                return stats

            page += 1

    async def ingest_popular_page(self, page: int = 1) -> PagedIngestionStats:
        return await self.ingest_from_paged_endpoint(
            lambda current_page: self._tmdb_client.get_popular(page=current_page),
            max_pages=1,
            start_page=page,
        )

    async def ingest_top_rated(
        self,
        *,
        max_pages: int | None = None,
        max_movies: int | None = None,
        start_page: int = 1,
        skip_existing: bool = False,
        wrap: bool = False,
    ) -> PagedIngestionStats:
        return await self.ingest_from_paged_endpoint(
            lambda page: self._tmdb_client.get_top_rated(page=page),
            max_pages=max_pages,
            max_movies=max_movies,
            start_page=start_page,
            skip_existing=skip_existing,
            wrap=wrap,
        )

    async def ingest_discover(
        self,
        *,
        filters: dict[str, str | int | float],
        max_pages: int | None = None,
        max_movies: int | None = None,
        skip_existing: bool = False,
    ) -> PagedIngestionStats:
        return await self.ingest_from_paged_endpoint(
            lambda page: self._tmdb_client.get_discover(page=page, **filters),
            max_pages=max_pages,
            max_movies=max_movies,
            skip_existing=skip_existing,
        )

    async def ingest_trending(
        self,
        *,
        time_window: str = "day",
        max_pages: int | None = None,
        max_movies: int | None = None,
        skip_existing: bool = False,
    ) -> PagedIngestionStats:
        return await self.ingest_from_paged_endpoint(
            lambda page: self._tmdb_client.get_trending(time_window=time_window, page=page),
            max_pages=max_pages,
            max_movies=max_movies,
            skip_existing=skip_existing,
        )

    async def ingest_list(self, list_id: int) -> IngestionStats:
        response = await self._tmdb_client.get_list(list_id)
        items = response.get("items") or []
        ids = [item["id"] for item in items if "id" in item]
        return await self.ingest_ids(ids)

    async def ingest_daily_export(
        self,
        cache_dir: Path,
        *,
        ingest_all: bool = False,
        limit: int | None = None,
    ) -> ExportIngestionStats:
        export_path = await download_daily_export(cache_dir)
        all_ids = parse_movie_ids(export_path)

        if ingest_all:
            target_ids = all_ids
        else:
            previous_path = find_previous_export(cache_dir, export_path)
            if previous_path is None:
                existing = await self._metadata_repository.get_existing_provider_ids(
                    provider=TMDB_PROVIDER,
                    provider_ids=[str(movie_id) for movie_id in all_ids],
                )
                target_ids = [movie_id for movie_id in all_ids if str(movie_id) not in existing]
            else:
                previous_ids = parse_movie_ids(previous_path)
                target_ids = diff_movie_ids(all_ids, previous_ids)

        if limit is not None:
            target_ids = target_ids[:limit]

        ingestion_stats = await self.ingest_ids(target_ids)
        return ExportIngestionStats(
            export_path=export_path,
            total_ids=len(all_ids),
            new_ids=len(target_ids),
            ingestion=ingestion_stats,
        )
