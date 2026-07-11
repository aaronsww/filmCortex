"""Ingest all pages from TMDb Top Rated Movies.

Run weekly:
    uv run python -m pipeline.jobs.ingest_top_rated
"""

import argparse
import asyncio

from filmcortex.config.settings import settings
from pipeline.shared.job_context import ingestion_job, print_ingestion_stats
from pipeline.shared.limits import resolve_limit


async def run(*, limit: int, max_pages: int | None) -> None:
    async with ingestion_job() as context:
        stats = await context.ingestion_service.ingest_top_rated(
            max_pages=max_pages,
            max_movies=limit,
        )
    print_ingestion_stats(stats, label="Top rated")


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest TMDb top-rated movies")
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help=(
            "Maximum number of movies to ingest "
            f"(default: {settings.tmdb_top_rated_limit} from TMDB_TOP_RATED_LIMIT)"
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
            limit=resolve_limit(args.limit, settings.tmdb_top_rated_limit),
            max_pages=args.max_pages,
        )
    )


if __name__ == "__main__":
    main()
