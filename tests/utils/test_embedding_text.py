from filmcortex.utils.embedding_text import build_embedding_text


def _full_payload() -> dict:
    return {
        "title": "The Batman",
        "original_title": "The Batman",
        "release_date": "2022-03-01",
        "overview": "When a killer targets Gotham's elite, Batman investigates corruption.",
        "runtime": 176,
        "original_language": "en",
        "genres": [
            {"id": 80, "name": "Crime"},
            {"id": 9648, "name": "Mystery"},
            {"id": 53, "name": "Thriller"},
        ],
        "keywords": {
            "keywords": [
                {"id": 1, "name": "vigilante"},
                {"id": 2, "name": "serial killer"},
            ]
        },
        "credits": {
            "crew": [
                {"job": "Director", "name": "Matt Reeves"},
                {"job": "Writer", "name": "Peter Craig"},
            ],
            "cast": [
                {"name": "Robert Pattinson", "order": 0},
                {"name": "Zoe Kravitz", "order": 1},
                {"name": "Paul Dano", "order": 2},
                {"name": "Jeffrey Wright", "order": 3},
                {"name": "Colin Farrell", "order": 4},
                {"name": "Andy Serkis", "order": 5},
            ],
        },
    }


def test_builds_full_document() -> None:
    text = build_embedding_text(_full_payload())

    assert text.startswith("The Batman (2022)")
    assert "When a killer targets Gotham's elite" in text
    assert "Batman investigates corruption." in text
    assert "Genres: Crime, Mystery, Thriller" in text
    assert "Keywords: vigilante, serial killer" in text
    assert "Director: Matt Reeves" in text
    assert "Runtime: 176 minutes" in text
    assert "Language: English" in text


def test_cast_is_limited_and_ordered() -> None:
    text = build_embedding_text(_full_payload())

    assert "Cast: Robert Pattinson, Zoe Kravitz, Paul Dano, Jeffrey Wright, Colin Farrell" in text
    assert "Andy Serkis" not in text


def test_writer_is_excluded_from_director() -> None:
    text = build_embedding_text(_full_payload())

    assert "Peter Craig" not in text


def test_title_only_payload() -> None:
    text = build_embedding_text({"title": "Untitled"})

    assert text == "Untitled"


def test_missing_title_falls_back_to_original_title() -> None:
    text = build_embedding_text({"original_title": "Le Film"})

    assert text.startswith("Le Film")


def test_missing_title_falls_back_to_unknown() -> None:
    text = build_embedding_text({})

    assert text == "Unknown"


def test_omits_empty_sections() -> None:
    text = build_embedding_text(
        {
            "title": "Minimal",
            "release_date": "1999-01-01",
            "overview": "",
            "genres": [],
            "keywords": {"keywords": []},
            "credits": {"crew": [], "cast": []},
        }
    )

    assert text == "Minimal (1999)"


def test_unknown_language_code_is_passed_through() -> None:
    text = build_embedding_text({"title": "Film", "original_language": "xx"})

    assert "Language: xx" in text


def test_is_pure_and_does_not_mutate_input() -> None:
    payload = _full_payload()
    snapshot = str(payload)

    build_embedding_text(payload)

    assert str(payload) == snapshot
