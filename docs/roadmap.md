# FilmCortex Roadmap

A living roadmap. It records what is done, what is in progress, and where the project is heading. Update it as milestones move. For the current system design see [architecture.md](architecture.md); for the reasoning behind pivots see the [devlog](devlog/README.md).

_Last updated: 2026-07-03_

## Completed

- **Project foundation** — repository scaffolding, `uv`-managed dependencies, Ruff, pytest.
- **Service skeleton** — FastAPI app with `/api/v1` routing and a health endpoint.
- **Database foundation** — PostgreSQL 16 via `pgvector/pgvector:pg16`, async SQLAlchemy + asyncpg, Alembic migrations.
- **Core schema** — `movies` and `external_metadata` tables (migration `001`).
- **pgvector enabled** — `CREATE EXTENSION vector` (migration `002`).
- **TMDb ingestion** — offline job that fetches movie metadata and upserts it with payload-fingerprint change detection; ingestion is the sole component that contacts TMDb.
- **Read API** — `GET /api/v1/movies` serving ingested movies.
- **Containerization** — `db` and `api` services in `docker-compose.yml`.

## Current milestone

**Embedding pipeline.**

- Add a `movie_embeddings` table (`embedded_text`, `model_name`, `model_revision`) via a new migration.
- Build an offline job that reads local movie state and generates embeddings stored with pgvector.
- Keep the API read-only over precomputed embeddings (no request-time inference).

## Upcoming milestones

- **Semantic search** — query movies by natural-language descriptions against stored embeddings.
- **Recommendation generation** — offline job producing personalized recommendations from embeddings and user taste signals.
- **User taste modeling** — represent a user's preferences at a semantic level (beyond recent-history heuristics).
- **Collections** — automatically generated, meaningful movie collections (e.g. clustering).
- **ARR integration** — hand off "request/download this" actions to the existing ARR stack rather than reimplementing them.

## Future ideas

- **Canonical Movie Document** — a stable, provider-agnostic representation used as the embedding source instead of raw TMDb text.
- **Metadata refresh job** — a future `refresh_tmdb_metadata.py` to refresh stored payloads and allow embeddings to be regenerated. Would join ingestion as the only other TMDb-facing component.
- **Additional providers** — support external metadata sources beyond TMDb (the `external_metadata` schema is already provider-agnostic).
- **Natural-language discovery UX** — conversational interface for taste-driven discovery.

## Technical debt / known gaps

- Embedding, recommendation, clustering, and search jobs are designed but not yet implemented.
- The API surface is minimal (health + movie listing); no pagination, filtering, or auth yet.
- Ingestion currently covers a single "popular" page; no full catalog sync, scheduling, or backfill strategy.
- No CI pipeline defined yet.
- Integration tests depend on a running database and are not automated in CI.
