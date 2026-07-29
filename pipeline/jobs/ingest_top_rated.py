"""Ingest TMDb Top Rated Movies with optional multi-day page resume.

Run daily (resumes from saved cursor, skips IDs already in DB):
    uv run python -m pipeline.jobs.ingest_top_rated
"""

import argparse
import asyncio
from pathlib import Path

from filmcortex.config.settings import settings
from pipeline.shared.job_context import ingestion_job, print_ingestion_stats
from pipeline.shared.limits import resolve_limit
from pipeline.shared.page_cursor import load_next_page, save_next_page


async def run(
    *,
    limit: int,
    max_pages: int | None,
    resume: bool,
    skip_existing: bool,
) -> None:
    cursor_path = Path(settings.tmdb_top_rated_cursor_path)
    start_page = load_next_page(cursor_path) if resume else 1

    async with ingestion_job() as context:
        stats = await context.ingestion_service.ingest_top_rated(
            max_pages=max_pages,
            max_movies=limit,
            start_page=start_page,
            skip_existing=skip_existing,
            wrap=resume,
        )

    if resume:
        save_next_page(cursor_path, stats.next_page)

    print(f"Top rated: Started at page {start_page}")
    print(f"Top rated: Pages scanned {stats.pages_scanned}")
    print(f"Top rated: Next page {stats.next_page}")
    print_ingestion_stats(stats, label="Top rated")


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest TMDb top-rated movies")
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help=(
            "Maximum number of new movie detail fetches "
            f"(default: {settings.tmdb_top_rated_limit} from TMDB_TOP_RATED_LIMIT)"
        ),
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=None,
        help="Optional page-scan cap for this run (in addition to --limit)",
    )
    parser.add_argument(
        "--no-resume",
        action="store_true",
        help="Start at page 1 and do not read/write the resume cursor",
    )
    parser.add_argument(
        "--refresh-existing",
        action="store_true",
        help="Detail-fetch movies already in the database (default: skip them)",
    )
    args = parser.parse_args()
    asyncio.run(
        run(
            limit=resolve_limit(args.limit, settings.tmdb_top_rated_limit),
            max_pages=args.max_pages,
            resume=not args.no_resume,
            skip_existing=not args.refresh_existing,
        )
    )


if __name__ == "__main__":
    main()
