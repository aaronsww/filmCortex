# FilmCortex Roadmap

A living roadmap. It records what is done, what is in progress, and where the project is heading. Update it as milestones move. For the current system design see [architecture.md](architecture.md); for the reasoning behind pivots see the [devlog](devlog/README.md).

_Last updated: 2026-07-11_

## Completed

- **Project foundation** — repository scaffolding, `uv`-managed dependencies, Ruff, pytest.
- **Service skeleton** — FastAPI app with `/api/v1` routing and a health endpoint.
- **Database foundation** — PostgreSQL 16 via `pgvector/pgvector:pg16`, async SQLAlchemy + asyncpg, Alembic migrations.
- **Core schema** — `movies` and `external_metadata` tables (migration `001`).
- **pgvector enabled** — `CREATE EXTENSION vector` (migration `002`).
- **TMDb ingestion foundation** — offline job that fetches movie metadata and upserts it with payload-fingerprint change detection; ingestion is the sole component that contacts TMDb.
- **Read API** — `GET /api/v1/movies` serving ingested movies.
- **Containerization** — `db` and `api` services in `docker-compose.yml`.
- **Embedding pipeline** — `movie_embeddings` table (migration `003`), offline `generate_embeddings` job (`sentence-transformers` / `BAAI/bge-small-en-v1.5`), embedding text builder, and `GET /api/v1/movies/{id}/similar` via pgvector cosine search.
- **Multi-source TMDb ingestion** — daily ID exports, top rated, discover sweeps, trending, curated lists, and initial bulk load; rate-limited client with `append_to_response`; configurable homelab batch limits; scheduler-agnostic job modules.

## Current milestone

**Semantic search and richer discovery API.**

- Expose natural-language movie search against stored embeddings.
- Add pagination/filtering on movie listing.
- Harden the read API for clients (Jellyfin and others) without request-time inference.

## Upcoming milestones

- **Recommendation generation** — offline job producing personalized recommendations from embeddings and user taste signals.
- **User taste modeling** — represent a user's preferences at a semantic level (beyond recent-history heuristics).
- **Collections** — automatically generated, meaningful movie collections (e.g. clustering).
- **ARR integration** — hand off "request/download this" actions to the existing ARR stack rather than reimplementing them.
- **Jellyfin integration** — wire FilmCortex as a recommendation/collections consumer for Jellyfin.

## Future ideas

- **Canonical Movie Document** — a stable, provider-agnostic representation used as the embedding source instead of raw TMDb text.
- **Metadata refresh job** — a future `refresh_tmdb_metadata.py` to refresh stored payloads and allow embeddings to be regenerated. Would join ingestion as the only other TMDb-facing component.
- **Re-embed on payload change** — detect stale embeddings when ingested payloads change and regenerate them.
- **Additional providers** — support external metadata sources beyond TMDb (the `external_metadata` schema is already provider-agnostic).
- **Natural-language discovery UX** — conversational interface for taste-driven discovery.
- **External scheduling** — operators wire pipeline jobs into cron, systemd timers, Kubernetes CronJobs, or similar (application stays scheduler-agnostic).

## Technical debt / known gaps

- The API surface is still thin (health, movie listing, similar); no semantic search endpoint, pagination, filtering, or auth yet.
- Embedding job only fills missing vectors; it does not re-embed when TMDb payloads change.
- No CI pipeline defined yet.
- Integration tests depend on a running database and are not automated in CI.
- Docker entrypoint can run migrations, but is not wired into the API image/compose flow (migrations are still run manually).
