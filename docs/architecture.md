# FilmCortex Architecture

A concise, up-to-date reference for how FilmCortex is **currently** designed. For the reasoning behind decisions, see the [devlog](devlog/README.md). For what is planned next, see the [roadmap](roadmap.md).

## Overview

FilmCortex is an AI movie intelligence engine. It ingests external movie metadata, stores it locally, and (once the AI layer lands) will serve personalized recommendations, semantic search, and collections. Media requesting/downloading is delegated to the existing ARR ecosystem and is out of scope for this service.

## Pipeline

```
TMDb
  ↓  (ingestion — the only component allowed to call TMDb)
PostgreSQL  (canonical local state)
  ↓  (offline jobs read local state only)
Offline Jobs  (embeddings, clustering, recommendations — planned)
  ↓
API  (serves precomputed data only)
```

Core rule: **ingestion is the only component that talks to TMDb.** Every downstream job reads exclusively from PostgreSQL. Stored payloads must contain everything downstream jobs need, which keeps the system deterministic, reproducible, and fully offline after ingestion.

## Components

### API

- FastAPI application (`src/filmcortex/main.py`), served by Uvicorn.
- Routes are mounted under `/api/v1`:
  - `GET /api/v1/health` — liveness check.
  - `GET /api/v1/movies` — lists ingested movies (joins `movies` with active `external_metadata`).
- Interactive docs at `http://localhost:8000/docs`.
- The API is **read-only over precomputed data**. It performs no TMDb calls and no model inference at request time.
- Layering: `api/` (routers, dependency wiring) → `services/` (application logic) → `repositories/` (data access) → `models/` (SQLAlchemy ORM).

### Database

- PostgreSQL 16 using the `pgvector/pgvector:pg16` image.
- Accessed asynchronously via SQLAlchemy 2.x + `asyncpg`.
- Schema is managed by Alembic (`alembic/versions/`):
  - `001_initial_movies_and_external_metadata` — creates the `movies` and `external_metadata` tables.
  - `002_enable_pgvector` — runs `CREATE EXTENSION IF NOT EXISTS vector`.
- Current tables:
  - **`movies`** — canonical, provider-agnostic record: `id` (UUID), `canonical_title`, `media_type`, `first_indexed_at`.
  - **`external_metadata`** — raw provider payloads: `movie_id` (FK), `provider`, `provider_id`, `payload` (JSONB), `payload_version`, `fetched_at`, `is_active`. Unique on `(provider, provider_id)`.

### Ingestion

- Implemented as an offline job: `pipeline/jobs/ingest_tmdb.py`.
- Fetches from TMDb via `TMDbClient` and upserts through `TMDbIngestionService`:
  - New movie → create `movies` row + `external_metadata` row.
  - Existing movie, unchanged payload → skip (payload fingerprint comparison).
  - Existing movie, changed payload → update title and payload.
- Requires `TMDB_API_KEY`. The full TMDb payload is persisted so downstream jobs never need to re-contact TMDb.

### Embedding pipeline (planned, not yet implemented)

- Designed to run offline: read local movie state, generate embeddings, and store them in PostgreSQL via pgvector.
- A `movie_embeddings` table is planned to hold `embedded_text`, `model_name`, and `model_revision` for reproducibility.
- The API will read precomputed embeddings only; no inference at request time.
- pgvector is already enabled (migration `002`) so this layer can be added without further extension setup. Tracked in the [roadmap](roadmap.md).

## Docker services

Defined in `docker-compose.yml`:

- **`db`** — `pgvector/pgvector:pg16`. Host port `5433` → container `5432`. Data persisted in the `postgres_data` volume. Has a `pg_isready` healthcheck.
- **`api`** — built from the `Dockerfile` (Python 3.12, dependencies via `uv`). Waits for `db` to be healthy, then runs Uvicorn on port `8000`. Inside the Docker network it reaches the database at host `db`; external tools (e.g. DBeaver) connect at `localhost:5433`.

## Data flow

1. **Ingest** — an operator runs the TMDb ingestion job; movie metadata is fetched and persisted to PostgreSQL.
2. **Process (planned)** — offline jobs read local state to produce embeddings, clusters, and recommendations, writing results back to PostgreSQL.
3. **Serve** — the API exposes precomputed data to clients over `/api/v1`.

## Configuration

- Settings are loaded from environment / `.env` via `pydantic-settings` (`src/filmcortex/config/settings.py`).
- Key variables: `DATABASE_URL`, `TMDB_API_KEY`, `APP_ENV`, `APP_DEBUG`, `API_HOST`, `API_PORT`. See `.env.example` for the full list.
