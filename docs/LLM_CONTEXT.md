# FilmCortex — Complete Project Context

> **Purpose of this document:** Give an LLM (or new contributor) full context on what FilmCortex is, what has been built, how it works, and what has not been built yet. Read this before making changes or answering questions about the project.
>
> **Version:** 0.1.0  
> **Branch at time of writing:** `feature/initial-development`  
> **Last updated:** 2026-07-11

---

## 1. What FilmCortex Is

FilmCortex is an **AI-powered movie intelligence engine** for personalized Jellyfin recommendations and auto-generated movie collections.

**End goal:** Ingest movie metadata, compute embeddings and recommendations offline, and expose a read-only API that Jellyfin (or other clients) can query for "similar movies," semantic search, and curated collections.

**Current state:** Foundation is complete — TMDb ingestion, PostgreSQL storage, offline embedding generation, and a read API with movie listing and similarity search. Recommendation engine, user taste modeling, semantic search endpoint, Jellyfin integration, and Radarr integration are **not yet built**.

**Core architectural rule:**

```
TMDb → [Ingestion job] → PostgreSQL → [Offline jobs: embeddings, etc.] → API (read-only, precomputed)
```

- **Ingestion is the only component allowed to call TMDb.**
- All downstream jobs read exclusively from PostgreSQL.
- The API performs **no external API calls** and **no model inference** at request time.
- Full provider payloads are stored so jobs can re-run deterministically without re-contacting TMDb.

---

## 2. Tech Stack

| Layer | Technology |
|-------|------------|
| Language | Python 3.12+ |
| Web framework | FastAPI |
| ASGI server | Uvicorn (`[standard]` extras) |
| Database | PostgreSQL 16 with **pgvector** extension |
| ORM | SQLAlchemy 2.x (async) |
| DB driver | asyncpg |
| Vector search | pgvector (384-dim cosine similarity) |
| Migrations | Alembic |
| HTTP client | httpx (async, for TMDb) |
| Config | pydantic-settings (loads `.env`) |
| API schemas | Pydantic v2 |
| Embeddings (offline only) | sentence-transformers (`BAAI/bge-small-en-v1.5`, 384 dims) |
| Package manager | uv |
| Linting | Ruff |
| Testing | pytest + pytest-asyncio |
| Containers | Docker + Docker Compose |

**Not used:** OpenAI, LangChain, Redis, Celery, Node.js, frontend, CI/CD.

**Planned integrations (not implemented):** Jellyfin (target consumer), Radarr (env vars stubbed only).

---

## 3. Repository Structure

```
filmCortex/
├── alembic/                          # Database migrations
│   ├── env.py                        # Async Alembic runner
│   └── versions/
│       ├── 001_initial_movies_and_external_metadata.py
│       ├── 002_enable_pgvector.py
│       └── 003_movie_embeddings.py
├── alembic.ini
├── docker-compose.yml                # db + api services
├── Dockerfile                        # Python 3.12, uv sync, uvicorn
├── docs/
│   ├── architecture.md               # Current system design
│   ├── roadmap.md                    # Milestones
│   ├── devlog/                       # Engineering journal
│   └── LLM_CONTEXT.md                # This file
├── pipeline/                         # Offline batch jobs (NOT in src/)
│   ├── jobs/
│   │   ├── ingest_initial_load.py    # Export seed + top rated + discover
│   │   ├── ingest_daily_export.py    # Daily ID export → new IDs
│   │   ├── ingest_top_rated.py
│   │   ├── ingest_discover.py
│   │   ├── ingest_trending.py
│   │   ├── ingest_list.py
│   │   ├── ingest_tmdb.py            # Popular page (manual/smoke)
│   │   └── generate_embeddings.py    # Generate embeddings for movies missing them
│   └── shared/
│       ├── job_context.py            # Shared DB/TMDb job setup
│       └── limits.py                 # CLI vs settings limit resolver
├── pyproject.toml                    # Dependencies, pytest/ruff config
├── uv.lock
├── README.md
├── scripts/
│   └── docker-entrypoint.sh          # Runs alembic then exec (NOT wired in Dockerfile)
├── src/filmcortex/                   # Main application package
│   ├── main.py                       # FastAPI app entry point
│   ├── api/                          # HTTP layer
│   │   ├── router.py                 # Mounts /api
│   │   ├── deps.py                   # FastAPI dependency injection
│   │   └── v1/
│   │       ├── router.py
│   │       ├── health.py
│   │       └── movies.py
│   ├── config/
│   │   └── settings.py               # Pydantic settings from env
│   ├── core/
│   │   └── logging.py                # Logging config for pipeline jobs
│   ├── db/
│   │   ├── base.py                   # SQLAlchemy DeclarativeBase
│   │   └── session.py                # Async engine + session factory
│   ├── integrations/
│   │   └── tmdb/
│   │       ├── client.py             # Async TMDb HTTP client (rate-limited)
│   │       ├── constants.py          # Provider, append_to_response, discover sweeps
│   │       ├── exports.py            # Daily ID export download/parse/diff
│   │       └── rate_limit.py         # Token-bucket limiter
│   ├── models/                       # SQLAlchemy ORM entities
│   │   ├── movie.py
│   │   ├── external_metadata.py
│   │   └── movie_embedding.py
│   ├── repositories/               # Data access layer
│   │   ├── movie_repository.py
│   │   ├── external_metadata_repository.py
│   │   └── movie_embedding_repository.py
│   ├── schemas/                      # Pydantic request/response models
│   │   ├── health.py
│   │   └── movie.py
│   ├── services/                     # Business logic
│   │   ├── movie_query.py
│   │   ├── movie_similarity.py
│   │   ├── movie_embedding.py
│   │   └── tmdb_ingestion.py
│   └── utils/
│       ├── embedding_text.py         # Build natural-language doc from TMDb payload
│       └── payload.py                # SHA-256 fingerprint for change detection
└── tests/                            # pytest suite (unit + integration)
```

---

## 4. Application Architecture

### Layering

```
api/          → Routers, HTTP handlers, FastAPI Depends() wiring
services/     → Business logic (ingestion, embeddings, similarity, queries)
repositories/ → SQLAlchemy data access (CRUD, vector search)
models/       → SQLAlchemy ORM table definitions
db/           → Engine and async session factory
schemas/      → Pydantic response/request models
integrations/ → External API clients (TMDb only)
utils/        → Pure helpers (no DB, no network)
config/       → Environment-based settings
core/         → Cross-cutting concerns (logging)
pipeline/     → Offline job entry points (imports from filmcortex package)
```

### Dependency injection

`src/filmcortex/api/deps.py` wires:
- `get_db()` — async session with auto commit/rollback
- Repository factories → Service factories → injected into route handlers

### App entry point

`src/filmcortex/main.py`:
- Creates FastAPI app with lifespan (disposes DB engine on shutdown)
- Mounts router at `/api`
- OpenAPI docs at `/docs`

---

## 5. Database Schema

### Entity relationships

```
movies (1) ──< (many) external_metadata
movies (1) ──< (0..1) movie_embeddings
```

### Table: `movies`

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID | Primary key, auto-generated |
| `canonical_title` | VARCHAR(512) | NOT NULL |
| `media_type` | ENUM | Currently only `film` (`MediaType.FILM`) |
| `first_indexed_at` | TIMESTAMPTZ | Server default `now()` |

Model: `src/filmcortex/models/movie.py`  
Migration: `001_initial_movies_and_external_metadata`

### Table: `external_metadata`

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID | Primary key |
| `movie_id` | UUID | FK → `movies.id` ON DELETE CASCADE |
| `provider` | VARCHAR(64) | e.g. `"tmdb"` |
| `provider_id` | VARCHAR(128) | External ID as string |
| `payload` | JSONB | Full TMDb API response |
| `payload_version` | VARCHAR(32) | Schema version (`"2"` for TMDb) |
| `fetched_at` | TIMESTAMPTZ | Server default `now()` |
| `is_active` | BOOLEAN | Default `true` |

**Unique constraint:** `(provider, provider_id)`

Model: `src/filmcortex/models/external_metadata.py`

The repository computes a SHA-256 fingerprint of the payload for change detection (not stored as a column — computed on read via `utils/payload.py`).

### Table: `movie_embeddings`

| Column | Type | Notes |
|--------|------|-------|
| `movie_id` | UUID | PK + FK → `movies.id` ON DELETE CASCADE |
| `embedding` | VECTOR(384) | pgvector column |
| `embedded_text` | TEXT | Source text that was embedded |
| `model_name` | VARCHAR(128) | e.g. `BAAI/bge-small-en-v1.5` |
| `model_revision` | VARCHAR(128) | Nullable, best-effort from model |
| `generated_at` | TIMESTAMPTZ | Server default `now()` |

Model: `src/filmcortex/models/movie_embedding.py`  
Migration: `003_movie_embeddings`

### Extension

Migration `002_enable_pgvector` runs `CREATE EXTENSION IF NOT EXISTS vector`.

---

## 6. API Endpoints

**Base URL:** `http://localhost:8000`  
**Prefix:** `/api/v1`  
**Interactive docs:** `http://localhost:8000/docs`

| Method | Route | Purpose | Response |
|--------|-------|---------|----------|
| GET | `/api/v1/health` | Liveness check | `{"status": "ok"}` |
| GET | `/api/v1/movies` | List ingested movies | `list[MovieListItem]` |
| GET | `/api/v1/movies/{movie_id}/similar` | Similar movies by embedding | `list[SimilarMovie]` |

### GET /api/v1/movies

- Joins `movies` with active `external_metadata`
- Returns: `id`, `canonical_title`, `provider`, `provider_id`
- Ordered by `canonical_title`
- Handler: `src/filmcortex/api/v1/movies.py` → `MovieQueryService`

### GET /api/v1/movies/{movie_id}/similar

- Query param: `include_scores: bool = false`
- Uses pgvector **cosine distance** on precomputed embeddings
- Returns 404 if movie not found or has no embedding
- Default limit: 10 similar movies
- Filters to active TMDb metadata only
- Excludes source movie from results
- Handler: `MovieSimilarityService.find_similar()`

### Response schemas (`src/filmcortex/schemas/movie.py`)

```python
class MovieListItem:
    id: UUID
    canonical_title: str
    provider: str
    provider_id: str

class SimilarMovie(MovieListItem):
    similarity_score: float | None  # only when include_scores=true
```

---

## 7. Services (Business Logic)

### TMDbIngestionService (`services/tmdb_ingestion.py`)

Ingests movies from TMDb into PostgreSQL.

**Flow per movie:**
1. Fetch full movie detail from TMDb (`append_to_response` includes credits, keywords, external_ids, images, videos, alternative_titles, translations)
2. Compute SHA-256 payload fingerprint
3. If new → create `movies` row + `external_metadata` row → `"inserted"`
4. If exists, fingerprint unchanged → `"skipped"`
5. If exists, fingerprint changed → update title + payload → `"updated"`

**Batch methods:** `ingest_ids`, `ingest_from_paged_endpoint` (with `max_movies` / `max_pages`), `ingest_top_rated`, `ingest_discover`, `ingest_trending`, `ingest_list`, `ingest_daily_export`, `ingest_popular_page`.

### MovieEmbeddingService (`services/movie_embedding.py`)

Offline embedding generation. Loads sentence-transformers model lazily.

**Flow:**
1. Count movies with active TMDb metadata but no embedding (`pending`)
2. Load a batch (default `EMBEDDING_BATCH_SIZE`, CLI `--limit` overrides)
3. For each: build embedding text from payload → encode with model → upsert `movie_embeddings`
4. Returns stats: `{pending, generated, failed}`

**Idempotent for missing embeddings:** Only processes movies without an embedding. Does not yet re-embed when payloads change.

### MovieSimilarityService (`services/movie_similarity.py`)

Finds similar movies using precomputed embeddings.

- Looks up source movie's embedding
- Queries pgvector for nearest neighbors by cosine distance
- Maps results to `SimilarMovie` schema
- Returns `None` if source movie has no embedding (API returns 404)

### MovieQueryService (`services/movie_query.py`)

Lists ingested movies for the API. Joins movies with active external metadata.

---

## 8. Repositories (Data Access)

| Repository | Key methods |
|------------|-------------|
| `MovieRepository` | `create()`, `update_title()` |
| `ExternalMetadataRepository` | `create()`, `get_by_provider()`, `get_existing_provider_ids()`, `update_payload()`, `list_active_with_movies()` |
| `MovieEmbeddingRepository` | `upsert()`, `get_by_movie_id()`, `count_movies_without_embeddings()`, `list_movies_without_embeddings(limit=)`, `find_similar()` |

Vector search is in `MovieEmbeddingRepository.find_similar()` using pgvector's cosine distance operator.

---

## 9. External Integrations

### TMDb (The Movie Database) — IMPLEMENTED

**Client:** `src/filmcortex/integrations/tmdb/client.py`

| Method | TMDb endpoint | Used by |
|--------|---------------|---------|
| `get_movie(movie_id)` | `GET /movie/{id}?append_to_response=...` | All ingest jobs |
| `get_popular(page)` | `GET /movie/popular` | `ingest_tmdb` |
| `get_top_rated(page)` | `GET /movie/top_rated` | `ingest_top_rated`, initial load |
| `get_discover(page, **filters)` | `GET /discover/movie` | `ingest_discover`, initial load |
| `get_trending(time_window, page)` | `GET /trending/movie/{window}` | `ingest_trending` |
| `get_list(list_id)` | `GET /list/{id}` | `ingest_list` |
| `get_collection(id)` | `GET /collection/{id}` | Available |
| `get_movie_changes(...)` | `GET /movie/{id}/changes` | Available (no dedicated job yet) |
| `search_movie(query)` | `GET /search/movie` | Implemented but unused |

Daily exports are downloaded from `files.tmdb.org/p/exports/` (no API key) via `integrations/tmdb/exports.py`.

**Auth:** `TMDB_API_KEY` env var, passed as query parameter. Client rate-limits requests and retries on 429.

### Hugging Face / sentence-transformers — IMPLEMENTED (pipeline only)

- Model: `BAAI/bge-small-en-v1.5` (configurable via `EMBEDDING_MODEL_NAME`)
- 384 dimensions, normalized embeddings
- Used only in offline `generate_embeddings` job
- Requires `uv sync --extra pipeline` to install

### Jellyfin — NOT IMPLEMENTED

Target consumer. Referenced in project description only.

### Radarr — NOT IMPLEMENTED

`RADARR_URL` and `RADARR_API_KEY` exist in `.env.example` but no code uses them.

### OpenAI — NOT USED

---

## 10. Offline Pipeline Jobs

Located in `pipeline/jobs/`. Run as Python modules. Each job has a safe default batch limit from settings; CLI `--limit` (and related flags) override configuration. Jobs are scheduler-agnostic — wire them into cron/systemd/K8s later without changing app code. See [README](../README.md) for the recommended homelab schedule.

### Initial load (once)

```bash
uv run python -m pipeline.jobs.ingest_initial_load
```

- Export seed (`TMDB_INITIAL_LOAD_LIMIT`) + top rated (`TMDB_TOP_RATED_LIMIT`) + discover sweeps (`TMDB_DISCOVER_LIMIT`)

### Daily / weekly jobs

```bash
# Daily (resumable top-rated crawl; skips IDs already in DB)
uv run python -m pipeline.jobs.ingest_top_rated       # TMDB_TOP_RATED_LIMIT
uv run python -m pipeline.jobs.generate_embeddings

# Weekly
uv run python -m pipeline.jobs.ingest_discover --preset all   # TMDB_DISCOVER_LIMIT
uv run python -m pipeline.jobs.ingest_trending        # TMDB_TRENDING_LIMIT
uv run python -m pipeline.jobs.generate_embeddings
```

`ingest_daily_export` remains available manually but is not on the homelab schedule.
### Manual

```bash
uv run python -m pipeline.jobs.ingest_list --list-id 634
uv run python -m pipeline.jobs.ingest_tmdb --page 1
```

### Generate embeddings

```bash
uv sync --extra pipeline
uv run python -m pipeline.jobs.generate_embeddings    # EMBEDDING_BATCH_SIZE
```

- Processes a batch of movies missing embeddings
- Idempotent for the missing-embedding backlog — safe to re-run
- Prints: pending (total backlog), generated, failed counts
---

## 11. Embedding Text Builder

`src/filmcortex/utils/embedding_text.py` — **pure function**, no side effects.

Takes a TMDb payload dict, returns a natural-language document:

```
Title (Year)

Overview paragraph...

Genres: Action, Thriller
Keywords: revenge, heist
Director: Christopher Nolan
Cast: Actor1, Actor2, Actor3, Actor4, Actor5
Runtime: 148 minutes
Language: English
```

- Max 5 cast members (sorted by billing order)
- Falls back gracefully when fields are missing
- Designed to be iterated on independently of embedding model

---

## 12. Payload Fingerprinting

`src/filmcortex/utils/payload.py`

- Computes SHA-256 hash of canonical JSON serialization of TMDb payload
- Used by ingestion to detect unchanged payloads (skip re-write)
- Stable ordering ensures same payload always produces same fingerprint

---

## 13. Configuration

**Settings class:** `src/filmcortex/config/settings.py` (pydantic-settings)  
**Template:** `.env.example`

| Variable | Default | Purpose |
|----------|---------|---------|
| `APP_NAME` | `FilmCortex` | App title |
| `APP_ENV` | `development` | Environment name |
| `APP_DEBUG` | `false` | SQL echo when true |
| `API_HOST` | `0.0.0.0` | API bind host |
| `API_PORT` | `8000` | API port |
| `DATABASE_URL` | `postgresql+asyncpg://filmcortex:filmcortex@localhost:5433/filmcortex` | Async PostgreSQL URL |
| `TMDB_API_KEY` | `""` | Required for ingestion |
| `TMDB_REQUESTS_PER_SECOND` | `30` | Client rate limit |
| `TMDB_EXPORT_CACHE_DIR` | `.cache/tmdb_exports` | Daily export cache |
| `TMDB_INITIAL_LOAD_LIMIT` | `500` | Initial load export step |
| `TMDB_DAILY_EXPORT_LIMIT` | `100` | Daily export job |
| `TMDB_TRENDING_LIMIT` | `40` | Trending job |
| `TMDB_TOP_RATED_LIMIT` | `100` | Top rated job / initial load |
| `TMDB_DISCOVER_LIMIT` | `100` | Discover job / initial load |
| `EMBEDDING_MODEL_NAME` | `BAAI/bge-small-en-v1.5` | HuggingFace model |
| `EMBEDDING_DIMENSIONS` | `384` | Must match model output |
| `EMBEDDING_BATCH_SIZE` | `100` | Embeddings per job run |
| `RADARR_URL` | — | Not implemented |
| `RADARR_API_KEY` | — | Not implemented |

Docker Compose also sets: `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `PYTHONPATH=/app/src`.

---

## 14. Infrastructure (Docker)

### docker-compose.yml

| Service | Image / Build | Port | Notes |
|---------|---------------|------|-------|
| `db` | `pgvector/pgvector:pg16` | 5433→5432 | Healthcheck via `pg_isready`, volume `postgres_data` |
| `api` | Built from Dockerfile | 8000→8000 | Depends on healthy db, hot-reload via volume mount |

**API command:** `uvicorn filmcortex.main:app --host 0.0.0.0 --port 8000 --reload`

### Dockerfile

- Base: `python:3.12-slim`
- Package manager: `uv`
- Installs production deps only (`uv sync --frozen --no-dev --no-editable`)
- Default CMD: uvicorn (no alembic)

### Known gap

`scripts/docker-entrypoint.sh` exists (runs `alembic upgrade head` then exec) but is **NOT wired** in Dockerfile or docker-compose. README claims auto-migrations on container start — **this is incorrect**. Migrations must be run manually:

```bash
docker compose up -d db
uv run alembic upgrade head
```

---

## 15. Testing

**Framework:** pytest with `asyncio_mode = auto`  
**Fixture:** `tests/conftest.py` — async HTTP client via httpx ASGITransport

### Test files (14 total)

| File | Type | What it tests |
|------|------|---------------|
| `tests/api/test_health.py` | Unit | Health endpoint |
| `tests/api/test_movies.py` | Unit (mocked DI) | Movie list endpoint |
| `tests/api/test_similar_movies.py` | Unit (mocked DI) | Similar movies endpoint, scores, 404 |
| `tests/services/test_movie_similarity.py` | Unit (mocked repo) | Similarity logic |
| `tests/services/test_movie_embedding_service.py` | Unit (mocked) | Embedding generation stats |
| `tests/services/test_tmdb_ingestion.py` | Unit (mocked) | Insert, skip, update flows |
| `tests/repositories/test_movie_embedding_repository.py` | **Integration** | Upsert, pending list, cosine search |
| `tests/integrations/test_tmdb_client.py` | Unit (mocked httpx) | TMDb client requests |
| `tests/utils/test_embedding_text.py` | Unit | Document builder |
| `tests/utils/test_payload.py` | Unit | Fingerprint stability |
| `tests/models/test_movie_embedding.py` | Unit | Model schema |
| `tests/migrations/test_002_enable_pgvector.py` | Unit + Integration | pgvector extension |
| `tests/migrations/test_003_movie_embeddings.py` | Unit + Integration | Embeddings table |

Integration tests use `@pytest.mark.integration` and skip if `DATABASE_URL` is unset.

### Not covered

- End-to-end API tests against real DB
- `MovieRepository`, `ExternalMetadataRepository` direct tests
- `MovieQueryService` direct tests
- Pipeline job integration tests
- Docker/container tests
- CI pipeline (does not exist)

---

## 16. Dependencies

From `pyproject.toml`:

**Core:** alembic, asyncpg, fastapi, httpx, pgvector, pydantic-settings, sqlalchemy[asyncio], uvicorn[standard]

**Optional `[dev]`:** pytest, pytest-asyncio, ruff

**Optional `[pipeline]`:** sentence-transformers (pulls torch, transformers, huggingface-hub, numpy, scipy, scikit-learn)

**Build:** uv_build  
**Lock file:** `uv.lock`

---

## 17. How to Run

### First-time setup

```bash
cp .env.example .env          # Set TMDB_API_KEY
uv sync --all-extras            # Install all deps
docker compose up -d            # Start db + api
uv run alembic upgrade head     # Run migrations (manual — see §14)
```

### Verify pgvector

```bash
docker compose exec db psql -U filmcortex -d filmcortex -c \
  "SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';"
```

### Run pipeline

```bash
uv run python -m pipeline.jobs.ingest_initial_load
uv run python -m pipeline.jobs.generate_embeddings
# thereafter: daily export / trending / weekly top_rated + discover (see README)
```

### Run tests

```bash
uv run pytest
uv run pytest tests/migrations/ -m integration   # needs running DB
uv run ruff check .
```

---

## 18. What Is Built vs. Not Built

### Built (working)

- [x] Project scaffolding (uv, Ruff, pytest)
- [x] FastAPI app with `/api/v1` routing
- [x] Health endpoint
- [x] PostgreSQL 16 + pgvector via Docker
- [x] Async SQLAlchemy + Alembic migrations (001, 002, 003)
- [x] Core schema: `movies`, `external_metadata`, `movie_embeddings`
- [x] TMDb client (details, popular, top rated, discover, trending, lists, collections, changes, rate limiting)
- [x] Multi-source ingestion jobs (initial load, daily export, top rated, discover, trending, lists, popular)
- [x] Configurable homelab batch limits (settings / CLI overrides)
- [x] Embedding text builder (pure function)
- [x] Offline embedding generation job (sentence-transformers, batch-sized)
- [x] Movie listing API (`GET /api/v1/movies`)
- [x] Similar movies API (`GET /api/v1/movies/{id}/similar`)
- [x] pgvector cosine similarity search
- [x] Docker Compose (db + api)
- [x] Test suite (unit + integration)

### Not built (planned)

- [ ] Semantic search API (natural-language query → similar movies)
- [ ] Recommendation generation (personalized, offline)
- [ ] User taste modeling
- [ ] Auto-generated collections (clustering)
- [ ] Jellyfin integration
- [ ] Radarr / ARR integration
- [ ] Metadata refresh job / Movie Changes–driven updates
- [ ] Re-embed on payload change
- [ ] Additional metadata providers (schema supports it)
- [ ] API pagination, filtering, authentication
- [ ] Built-in scheduler (intentionally omitted — use external cron/systemd/K8s)
- [ ] CI pipeline
- [ ] Canonical Movie Document (provider-agnostic embedding source)
- [ ] Natural-language discovery UX
- [ ] Wire Docker entrypoint for auto-migrations
---

## 19. Documentation Notes

Keep `docs/architecture.md`, `docs/roadmap.md`, and this file in sync when milestones land. Prefer the codebase if a short-lived conflict remains.

| Doc | Role |
|-----|------|
| `docs/architecture.md` | How the system works today |
| `docs/roadmap.md` | Done / current / upcoming |
| `README.md` | Quick start, migrations, pipeline schedule + batch limits |

Known operational gap: README historically claimed auto-migrations on API start; the entrypoint script exists but is **not wired** in Docker. Migrations are still manual (`uv run alembic upgrade head`).
---

## 20. Design Decisions Worth Knowing

1. **Provider-agnostic movies table.** `movies` holds canonical title and media type. Provider-specific data lives in `external_metadata` with a flexible JSONB payload. This allows adding providers beyond TMDb without schema changes.

2. **Full payload storage.** TMDb responses (including credits and keywords via `append_to_response`) are stored whole. Downstream jobs never need TMDb access.

3. **Offline-first AI.** Embeddings are computed in batch jobs, not at request time. The API is fast and deterministic.

4. **Pure embedding text builder.** Separated from DB and model loading so document format can be iterated and tested independently.

5. **Fingerprint-based skip.** Ingestion avoids unnecessary DB writes when TMDb payload hasn't changed.

6. **Idempotent embedding job.** Only processes movies without embeddings. Re-running is safe until the backlog clears (batch-sized).

7. **Homelab batch limits.** Defaults in settings prevent accidental full-catalog ingestion; CLI overrides for one-off runs. No built-in scheduler.

8. **Layered architecture with DI.** Repositories → Services → API, wired via FastAPI `Depends()`. Easy to mock in tests.

---

## 21. Typical Data Flow (End to End)

```
1. Operator runs:  uv run python -m pipeline.jobs.ingest_initial_load
   → Daily ID export downloaded; limited IDs ingested
   → Top rated + discover sweeps ingest notable films
   → For each movie: full detail fetched, fingerprint checked, upserted
   → Result: rows in `movies` + `external_metadata`

2. Operator runs:  uv run python -m pipeline.jobs.generate_embeddings
   → Finds a batch of movies without embeddings
   → Builds text doc from TMDb payload (title, overview, genres, cast, etc.)
   → Encodes with BAAI/bge-small-en-v1.5
   → Upserts into `movie_embeddings`

3. Ongoing: daily export + trending; weekly top_rated + discover; then embeddings

4. Client calls:   GET /api/v1/movies
   → Returns list of ingested movies

5. Client calls:   GET /api/v1/movies/{id}/similar?include_scores=true
   → Looks up embedding for source movie
   → pgvector cosine search for nearest neighbors
   → Returns top 10 similar movies with optional scores
```
---

## 22. Key File Quick Reference

| Need to... | Look at |
|------------|---------|
| Add an API endpoint | `src/filmcortex/api/v1/`, register in `router.py` |
| Add business logic | `src/filmcortex/services/` |
| Add DB query | `src/filmcortex/repositories/` |
| Add a table | `src/filmcortex/models/` + new Alembic migration |
| Add env var | `src/filmcortex/config/settings.py` + `.env.example` |
| Add offline job | `pipeline/jobs/` |
| Change embedding text format | `src/filmcortex/utils/embedding_text.py` |
| Change TMDb integration | `src/filmcortex/integrations/tmdb/` |
| Add tests | `tests/` mirroring src structure |

---

*End of context document.*
