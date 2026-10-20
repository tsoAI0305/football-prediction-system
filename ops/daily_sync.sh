#!/usr/bin/env bash
# 每日同步的唯一實作。Linux 上交給 cron；這台 Windows 由工作排程器呼叫 Git Bash 跑這支。
#   bash ops/daily_sync.sh
#   bash ops/daily_sync.sh --dry-run

set -uo pipefail

if [ -d "/c/Program Files/Docker/Docker/resources/bin" ]; then
  PATH="/c/Program Files/Docker/Docker/resources/bin:$PATH"
  export PATH
fi

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
