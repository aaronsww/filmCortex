"""Ingest movies from a public TMDb list (e.g. curated top-100 lists).

Example:
    uv run python -m pipeline.jobs.ingest_list --list-id 634
"""

import argparse
import asyncio

from pipeline.shared.job_context import ingestion_job, print_ingestion_stats


async def run(*, list_id: int) -> None:
    async with ingestion_job() as context:
        stats = await context.ingestion_service.ingest_list(list_id)
    print_ingestion_stats(stats, label=f"List {list_id}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest movies from a TMDb public list")
    parser.add_argument("--list-id", type=int, required=True, help="TMDb list ID")
    args = parser.parse_args()
    asyncio.run(run(list_id=args.list_id))


if __name__ == "__main__":
    main()
