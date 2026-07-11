import gzip
import json
from datetime import date
from pathlib import Path

import pytest

from filmcortex.integrations.tmdb.exports import (
    diff_movie_ids,
    export_filename,
    export_url,
    parse_movie_ids,
)


def test_export_filename_uses_mm_dd_yyyy() -> None:
    assert export_filename(date(2025, 10, 25)) == "movie_ids_10_25_2025.json.gz"


def test_export_url() -> None:
    assert (
        export_url(date(2025, 10, 25))
        == "https://files.tmdb.org/p/exports/movie_ids_10_25_2025.json.gz"
    )


def test_parse_movie_ids_from_gzip(tmp_path: Path) -> None:
    export_path = tmp_path / "movie_ids_10_25_2025.json.gz"
    lines = [json.dumps({"id": 550}), json.dumps({"id": 551})]
    with gzip.open(export_path, "wt", encoding="utf-8") as handle:
        handle.write("\n".join(lines))

    assert parse_movie_ids(export_path) == [550, 551]


def test_diff_movie_ids() -> None:
    current = [1, 2, 3, 4]
    previous = [1, 2]
    assert diff_movie_ids(current, previous) == [3, 4]
