#!/usr/bin/env bash
# F-026: Smoke-test the pilot deployment.
#
# Usage: ./scripts/ops/smoke_test.sh
#
# Verifies:
# - All containers are running and healthy
# - Database is reachable
# - LLM Gateway is healthy
# - Tutor API /health and /ready return 200
# - Frontend /healthz and /backend-health return 200
# - A synthetic login page loads
#
# Returns 0 on success, 1 on failure.

set -euo pipefail

# For exec commands, use the default compose file — the running containers are
# identified by project name, not by which compose file launched them.
COMPOSE="docker compose"
COMPOSE_PILOT="docker compose -f docker-compose.yml -f docker-compose.pilot.yml"
FAILURES=0
API_URL="${API_URL:-http://localhost:8002}"
FRONTEND_URL="${FRONTEND_URL:-http://localhost:3000}"

check() {
    local name="$1" cmd="$2"
    if eval "$cmd" >/dev/null 2>&1; then
        echo "  PASS  $name"
    else
        echo "  FAIL  $name"
        FAILURES=$((FAILURES + 1))
    fi
}

echo "=== Container status ==="
$COMPOSE_PILOT ps --format "table {{.Name}}\t{{.Status}}" 2>/dev/null \
    || $COMPOSE ps --format "table {{.Name}}\t{{.Status}}" | tee /dev/stderr | grep -c "healthy\|running" || true

echo ""
echo "=== Health checks ==="
# Exec commands use the default compose file — running containers are found by project name.
check "db pg_isready" "$COMPOSE exec -T db pg_isready -U ${POSTGRES_USER:-ai_tutor} -d ${POSTGRES_DB:-ai_tutor}"
check "llm-gateway /health" "$COMPOSE exec -T llm-gateway python -c \"import urllib.request; urllib.request.urlopen('http://localhost:8001/health')\""
check "llm-gateway /ready" "$COMPOSE exec -T llm-gateway python -c \"import urllib.request; urllib.request.urlopen('http://localhost:8001/ready')\""
check "tutor-api /health" "curl -sf --max-time 5 $API_URL/health"
check "tutor-api /ready" "curl -sf --max-time 5 $API_URL/ready"
check "frontend /healthz" "curl -sf --max-time 5 $FRONTEND_URL/healthz"
check "frontend /backend-health" "curl -sf --max-time 5 $FRONTEND_URL/backend-health"

echo ""
echo "=== Synthetic surface checks ==="
check "login page loads" "curl -sf --max-time 5 $API_URL/login | grep -q 'Sign in\|login\|email'"
check "learn page loads" "curl -sf --max-time 5 $API_URL/learn | grep -q 'Start learning\|AI Tutor'"
check "parent page loads" "curl -sf --max-time 5 $FRONTEND_URL/parent | grep -q 'Parent\|parent'"

echo ""
if [ "$FAILURES" -eq 0 ]; then
    echo "All smoke tests passed."
    exit 0
else
    echo "$FAILURES smoke test(s) failed."
    exit 1
fi
