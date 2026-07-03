# FilmCortex

AI-powered movie intelligence engine for personalized Jellyfin recommendations and collections.

## Quick start

```bash
cp .env.example .env
uv sync --all-extras
docker compose up -d
```

API: http://localhost:8000/docs

## Database migrations

Migrations run automatically when the API container starts (`alembic upgrade head` in the entrypoint).

To run them manually against the Docker database:

```bash
docker compose up -d db
uv run alembic upgrade head
```

Verify pgvector is enabled:

```bash
docker compose exec db psql -U filmcortex -d filmcortex -c \
  "SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';"
```

The database image is `pgvector/pgvector:pg16`, which ships the vector extension. Migration `002_enable_pgvector` runs `CREATE EXTENSION IF NOT EXISTS vector` and is safe to re-run.

Optional integration test (requires a running database and `DATABASE_URL` in the environment):

```bash
uv run pytest tests/migrations/test_002_enable_pgvector.py -m integration
```

## Offline pipeline

Heavy AI work runs offline in `pipeline/`; the API serves only precomputed data. Jobs read from PostgreSQL and (except ingestion) never call external APIs.

Ingest movies from TMDb (requires `TMDB_API_KEY`):

```bash
uv run python -m pipeline.jobs.ingest_tmdb
```

Generate embeddings for movies that don't have one yet (requires the `pipeline` extra):

```bash
uv sync --extra pipeline
uv run python -m pipeline.jobs.generate_embeddings
```

The embedding job is idempotent: it only processes movies without an embedding, so it is safe to re-run.

## Project layout

See repository structure in the codebase. Heavy AI work runs in `pipeline/`; the API in `src/filmcortex/` serves precomputed data only.

Pipeline architecture and future design notes: [docs/architecture.md](docs/architecture.md).
