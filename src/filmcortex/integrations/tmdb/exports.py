import gzip
import json
from datetime import date
from pathlib import Path

import httpx

from filmcortex.integrations.tmdb.constants import TMDB_EXPORT_BASE_URL


def export_filename(for_date: date | None = None) -> str:
    export_date = for_date or date.today()
    return f"movie_ids_{export_date.month:02d}_{export_date.day:02d}_{export_date.year}.json.gz"


def export_url(for_date: date | None = None) -> str:
    return f"{TMDB_EXPORT_BASE_URL}/{export_filename(for_date)}"


async def download_daily_export(
    cache_dir: Path,
    *,
    for_date: date | None = None,
    client: httpx.AsyncClient | None = None,
) -> Path:
    """Download the daily movie ID export and return the local file path."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    filename = export_filename(for_date)
    destination = cache_dir / filename

    if destination.exists():
        return destination

    owns_client = client is None
    http_client = client or httpx.AsyncClient(timeout=120.0, follow_redirects=True)
    try:
        response = await http_client.get(export_url(for_date))
        response.raise_for_status()
        destination.write_bytes(response.content)
        return destination
    finally:
        if owns_client:
            await http_client.aclose()


def parse_movie_ids(export_path: Path) -> list[int]:
    """Parse newline-delimited JSON movie IDs from a daily export file."""
    opener = gzip.open if export_path.suffix == ".gz" else open
    ids: list[int] = []
    with opener(export_path, "rt", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            movie_id = record.get("id")
            if isinstance(movie_id, int):
                ids.append(movie_id)
    return ids


def diff_movie_ids(current_ids: list[int], previous_ids: list[int]) -> list[int]:
    """Return IDs present in current export but not in the previous one."""
    previous = set(previous_ids)
    return [movie_id for movie_id in current_ids if movie_id not in previous]


def find_previous_export(cache_dir: Path, current_path: Path) -> Path | None:
    """Find the most recent export file in cache_dir other than current_path."""
    exports = sorted(
        path
        for path in cache_dir.glob("movie_ids_*.json.gz")
        if path != current_path and path.is_file()
    )
    if not exports:
        return None
    return exports[-1]
