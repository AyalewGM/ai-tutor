#!/usr/bin/env bash
# F-026: Restore the PostgreSQL database from a compressed backup.
#
# Usage: ./scripts/ops/restore_db.sh <backup_file.sql.gz>
#
# This script will:
# 1. Stop the tutor-api and frontend services (traffic freeze)
# 2. Drop and recreate the database
# 3. Restore the backup
# 4. Run migrations to reconcile schema
# 5. Restart services and verify readiness
#
# IMPORTANT: Only restore to a backup created for the same application version.
# For cross-version restores, run migrations after restoring.

set -euo pipefail

if [ $# -lt 1 ]; then
    echo "Usage: $0 <backup_file.sql.gz>" >&2
    exit 1
fi

BACKUP_FILE="$1"
if [ ! -f "$BACKUP_FILE" ]; then
    echo "ERROR: Backup file not found: $BACKUP_FILE" >&2
    exit 1
fi

COMPOSE="docker compose -f docker-compose.yml -f docker-compose.pilot.yml"

if [ -f .env.pilot ]; then
    set -a; source .env.pilot; set +a
fi
DB_NAME="${POSTGRES_DB:-ai_tutor}"
DB_USER="${POSTGRES_USER:-ai_tutor}"

echo "[restore] Stopping application services..."
$COMPOSE stop tutor-api frontend llm-gateway

echo "[restore] Recreating database ${DB_NAME}..."
$COMPOSE exec -T db psql -U "$DB_USER" -d postgres -c "DROP DATABASE IF EXISTS ${DB_NAME};"
$COMPOSE exec -T db psql -U "$DB_USER" -d postgres -c "CREATE DATABASE ${DB_NAME};"

echo "[restore] Restoring from ${BACKUP_FILE}..."
gunzip -c "$BACKUP_FILE" | $COMPOSE exec -T db psql -U "$DB_USER" -d "$DB_NAME"

echo "[restore] Running migrations to reconcile schema..."
$COMPOSE run --rm migrate

echo "[restore] Restarting services..."
$COMPOSE up -d db llm-gateway tutor-api frontend

echo "[restore] Verifying readiness..."
sleep 5
$COMPOSE ps
curl --fail --retry 5 --retry-delay 2 http://localhost:8002/ready || {
    echo "[restore] ERROR: API not ready after restore" >&2
    exit 1
}

echo "[restore] Restore complete. Run smoke tests before admitting traffic."
