# F-026: Private Pilot Deployment & Operations Runbook

> **Scope:** This document covers deployment, verification, backup, restore,
> rollback, troubleshooting, and restart for the controlled 3–5 family private
> pilot on a VPS. It does not cover curriculum authoring, pedagogy changes, or
> learner-facing feature work.

---

## 1. Prerequisites

| Requirement | Notes |
|-------------|-------|
| VPS | Ubuntu 22.04+ or Debian 12+, 2 GB RAM minimum, 20 GB disk |
| Docker | 24.x+ with Compose plugin |
| DNS | A record pointing to the VPS |
| TLS | Terminated in front of nginx (e.g., Caddy, Traefik, or host nginx) |
| `.env.pilot` | Copied from `.env.pilot.example`, filled with strong secrets |

---

## 2. Initial Deployment

```bash
# 1. Clone and checkout the release tag
git clone https://github.com/AyalewGM/ai-tutor.git
cd ai-tutor
git checkout <release-commit>

# 2. Configure environment
cp .env.pilot.example .env.pilot
# Edit .env.pilot: set POSTGRES_PASSWORD, provider keys (or leave empty for fallback)
chmod 600 .env.pilot

# 3. Start the stack
docker compose -f docker-compose.yml -f docker-compose.pilot.yml up -d --build

# 4. Wait for readiness
docker compose -f docker-compose.yml -f docker-compose.pilot.yml ps
# All services should show "healthy" or "running"

# 5. Verify
./scripts/ops/smoke_test.sh
```

### What the pilot compose file does

- Uses `.env.pilot` for all environment/secrets (never committed).
- Runs a one-shot `migrate` service before `tutor-api` starts.
- Enables JSON log rotation (10 MiB × 3 files per service).
- Sets `restart: unless-stopped` on every service.
- Health-checks `tutor-api` via `/ready` (DB + Alembic head check).

---

## 3. Verification

| Check | Command | Expected |
|-------|---------|----------|
| DB ready | `docker compose exec db pg_isready -U ai_tutor` | `accepting connections` |
| Gateway health | `curl http://localhost:8001/health` | `{"status":"ok"}` |
| Gateway ready | `curl http://localhost:8001/ready` | `{"status":"ready"}` |
| API health | `curl http://localhost:8002/health` | `{"status":"ok"}` |
| API ready | `curl http://localhost:8002/ready` | `{"status":"ready"}` |
| Frontend | `curl http://localhost:3000/healthz` | `ok` |
| Backend proxy | `curl http://localhost:3000/backend-health` | `{"status":"ok"}` |
| Login page | `curl http://localhost:8002/login` | HTML with sign-in form |

Run all at once: `./scripts/ops/smoke_test.sh`

---

## 4. Backup

```bash
# Manual backup
./scripts/ops/backup_db.sh

# Cron example (daily at 02:00, keep 30 days)
0 2 * * * cd /opt/ai-tutor && ./scripts/ops/backup_db.sh >> /var/log/ai_tutor_backup.log 2>&1
```

- Output: `backups/ai_tutor_YYYYMMDD_HHMMSS.sql.gz`
- Default retention: 30 days (`BACKUP_RETENTION_DAYS` env var)
- Store backups off-host for disaster recovery (e.g., `scp` to a secure workstation)

---

## 5. Restore

```bash
# Restore from a specific backup
./scripts/ops/restore_db.sh backups/ai_tutor_20250928_020000.sql.gz
```

The script:
1. Stops `tutor-api`, `frontend`, `llm-gateway`
2. Drops and recreates the `ai_tutor` database
3. Restores the backup
4. Runs Alembic migrations
5. Restarts all services
6. Verifies readiness

**Important:** Only restore to a backup made for the same application version.
For cross-version restores, run migrations after restoring and verify manually.

---

## 6. Deploy a New Release

```bash
./scripts/ops/deploy.sh main        # or a specific commit/tag
```

The script:
1. Records the current commit for rollback
2. Pulls the latest code
3. Creates a pre-deploy backup
4. Builds images
5. Runs migrations
6. Restarts services
7. Runs smoke tests
8. Prints the rollback command if needed

---

## 7. Rollback

If the new release is broken:

```bash
# 1. Note the failed commit
git log --oneline -3

# 2. Checkout the previous known-good commit
git checkout <previous-commit>

# 3. Rebuild and restart
docker compose -f docker-compose.yml -f docker-compose.pilot.yml up -d --build

# 4. If the failed release ran migrations that broke the DB,
#    restore the pre-deploy backup:
./scripts/ops/restore_db.sh backups/<pre-deploy-backup>.sql.gz

# 5. Verify
./scripts/ops/smoke_test.sh
```

---

## 8. Pilot Account Provisioning

```bash
# Run interactively on the VPS
python scripts/ops/provision_pilot_family.py
```

The script prompts for:
- Parent email and display name
- Learner first name
- Curriculum selection
- Whether to generate a child link claim token

It prints the temporary password once. Share it securely with the parent.
The parent logs in at `/login`, changes their password, and links the learner.

### Account recovery

If a parent loses access:
1. Verify the parent's identity out-of-band.
2. Reset the password directly in the DB or create a new account and re-link.
3. Document the recovery in the pilot log.

---

## 9. Structured Logging

The application emits one JSON line per HTTP request with:
- `request_id` — UUID for correlation
- `method` — HTTP method
- `route` — route path template (no raw URLs that could contain names)
- `status` — HTTP status code
- `latency_ms` — response time
- `service` — `tutor-api`

**Never logged:** learner answers, problem prompts, PII, cookies, claim tokens,
provider API keys, or raw query strings.

View logs:
```bash
docker compose logs -f tutor-api
docker compose logs --tail 100 tutor-api | grep '"status":5'
```

---

## 10. Troubleshooting

| Symptom | Diagnosis | Fix |
|---------|-----------|-----|
| `tutor-api` unhealthy | `docker compose logs tutor-api` | Check DB connectivity, migration version |
| `db` unhealthy | `docker compose logs db` | Check disk space, volume permissions |
| `llm-gateway` unhealthy | `docker compose logs llm-gateway` | Check provider keys, network |
| `migrate` exits non-zero | `docker compose logs migrate` | Check Alembic error, DB connectivity |
| Login fails | Check `users`/`user_credentials` tables | Verify account exists, password reset |
| Blank learner page | `docker compose logs frontend` | Check nginx config, `/learn/` proxy |
| Backup fails | `df -h`, `docker compose exec db pg_isready` | Disk space, DB connectivity |
| Container won't start | `docker compose ps`, `docker inspect` | Check for port conflicts, OOM |

### Useful commands

```bash
# See all logs
docker compose -f docker-compose.yml -f docker-compose.pilot.yml logs --tail 200

# Restart a single service
docker compose -f docker-compose.yml -f docker-compose.pilot.yml restart tutor-api

# Full stack restart (after VPS reboot or config change)
docker compose -f docker-compose.yml -f docker-compose.pilot.yml down
docker compose -f docker-compose.yml -f docker-compose.pilot.yml up -d

# Check disk usage
df -h
du -sh backups/
docker system df
```

---

## 11. Security Checklist

- [ ] `.env.pilot` exists with strong `POSTGRES_PASSWORD`, no committed secrets
- [ ] `SESSION_COOKIE_SECURE=true` when TLS is active
- [ ] `LLM_GATEWAY_PROVIDER` set intentionally (`fallback` = no external calls)
- [ ] No ads, analytics, session replay, or third-party tracking enabled
- [ ] Backups encrypted or stored on access-controlled media
- [ ] Pilot cohort list maintained separately from the application DB
- [ ] No real child data in logs, tests, or GitHub
- [ ] Synthetic data used for all smoke tests and verification

---

## 12. Restart After VPS Reboot

Docker Compose `restart: unless-stopped` handles container restarts.
After a full VPS reboot:

```bash
cd /opt/ai-tutor
docker compose -f docker-compose.yml -f docker-compose.pilot.yml up -d
./scripts/ops/smoke_test.sh
```

If the DB container fails to start, check `docker compose logs db` and the
volume mount. For a corrupted volume, restore from the latest backup.
