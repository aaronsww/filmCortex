"""Download the daily TMDb movie ID export and ingest new IDs.

Run daily (AM UTC):
    uv run python -m pipeline.jobs.ingest_daily_export

For initial seeding of all missing IDs from the export:
    uv run python -m pipeline.jobs.ingest_daily_export --ingest-all --limit 1000
"""

import argparse
import asyncio

from filmcortex.config.settings import settings
from pipeline.shared.job_context import ingestion_job, print_ingestion_stats
from pipeline.shared.limits import resolve_limit


async def run(*, ingest_all: bool, limit: int) -> None:
    async with ingestion_job() as context:
        export_stats = await context.ingestion_service.ingest_daily_export(
            context.export_cache_dir,
            ingest_all=ingest_all,
            limit=limit,
        )

    if export_stats.export_path:
        print(f"Export file: {export_stats.export_path}")
    print(f"Total IDs in export: {export_stats.total_ids}")
    print(f"IDs selected for ingestion: {export_stats.new_ids}")
    print_ingestion_stats(export_stats.ingestion)


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest new movie IDs from TMDb daily export")
    parser.add_argument(
        "--ingest-all",
        action="store_true",
        help="Ingest all export IDs not already in the database (initial backfill)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help=(
            "Maximum number of IDs to ingest in this run "
            f"(default: {settings.tmdb_daily_export_limit} from TMDB_DAILY_EXPORT_LIMIT)"
        ),
    )
    args = parser.parse_args()
    asyncio.run(
        run(
            ingest_all=args.ingest_all,
            limit=resolve_limit(args.limit, settings.tmdb_daily_export_limit),
        )
    )


if __name__ == "__main__":
    main()
