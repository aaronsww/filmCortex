import importlib.util
import os
from pathlib import Path

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

MIGRATION_PATH = (
    Path(__file__).resolve().parents[2] / "alembic" / "versions" / "002_enable_pgvector.py"
)


def _load_migration():
    spec = importlib.util.spec_from_file_location("migration_002", MIGRATION_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_pgvector_migration_revision_chain() -> None:
    migration = _load_migration()

    assert migration.revision == "002"
    assert migration.down_revision == "001"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_pgvector_extension_is_available() -> None:
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        pytest.skip("DATABASE_URL is not set")

    engine = create_async_engine(database_url)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    try:
        async with session_factory() as session:
            result = await session.execute(
                text("SELECT 1 FROM pg_extension WHERE extname = 'vector'")
            )
            assert result.scalar_one() == 1
    finally:
        await engine.dispose()
