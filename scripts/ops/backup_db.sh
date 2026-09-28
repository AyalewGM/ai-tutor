#!/usr/bin/env bash
# F-026: Create a compressed PostgreSQL backup for the pilot deployment.
#
# Usage: ./scripts/ops/backup_db.sh
#
# Requires: docker compose stack running, .env.pilot present.
# Output: $BACKUP_DIR/ai_tutor_YYYYMMDD_HHMMSS.sql.gz
#         Default BACKUP_DIR=./backups (gitignored)

set -euo pipefail

COMPOSE="docker compose -f docker-compose.yml -f docker-compose.pilot.yml"
BACKUP_DIR="${BACKUP_DIR:-./backups}"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP_FILE="${BACKUP_DIR}/ai_tutor_${TIMESTAMP}.sql.gz"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-30}"

mkdir -p "$BACKUP_DIR"

# Read DB credentials from .env.pilot (never commit real values)
if [ -f .env.pilot ]; then
    set -a; source .env.pilot; set +a
fi
DB_NAME="${POSTGRES_DB:-ai_tutor}"
DB_USER="${POSTGRES_USER:-ai_tutor}"

echo "[backup] Starting backup of ${DB_NAME} → ${BACKUP_FILE}"
$COMPOSE exec -T db pg_dump -U "$DB_USER" -d "$DB_NAME" --no-owner --no-privileges \
    | gzip > "$BACKUP_FILE"

if [ ! -s "$BACKUP_FILE" ]; then
    echo "[backup] ERROR: Backup file is empty" >&2
    rm -f "$BACKUP_FILE"
    exit 1
fi

echo "[backup] Created $(du -h "$BACKUP_FILE" | cut -f1) backup: $BACKUP_FILE"

# Prune backups older than retention window
find "$BACKUP_DIR" -name 'ai_tutor_*.sql.gz' -mtime "+${RETENTION_DAYS}" -delete
echo "[backup] Retention: kept backups newer than ${RETENTION_DAYS} days"
