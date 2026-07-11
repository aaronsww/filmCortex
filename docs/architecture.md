# FilmCortex Architecture

A concise, up-to-date reference for how FilmCortex is **currently** designed. For the reasoning behind decisions, see the [devlog](devlog/README.md). For what is planned next, see the [roadmap](roadmap.md).

_Last updated: 2026-07-11_

## Overview

FilmCortex is an AI movie intelligence engine. It ingests external movie metadata, stores it locally, precomputes embeddings offline, and serves a read-only API for listing movies and finding similar films. Media requesting/downloading is delegated to the existing ARR ecosystem and is out of scope for this service.

## Pipeline

```
TMDb (API + daily ID exports)
  ↓  (ingestion jobs — the only components allowed to call TMDb)
PostgreSQL  (canonical local state: movies, external_metadata)
  ↓  (offline jobs read local state only)
Offline Jobs  (generate_embeddings)
  ↓
API  (serves precomputed data only: list + similar)
```

Core rule: **ingestion is the only component that talks to TMDb.** Every downstream job reads exclusively from PostgreSQL. Stored payloads must contain everything downstream jobs need, which keeps the system deterministic, reproducible, and fully offline after ingestion.

Jobs are **scheduler-agnostic**: operators run them manually or wire them into cron, systemd timers, Kubernetes CronJobs, etc. Application code does not include a built-in scheduler.

## Components

### API

- FastAPI application (`src/filmcortex/main.py`), served by Uvicorn.
- Routes are mounted under `/api/v1`:
  - `GET /api/v1/health` — liveness check.
  - `GET /api/v1/movies` — lists ingested movies (joins `movies` with active `external_metadata`).
  - `GET /api/v1/movies/{movie_id}/similar` — nearest neighbors via precomputed embeddings (optional similarity scores).
- Interactive docs at `http://localhost:8000/docs`.
- The API is **read-only over precomputed data**. It performs no TMDb calls and no model inference at request time.
- Layering: `api/` (routers, dependency wiring) → `services/` (application logic) → `repositories/` (data access) → `models/` (SQLAlchemy ORM).

### Database

- PostgreSQL 16 using the `pgvector/pgvector:pg16` image.
- Accessed asynchronously via SQLAlchemy 2.x + `asyncpg`.
- Schema is managed by Alembic (`alembic/versions/`):
  - `001_initial_movies_and_external_metadata` — creates the `movies` and `external_metadata` tables.
  - `002_enable_pgvector` — runs `CREATE EXTENSION IF NOT EXISTS vector`.
  - `003_movie_embeddings` — creates the `movie_embeddings` table.
- Current tables:
  - **`movies`** — canonical, provider-agnostic record: `id` (UUID), `canonical_title`, `media_type`, `first_indexed_at`.
  - **`external_metadata`** — raw provider payloads: `movie_id` (FK), `provider`, `provider_id`, `payload` (JSONB), `payload_version`, `fetched_at`, `is_active`. Unique on `(provider, provider_id)` (TMDb ID dedup).
  - **`movie_embeddings`** — one vector per movie: `embedding` (VECTOR 384), `embedded_text`, `model_name`, `model_revision`, `generated_at`.

### Ingestion

- Offline jobs under `pipeline/jobs/`, backed by `TMDbClient` + `TMDbIngestionService`.
- Sources:
  - Daily ID export (`files.tmdb.org`) → ID list, then per-ID details.
  - List endpoints (`top_rated`, `discover`, `trending`, `popular`, curated lists) → IDs, then per-ID details.
- Per movie: `GET /movie/{id}` with `append_to_response` (credits, keywords, external_ids, images, videos, alternative_titles, translations). Full JSON stored in `external_metadata.payload`.
- Upsert rules:
  - New movie → create `movies` + `external_metadata`.
  - Existing, unchanged fingerprint → skip.
  - Existing, changed fingerprint → update title and payload.
- Rate limiting (~30 req/s by default) and 429 retries live in the TMDb client.
- Homelab-safe **batch limits** are configured in settings / `.env` (e.g. `TMDB_INITIAL_LOAD_LIMIT`, `TMDB_DAILY_EXPORT_LIMIT`); CLI `--limit` flags override them. See the [README](../README.md) for the recommended schedule.

### Embedding pipeline

- Offline job: `pipeline/jobs/generate_embeddings.py`.
- Reads local `external_metadata` payloads; builds text via `utils/embedding_text.py`; encodes with `sentence-transformers` (`BAAI/bge-small-en-v1.5` by default).
- Writes to `movie_embeddings`. Processes at most `EMBEDDING_BATCH_SIZE` movies per run (CLI `--limit` overrides).
- Idempotent for missing embeddings: only movies without a vector are processed. Re-embedding on payload change is not implemented yet.
- Requires `uv sync --extra pipeline`. The API container does not load the model.

## Docker services

Defined in `docker-compose.yml`:

- **`db`** — `pgvector/pgvector:pg16`. Host port `5433` → container `5432`. Data persisted in the `postgres_data` volume. Has a `pg_isready` healthcheck.
- **`api`** — built from the `Dockerfile` (Python 3.12, dependencies via `uv`). Waits for `db` to be healthy, then runs Uvicorn on port `8000`. Inside the Docker network it reaches the database at host `db`; external tools (e.g. DBeaver) connect at `localhost:5433`.

Migrations are run manually (`uv run alembic upgrade head`). An entrypoint script exists but is not wired into the API image yet.

## Data flow

1. **Ingest** — operator (or external scheduler) runs TMDb ingestion jobs; metadata is persisted to PostgreSQL.
2. **Embed** — `generate_embeddings` reads local payloads and writes vectors.
3. **Serve** — the API exposes listing and similarity over precomputed data on `/api/v1`.

## Configuration

- Settings are loaded from environment / `.env` via `pydantic-settings` (`src/filmcortex/config/settings.py`).
- Key variables: `DATABASE_URL`, `TMDB_API_KEY`, pipeline batch limits (`TMDB_*_LIMIT`, `EMBEDDING_BATCH_SIZE`), embedding model settings, `APP_ENV`, `APP_DEBUG`, `API_HOST`, `API_PORT`. See `.env.example` for the full list.
