#!/usr/bin/env bash
# Daily FilmCortex pipeline: top_rated (resumable) → embeddings.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

export PATH="${HOME}/.local/bin:/usr/local/bin:/usr/bin:/bin:${PATH:-}"

LOCK_FILE="${FILMCORTEX_PIPELINE_LOCK:-/tmp/filmcortex-pipeline.lock}"
exec 9>"$LOCK_FILE"
if ! flock -n 9; then
  echo "[filmcortex] daily pipeline skipped: another run holds $LOCK_FILE" >&2
  exit 0
fi

echo "[filmcortex] daily pipeline start $(date -u +%Y-%m-%dT%H:%M:%SZ)"
uv run python -m pipeline.jobs.ingest_top_rated
uv run python -m pipeline.jobs.generate_embeddings
echo "[filmcortex] daily pipeline done $(date -u +%Y-%m-%dT%H:%M:%SZ)"
