"""Ingest movies from TMDb Discover with configurable or preset filters.

Run weekly sweeps:
    uv run python -m pipeline.jobs.ingest_discover --preset all
    uv run python -m pipeline.jobs.ingest_discover --year 1994 --vote-count-gte 500
"""

import argparse
import asyncio

from filmcortex.config.settings import settings
from filmcortex.integrations.tmdb.constants import DISCOVER_SWEEPS
from pipeline.shared.job_context import ingestion_job, print_ingestion_stats
from pipeline.shared.limits import resolve_limit


def _build_filters(args: argparse.Namespace) -> dict[str, str | int | float]:
    filters: dict[str, str | int | float] = {"sort_by": args.sort_by}
    if args.year is not None:
        filters["primary_release_year"] = args.year
    if args.genre is not None:
        filters["with_genres"] = args.genre
    if args.vote_count_gte is not None:
        filters["vote_count.gte"] = args.vote_count_gte
    if args.vote_average_gte is not None:
        filters["vote_average.gte"] = args.vote_average_gte
    return filters


async def run(
    *,
    filters: dict[str, str | int | float],
    limit: int,
    max_pages: int | None,
) -> None:
    async with ingestion_job() as context:
        stats = await context.ingestion_service.ingest_discover(
            filters=filters,
            max_pages=max_pages,
            max_movies=limit,
        )
    print_ingestion_stats(stats, label="Discover")


async def run_presets(*, limit: int, max_pages: int | None) -> None:
    total_stats = None
    remaining = limit
    async with ingestion_job() as context:
        for index, filters in enumerate(DISCOVER_SWEEPS, start=1):
            if remaining <= 0:
                break
            print(f"Discover sweep {index}/{len(DISCOVER_SWEEPS)}: {filters}")
            stats = await context.ingestion_service.ingest_discover(
                filters=filters,
                max_pages=max_pages,
                max_movies=remaining,
            )
            print_ingestion_stats(stats, label=f"Sweep {index}")
            remaining -= stats.fetched
            if total_stats is None:
                total_stats = stats
            else:
                total_stats.merge(stats)

    if total_stats is not None:
        print_ingestion_stats(total_stats, label="Discover total")


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest movies via TMDb Discover")
    parser.add_argument(
        "--preset",
        choices=["all"],
        default=None,
        help="Run the built-in discover sweep presets",
    )
    parser.add_argument("--year", type=int, default=None, help="primary_release_year filter")
    parser.add_argument("--genre", type=int, default=None, help="with_genres filter")
    parser.add_argument(
        "--vote-count-gte",
        type=int,
        default=500,
        help="Minimum vote count filter",
    )
    parser.add_argument("--vote-average-gte", type=float, default=None)
    parser.add_argument(
        "--sort-by",
        default="vote_average.desc",
        help="Discover sort_by parameter",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help=(
            "Maximum number of movies to ingest "
            f"(default: {settings.tmdb_discover_limit} from TMDB_DISCOVER_LIMIT; "
            "shared across sweeps when using --preset all)"
        ),
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=None,
        help="Optional page cap per sweep (in addition to --limit)",
    )
    args = parser.parse_args()
    limit = resolve_limit(args.limit, settings.tmdb_discover_limit)

    if args.preset == "all":
        asyncio.run(run_presets(limit=limit, max_pages=args.max_pages))
        return

    filters = _build_filters(args)
    asyncio.run(run(filters=filters, limit=limit, max_pages=args.max_pages))


if __name__ == "__main__":
    main()
