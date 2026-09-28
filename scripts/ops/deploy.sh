#!/usr/bin/env bash
# F-026: Deploy a new release to the pilot VPS.
#
# Usage: ./scripts/ops/deploy.sh [git-ref]
#   git-ref defaults to 'main'
#
# Steps:
# 1. Record current commit for rollback
# 2. Pull latest code
# 3. Backup database
# 4. Build images
# 5. Run migrations
# 6. Restart services
# 7. Run smoke tests
# 8. Report status

set -euo pipefail

COMPOSE="docker compose -f docker-compose.yml -f docker-compose.pilot.yml"
REF="${1:-main}"
PREV_COMMIT="$(git rev-parse HEAD)"
BACKUP_DIR="${BACKUP_DIR:-./backups}"

echo "[deploy] Previous commit: $PREV_COMMIT"

echo "[deploy] Fetching latest code..."
git fetch origin "$REF"
git checkout "$REF"
git pull origin "$REF"

echo "[deploy] Creating pre-deploy backup..."
./scripts/ops/backup_db.sh

echo "[deploy] Building images..."
$COMPOSE build

echo "[deploy] Running migrations..."
$COMPOSE up -d db
$COMPOSE run --rm migrate

echo "[deploy] Starting all services..."
$COMPOSE up -d

echo "[deploy] Waiting for readiness..."
sleep 10

echo "[deploy] Running smoke tests..."
./scripts/ops/smoke_test.sh

echo "[deploy] Deploy complete at $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "[deploy] Rollback: git checkout $PREV_COMMIT && ./scripts/ops/deploy.sh"
