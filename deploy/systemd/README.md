# FilmCortex pipeline systemd timers

Homelab scheduling for the offline pipeline on Ubuntu (e.g. lab1). Application code stays scheduler-agnostic; these units only invoke the existing CLI jobs.

## Schedule (UTC)

| Timer | When | Jobs |
|-------|------|------|
| `filmcortex-pipeline-daily.timer` | every day 03:30 | `ingest_daily_export` → `generate_embeddings` → `ingest_trending` |
| `filmcortex-pipeline-weekly.timer` | Sunday 04:30 | `ingest_top_rated` → `ingest_discover --preset all` → `generate_embeddings` |

`Persistent=true` catches up if the machine was off at fire time. Daily and weekly share a flock so they do not overlap.

## Prerequisites (lab1)

- Repo at `/home/aaron/src/filmCortex` with `.env` configured
- `uv` at `~/.local/bin/uv`
- Postgres reachable (e.g. `filmcortex-db` via docker compose on port 5433)
- Pipeline deps installed: `uv sync --extra pipeline`

## Install

From the repo on the target host:

```bash
chmod +x deploy/systemd/install.sh scripts/run_daily.sh scripts/run_weekly.sh
./deploy/systemd/install.sh
```

## Useful commands

```bash
systemctl list-timers 'filmcortex-pipeline-*'
sudo systemctl start filmcortex-pipeline-daily.service   # run daily chain now
sudo systemctl start filmcortex-pipeline-weekly.service  # run weekly chain now
journalctl -u filmcortex-pipeline-daily.service -u filmcortex-pipeline-weekly.service -f
```

## Disable

```bash
sudo systemctl disable --now filmcortex-pipeline-daily.timer filmcortex-pipeline-weekly.timer
```
