from pipeline.shared.limits import resolve_limit


def test_resolve_limit_uses_cli_value_when_provided() -> None:
    assert resolve_limit(25, 100) == 25


def test_resolve_limit_uses_configured_default_when_cli_is_none() -> None:
    assert resolve_limit(None, 100) == 100
