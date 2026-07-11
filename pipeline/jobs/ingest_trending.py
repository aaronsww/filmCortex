"""Ingest currently trending movies from TMDb.

Run daily:
    uv run python -m pipeline.jobs.ingest_trending
    uv run python -m pipeline.jobs.ingest_trending --time-window week
"""

import argparse
import asyncio

from filmcortex.config.settings import settings
from pipeline.shared.job_context import ingestion_job, print_ingestion_stats
from pipeline.shared.limits import resolve_limit


async def run(*, time_window: str, limit: int, max_pages: int | None) -> None:
    async with ingestion_job() as context:
        stats = await context.ingestion_service.ingest_trending(
            time_window=time_window,
            max_pages=max_pages,
            max_movies=limit,
        )
    print_ingestion_stats(stats, label=f"Trending ({time_window})")


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest TMDb trending movies")
    parser.add_argument(
        "--time-window",
        choices=["day", "week"],
        default="day",
        help="Trending time window",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help=(
            "Maximum number of movies to ingest "
            f"(default: {settings.tmdb_trending_limit} from TMDB_TRENDING_LIMIT)"
        ),
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=None,
        help="Optional page cap (in addition to --limit)",
    )
    args = parser.parse_args()
    asyncio.run(
        run(
            time_window=args.time_window,
            limit=resolve_limit(args.limit, settings.tmdb_trending_limit),
            max_pages=args.max_pages,
        )
    )


if __name__ == "__main__":
    main()
