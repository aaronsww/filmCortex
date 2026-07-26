import uuid

import pytest

from filmcortex.utils.cursor import (
    CursorError,
    decode_movie_list_cursor,
    encode_movie_list_cursor,
)


def test_movie_list_cursor_roundtrip() -> None:
    metadata_id = uuid.uuid4()
    cursor = encode_movie_list_cursor(title="Fight Club", metadata_id=metadata_id)
    title, decoded_id = decode_movie_list_cursor(cursor)
    assert title == "Fight Club"
    assert decoded_id == metadata_id


@pytest.mark.parametrize("cursor", ["", "not-valid", "eyJ0IjoiIn0"])  # missing m
def test_invalid_movie_list_cursor_raises(cursor: str) -> None:
    with pytest.raises(CursorError):
        decode_movie_list_cursor(cursor)
