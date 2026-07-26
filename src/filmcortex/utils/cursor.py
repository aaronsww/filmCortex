import base64
import binascii
import json
import uuid
from typing import Any


class CursorError(ValueError):
    """Raised when a pagination cursor cannot be decoded or is malformed."""


def encode_cursor(payload: dict[str, Any]) -> str:
    raw = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def decode_cursor(cursor: str) -> dict[str, Any]:
    if not cursor:
        raise CursorError("Cursor must not be empty")

    padding = "=" * (-len(cursor) % 4)
    try:
        raw = base64.urlsafe_b64decode(f"{cursor}{padding}".encode("ascii"))
        payload = json.loads(raw.decode("utf-8"))
    except (binascii.Error, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CursorError("Invalid cursor") from exc

    if not isinstance(payload, dict):
        raise CursorError("Invalid cursor")
    return payload


def encode_movie_list_cursor(*, title: str, metadata_id: uuid.UUID) -> str:
    return encode_cursor({"t": title, "m": str(metadata_id)})


def decode_movie_list_cursor(cursor: str) -> tuple[str, uuid.UUID]:
    payload = decode_cursor(cursor)
    title = payload.get("t")
    metadata_id = payload.get("m")
    if not isinstance(title, str) or not isinstance(metadata_id, str):
        raise CursorError("Invalid cursor")
    try:
        return title, uuid.UUID(metadata_id)
    except ValueError as exc:
        raise CursorError("Invalid cursor") from exc
