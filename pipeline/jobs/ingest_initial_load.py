"""Initial bulk ingestion: daily export seed + top rated + discover sweeps.

Run once for the initial catalog load:
    uv run python -m pipeline.jobs.ingest_initial_load

Then run generate_embeddings afterward:
    uv run python -m pipeline.jobs.generate_embeddings
"""

import argparse
import asyncio

from filmcortex.config.settings import settings
from filmcortex.integrations.tmdb.constants import DISCOVER_SWEEPS
from pipeline.shared.job_context import ingestion_job, print_ingestion_stats
from pipeline.shared.limits import resolve_limit


async def run(
    *,
    export_limit: int,
    top_rated_limit: int,
    discover_limit: int,
) -> None:
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
        top_rated_stats = await context.ingestion_service.ingest_top_rated(
            max_movies=top_rated_limit,
        )
        print_ingestion_stats(top_rated_stats, label="Top rated")

        print(f"Step 3/3: Run discover sweeps (budget: {discover_limit} movies)")
        discover_total = None
        remaining = discover_limit
        for index, filters in enumerate(DISCOVER_SWEEPS, start=1):
            if remaining <= 0:
                break
            print(f"Discover sweep {index}/{len(DISCOVER_SWEEPS)}: {filters}")
            stats = await context.ingestion_service.ingest_discover(
                filters=filters,
                max_movies=remaining,
            )
            print_ingestion_stats(stats, label=f"Sweep {index}")
            remaining -= stats.fetched
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
        help=(
            "Maximum export IDs to ingest "
            f"(default: {settings.tmdb_initial_load_limit} from TMDB_INITIAL_LOAD_LIMIT)"
        ),
    )
    parser.add_argument(
        "--top-rated-limit",
        type=int,
        default=None,
        help=(
            "Maximum top-rated movies to ingest "
            f"(default: {settings.tmdb_top_rated_limit} from TMDB_TOP_RATED_LIMIT)"
        ),
    )
    parser.add_argument(
        "--discover-limit",
        type=int,
        default=None,
        help=(
            "Maximum discover movies to ingest across all sweeps "
            f"(default: {settings.tmdb_discover_limit} from TMDB_DISCOVER_LIMIT)"
        ),
    )
    args = parser.parse_args()
    asyncio.run(
        run(
            export_limit=resolve_limit(args.export_limit, settings.tmdb_initial_load_limit),
            top_rated_limit=resolve_limit(args.top_rated_limit, settings.tmdb_top_rated_limit),
            discover_limit=resolve_limit(args.discover_limit, settings.tmdb_discover_limit),
        )
    )


if __name__ == "__main__":
    main()
