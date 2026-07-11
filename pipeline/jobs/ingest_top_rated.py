"""Ingest all pages from TMDb Top Rated Movies.

Run weekly/monthly:
    uv run python -m pipeline.jobs.ingest_top_rated
"""

import argparse
import asyncio

from pipeline.shared.job_context import ingestion_job, print_ingestion_stats


async def run(*, max_pages: int | None) -> None:
    async with ingestion_job() as context:
        stats = await context.ingestion_service.ingest_top_rated(max_pages=max_pages)
    print_ingestion_stats(stats, label="Top rated")


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest TMDb top-rated movies")
    parser.add_argument(
        "--max-pages",
        type=int,
        default=None,
        help="Limit the number of pages to ingest",
    )
    args = parser.parse_args()
    asyncio.run(run(max_pages=args.max_pages))


if __name__ == "__main__":
    main()
