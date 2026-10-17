#!/usr/bin/env bash
# Linux 終端機手動備份。排程請用 Windows 工作排程器。
#   bash ops/backup_db.sh

set -uo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
BACKUP_DIR="$ROOT/ops/backups"
LOG_DIR="$ROOT/ops/logs"
mkdir -p "$BACKUP_DIR" "$LOG_DIR"
LOG="$LOG_DIR/backup_db_$(date +%Y%m%d).log"
DEST="$BACKUP_DIR/football_db_$(date +%Y%m%d).sql.gz"

log() {
  printf '%s  %s\n' "$(date '+%F %T')" "$1" >>"$LOG"
}

log "start cwd=$ROOT"

if ! docker compose ps --status running --services | grep -qx db; then
  log "db 容器沒有在跑。先在專案目錄執行 docker compose up -d"
  exit 1
fi

code=0
docker compose exec -T -e PGPASSWORD=football_pass db \
  pg_dump -U football_user -d football_db --no-owner | gzip >"$DEST" || code=$?

if [ "$code" -ne 0 ] || [ ! -s "$DEST" ]; then
  log "pg_dump failed exit $code"
  rm -f "$DEST"
  exit 1
fi

removed=0
while IFS= read -r old; do
  rm -f "$old"
  removed=$((removed + 1))
done < <(find "$BACKUP_DIR" -name 'football_db_*.sql.gz' -type f -mtime +14)
log "wrote $DEST removed=$removed"
exit 0
