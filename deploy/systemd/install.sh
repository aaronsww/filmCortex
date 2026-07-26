#!/usr/bin/env bash
# Install FilmCortex pipeline systemd timers on this host (requires sudo).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
UNIT_DIR="$ROOT/deploy/systemd"
DEST=/etc/systemd/system

UNITS=(
  filmcortex-pipeline-daily.service
  filmcortex-pipeline-daily.timer
  filmcortex-pipeline-weekly.service
  filmcortex-pipeline-weekly.timer
)

chmod +x "$ROOT/scripts/run_daily.sh" "$ROOT/scripts/run_weekly.sh"

for unit in "${UNITS[@]}"; do
  sudo cp "$UNIT_DIR/$unit" "$DEST/$unit"
done

sudo systemctl daemon-reload
sudo systemctl enable --now filmcortex-pipeline-daily.timer
sudo systemctl enable --now filmcortex-pipeline-weekly.timer

echo
systemctl list-timers 'filmcortex-pipeline-*' --no-pager
echo
echo "Manual smoke test:"
echo "  sudo systemctl start filmcortex-pipeline-daily.service"
echo "  journalctl -u filmcortex-pipeline-daily.service -f"
