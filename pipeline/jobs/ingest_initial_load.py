"""Initial bulk ingestion: daily export seed + top rated + discover sweeps.

Run once for the initial catalog load:
    uv run python -m pipeline.jobs.ingest_initial_load

Then run generate_embeddings afterward:
    uv run python -m pipeline.jobs.generate_embeddings
"""

import argparse
import asyncio

from filmcortex.integrations.tmdb.constants import DISCOVER_SWEEPS
from pipeline.shared.job_context import ingestion_job, print_ingestion_stats


async def run(*, export_limit: int | None, discover_max_pages: int | None) -> None:
    async with ingestion_job() as context:
        print("Step 1/3: Download daily export and ingest missing IDs")
        export_stats = await context.ingestion_service.ingest_daily_export(
            context.export_cache_dir,
            ingest_all=True,
            limit=export_limit,
        )
        print(f"Export IDs selected: {export_stats.new_ids}")
        print_ingestion_stats(export_stats.ingestion, label="Export")

        print("Step 2/3: Ingest top-rated movies")
        top_rated_stats = await context.ingestion_service.ingest_top_rated()
        print_ingestion_stats(top_rated_stats, label="Top rated")

        print(f"Step 3/3: Run {len(DISCOVER_SWEEPS)} discover sweeps")
        discover_total = None
        for index, filters in enumerate(DISCOVER_SWEEPS, start=1):
            print(f"Discover sweep {index}/{len(DISCOVER_SWEEPS)}: {filters}")
            stats = await context.ingestion_service.ingest_discover(
                filters=filters,
                max_pages=discover_max_pages,
            )
            print_ingestion_stats(stats, label=f"Sweep {index}")
            if discover_total is None:
                discover_total = stats
            else:
                discover_total.merge(stats)

        if discover_total is not None:
            print_ingestion_stats(discover_total, label="Discover total")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the initial TMDb bulk ingestion")
    parser.add_argument(
        "--export-limit",
        type=int,
        default=None,
        help="Limit export IDs ingested during initial load",
    )
    parser.add_argument(
        "--discover-max-pages",
        type=int,
        default=None,
        help="Limit pages per discover sweep",
    )
    args = parser.parse_args()
    asyncio.run(
        run(
            export_limit=args.export_limit,
            discover_max_pages=args.discover_max_pages,
        )
    )


if __name__ == "__main__":
    main()
