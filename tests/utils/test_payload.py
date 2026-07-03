from filmcortex.utils.payload import payload_fingerprint


def test_payload_fingerprint_is_stable() -> None:
    payload = {"id": 1, "title": "Example"}
    assert payload_fingerprint(payload) == payload_fingerprint({"title": "Example", "id": 1})


def test_payload_fingerprint_changes_when_payload_changes() -> None:
    first = payload_fingerprint({"id": 1, "title": "A"})
    second = payload_fingerprint({"id": 1, "title": "B"})
    assert first != second
