"""Ingest movies from TMDb's popular endpoint.

Example:
    uv run python -m pipeline.jobs.ingest_tmdb --page 1
"""

import argparse
import asyncio

from pipeline.shared.job_context import ingestion_job, print_ingestion_stats


async def run(*, page: int) -> None:
    async with ingestion_job() as context:
        stats = await context.ingestion_service.ingest_popular_page(page=page)
    print_ingestion_stats(stats, label="Popular")


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest TMDb popular movies")
    parser.add_argument("--page", type=int, default=1, help="Popular results page")
    args = parser.parse_args()
    asyncio.run(run(page=args.page))


if __name__ == "__main__":
    main()
