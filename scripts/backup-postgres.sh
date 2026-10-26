#!/usr/bin/env bash
set -euo pipefail
umask 077
BACKUP_DIR="$HOME/backups"
BACKUP_FILE="$BACKUP_DIR/app_db_$(date -u +%Y%m%d_%H%M%S).dump"

mkdir -p "$BACKUP_DIR"

sudo -n docker exec postgres_db sh -c \
  'PGPASSWORD="$POSTGRES_PASSWORD" pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc' \
  > "$BACKUP_FILE"
test -s "$BACKUP_FILE"

sudo -n docker exec -i postgres_db \
  pg_restore --list < "$BACKUP_FILE" > /dev/null

rclone copy "$BACKUP_FILE" backup_crypt:

printf 'Резервная копия загружена: %s\n' "$BACKUP_FILE"

# Удаляем облачные копии старше 30 суток.
rclone delete backup_crypt: \
  --include '/app_db_*.dump' \
  --min-age 30d

# Удаляем локальные копии старше 7 суток.
find "$BACKUP_DIR" -maxdepth 1 -type f \
  -name 'app_db_*.dump' -mmin +10080 -delete

METRICS_DIR="$HOME/monitoring/textfile"
METRICS_TMP="$(mktemp "$METRICS_DIR/postgres_backup.XXXXXX")"

printf 'postgres_backup_last_success_timestamp_seconds %s\n' \
  "$(date +%s)" > "$METRICS_TMP"

chmod 644 "$METRICS_TMP"
mv "$METRICS_TMP" "$METRICS_DIR/postgres_backup.prom"