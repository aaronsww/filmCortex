from pathlib import Path

from pipeline.shared.page_cursor import load_next_page, save_next_page


def test_page_cursor_defaults_when_missing(tmp_path: Path) -> None:
    assert load_next_page(tmp_path / "missing") == 1
    assert load_next_page(tmp_path / "missing", default=7) == 7


def test_page_cursor_roundtrip(tmp_path: Path) -> None:
    path = tmp_path / "top_rated_next_page"
    save_next_page(path, 42)
    assert load_next_page(path) == 42


def test_page_cursor_rejects_invalid_and_non_positive(tmp_path: Path) -> None:
    path = tmp_path / "cursor"
    path.write_text("nope\n", encoding="utf-8")
    assert load_next_page(path) == 1
    save_next_page(path, 0)
    assert load_next_page(path) == 1
