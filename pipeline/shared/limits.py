"""Resolve CLI overrides against configured pipeline batch limits."""


def resolve_limit(cli_value: int | None, configured_default: int) -> int:
    return cli_value if cli_value is not None else configured_default
