#!/usr/bin/env bash
# Linux 終端機（WSL）手動跑同一件事。排程請用 ops/register_schedules.ps1，不要靠 WSL cron。
#   bash ops/daily_sync.sh
#   bash ops/daily_sync.sh --dry-run

set -uo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
LOG_DIR="$ROOT/ops/logs"
mkdir -p "$LOG_DIR"
LOG="$LOG_DIR/daily_sync_$(date +%Y%m%d).log"

log() {
  printf '%s  %s\n' "$(date '+%F %T')" "$1" >>"$LOG"
}

log "start cwd=$ROOT"

if ! docker compose ps --status running --services | grep -qx api; then
  log "api 容器沒有在跑。先在專案目錄執行 docker compose up -d"
  exit 1
fi

code=0
docker compose exec -T api python scripts/master_sync.py "$@" >>"$LOG" 2>&1 || code=$?
log "exit $code"
exit "$code"
