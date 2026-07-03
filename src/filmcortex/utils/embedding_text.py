"""Build the canonical text document that gets embedded for each movie.

This module is intentionally pure: no database access, no network calls, and no
model loading. It takes a TMDb payload and returns a single natural-language
document. Keeping it side-effect free makes it trivial to unit test, iterate on
the document format, regenerate embeddings deterministically, and compare
different document strategies later.
"""

MAX_CAST = 5

_LANGUAGE_NAMES = {
    "en": "English",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "it": "Italian",
    "pt": "Portuguese",
    "ru": "Russian",
    "ja": "Japanese",
    "ko": "Korean",
    "zh": "Chinese",
    "hi": "Hindi",
    "ar": "Arabic",
    "nl": "Dutch",
    "sv": "Swedish",
    "da": "Danish",
    "no": "Norwegian",
    "fi": "Finnish",
    "pl": "Polish",
    "tr": "Turkish",
    "th": "Thai",
}


def _title(payload: dict) -> str:
    return payload.get("title") or payload.get("original_title") or "Unknown"


def _year(payload: dict) -> str | None:
    release_date = payload.get("release_date") or ""
    year = release_date[:4]
    return year or None


def _genres(payload: dict) -> str | None:
    names = [g.get("name") for g in payload.get("genres") or [] if g.get("name")]
    return ", ".join(names) or None


def _keywords(payload: dict) -> str | None:
    keywords = (payload.get("keywords") or {}).get("keywords") or []
    names = [k.get("name") for k in keywords if k.get("name")]
    return ", ".join(names) or None


def _directors(payload: dict) -> str | None:
    crew = (payload.get("credits") or {}).get("crew") or []
    names = [c.get("name") for c in crew if c.get("job") == "Director" and c.get("name")]
    return ", ".join(names) or None


def _cast(payload: dict) -> str | None:
    cast = (payload.get("credits") or {}).get("cast") or []
    ordered = sorted(cast, key=lambda c: c.get("order", 10_000))
    names = [c.get("name") for c in ordered if c.get("name")][:MAX_CAST]
    return ", ".join(names) or None


def _runtime(payload: dict) -> str | None:
    runtime = payload.get("runtime")
    if not runtime:
        return None
    return f"{runtime} minutes"


def _language(payload: dict) -> str | None:
    code = payload.get("original_language")
    if not code:
        return None
    return _LANGUAGE_NAMES.get(code, code)


def build_embedding_text(payload: dict) -> str:
    title = _title(payload)
    year = _year(payload)
    header = f"{title} ({year})" if year else title

    sections: list[str] = [header]

    overview = (payload.get("overview") or "").strip()
    if overview:
        sections.append(overview)

    fields = [
        ("Genres", _genres(payload)),
        ("Keywords", _keywords(payload)),
        ("Director", _directors(payload)),
        ("Cast", _cast(payload)),
        ("Runtime", _runtime(payload)),
        ("Language", _language(payload)),
    ]
    metadata_lines = [f"{label}: {value}" for label, value in fields if value]
    if metadata_lines:
        sections.append("\n".join(metadata_lines))

    return "\n\n".join(sections)
