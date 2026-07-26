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

Migrations are run manually against the Docker database:

```bash
docker compose up -d db
uv run alembic upgrade head
```

> Note: `scripts/docker-entrypoint.sh` can run `alembic upgrade head`, but it is not currently wired into the API Dockerfile/compose flow.
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

Every job has a safe default batch limit (configurable in `.env`) so a homelab deployment does not accidentally ingest the entire TMDb catalog. CLI `--limit` flags always override configuration.

| Setting | Default | Used by |
|---------|---------|---------|
| `TMDB_INITIAL_LOAD_LIMIT` | 500 | `ingest_initial_load` (export step) |
| `TMDB_DAILY_EXPORT_LIMIT` | 100 | `ingest_daily_export` |
| `TMDB_TRENDING_LIMIT` | 40 | `ingest_trending` |
| `TMDB_TOP_RATED_LIMIT` | 100 | `ingest_top_rated`, `ingest_initial_load` |
| `TMDB_DISCOVER_LIMIT` | 100 | `ingest_discover`, `ingest_initial_load` |
| `EMBEDDING_BATCH_SIZE` | 100 | `generate_embeddings` |

FilmCortex is scheduler-agnostic: wire these commands into cron, systemd timers, Kubernetes CronJobs, GitHub Actions, or any other scheduler without changing application code.

Homelab systemd timers (daily/weekly) live under [`deploy/systemd/`](deploy/systemd/README.md).

### Recommended homelab schedule

**Initial setup (manual, once):**

```bash
uv run python -m pipeline.jobs.ingest_initial_load
uv run python -m pipeline.jobs.generate_embeddings
```

**Daily:**

```bash
uv run python -m pipeline.jobs.ingest_daily_export
uv run python -m pipeline.jobs.generate_embeddings
uv run python -m pipeline.jobs.ingest_trending
```

**Weekly:**

```bash
uv run python -m pipeline.jobs.ingest_top_rated
uv run python -m pipeline.jobs.ingest_discover --preset all
uv run python -m pipeline.jobs.generate_embeddings
```

**Manual (as needed):**

```bash
uv run python -m pipeline.jobs.ingest_list --list-id 634
uv run python -m pipeline.jobs.ingest_tmdb --page 1
```

### Running jobs

Ingest movies from TMDb (requires `TMDB_API_KEY`):

```bash
uv run python -m pipeline.jobs.ingest_tmdb
uv run python -m pipeline.jobs.ingest_initial_load
uv run python -m pipeline.jobs.ingest_daily_export
```

Generate embeddings for movies that don't have one yet (requires the `pipeline` extra):

```bash
uv sync --extra pipeline
uv run python -m pipeline.jobs.generate_embeddings
```

Override a default batch size for a single run:

```bash
uv run python -m pipeline.jobs.ingest_daily_export --limit 50
uv run python -m pipeline.jobs.generate_embeddings --limit 25
```

The embedding job is idempotent: it only processes movies without an embedding, so it is safe to re-run daily until the backlog clears.

## Project layout

See repository structure in the codebase. Heavy AI work runs in `pipeline/`; the API in `src/filmcortex/` serves precomputed data only.

Pipeline architecture and future design notes: [docs/architecture.md](docs/architecture.md).
