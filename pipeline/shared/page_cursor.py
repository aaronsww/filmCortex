"""Persist resume page for multi-day TMDb list crawls."""

from __future__ import annotations

from pathlib import Path


def load_next_page(path: Path, *, default: int = 1) -> int:
    if not path.is_file():
        return default
    raw = path.read_text(encoding="utf-8").strip()
    if not raw:
        return default
    try:
        page = int(raw)
    except ValueError:
        return default
    return page if page >= 1 else default


def save_next_page(path: Path, page: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"{max(1, page)}\n", encoding="utf-8")
