# Issue #302: dedicated 2 GB IONOS staging

Status: PREPARED, NOT DEPLOYED. Runtime feasibility, remote isolation, staging smoke,
backup/restore and independent acceptance are NOT VERIFIED. Links: #278, #298, #301.

## Purpose and architecture

As DevOps, prepare a small private environment where Muse can test the real container
stack with synthetic identities before any family access. Acceptance is #302 plus
independent review of #298 evidence, not merely successful configuration validation.
Source basis: repository Dockerfiles, Compose, pilot runbooks and CI at
`e84a7394a4c52eeee84be8c53ef29dbe6d817e1e`.

Existing stack: PostgreSQL 16, Redis 7, Python API and separate Python LLM gateway,
Vite-built static frontend served by nginx. Existing pilot deploy builds on-host;
its restore script drops the selected database. Neither is appropriate here.
**Do not use scripts/ops/{deploy,backup_db,restore_db,smoke_test}.sh for this stack.**
No production files, application interfaces or pedagogical behavior change.

This is deliberately a **standalone Compose file, not an overlay**: merging base
files can retain public ports, builds, pilot env files or database volume references.
Use only deploy/staging/compose.yml, fixed project mihur-staging and control.py.
The DB URL is fixed to db/mihur_staging with a fresh staging-only credential.
There are no external volumes, host database paths, provider credentials, SMTP or
payment credentials. An internal network denies provider egress. The actual gateway
container runs deterministic fallback; this does NOT validate a paid provider.
OCR is synthetic stub. Secure cookies stay enabled.

Only Caddy publishes a port: **127.0.0.1:8443**. TLS uses an internal CA, accessible
through an owner/QA SSH tunnel. No domain/public HTTP port or family access required.
No Docker socket is mounted. JSON logs rotate at 5 MiB x 2 per service.

## Resource budget (limits, NOT measurements)

| Service | RAM cap MiB | CPU cap |
|---|---:|---:|
| PostgreSQL | 320 | 0.50 |
| Redis (32 MiB data max, noeviction) | 64 | 0.15 |
| LLM gateway, one worker | 192 | 0.35 |
| API, one worker | 448 | 0.75 |
| nginx frontend | 64 | 0.20 |
| Caddy | 64 | 0.20 |
| Steady-state total | **1152** | **2.15** |

CPU caps are ceilings, not reserved CPU; actual vCPU allocation/steal and performance
remain unknown. Nominal 2 GB leaves roughly 0.8 GB for kernel, Docker and bursts.
Migration/seed cap 448 MiB; execute with application stopped, never concurrently.
Preflight requires nominal 2 GB, initial available RAM >= 1.4 GB, >= 1 GB swap and
>= 10 GiB free Docker disk. Swap is emergency headroom, not a capacity solution.
No image builds, browser installation, local models or heavyweight monitoring on VPS.
No assertion that these caps are sufficient until representative load is measured.

## Secure access and isolation gate (before deployment)

Owner supplies host identity/IP, SSH username, pinned SSH host-key fingerprint and
an approved secure SSH-key channel. Do not paste passwords/private keys into chat or
GitHub. Access must be to the **dedicated nonproduction VPS only**. Read-only inventory
first: IONOS server ID/account, machine ID, Docker containers/volumes/networks, system
services, mounts, listening ports and credential scope. Host must contain no production
services, mounts, backups or credentials, including outside Docker. A name/label alone
is NOT isolation proof. Record sanitized evidence under #298; stop on ambiguity.

After owner/DevOps verification, create /etc/mihur-staging (root-owned, mode 0700).
Create isolation.json root-owned mode 0600 with:

```json
{
  "environment": "staging",
  "machine_id": "ACTUAL_ETC_MACHINE_ID",
  "dedicated_nonproduction_host": true,
  "synthetic_data_only": true,
  "no_production_credentials_or_mounts": true,
  "owner_inventory_evidence": "Issue #298 evidence URL and verified IONOS server ID"
}
```

This attests the reviewed inventory; the script cannot independently prove cloud-account
ownership or absence of secrets outside Docker. It additionally rejects foreign Docker
containers/volumes, external volume drivers, unexpected mounts, remote Docker contexts,
mutable images, manifest overrides and a dirty/wrong-SHA checkout. Every action reruns
preflight. Run during an exclusive maintenance window (no concurrent operators).

IONOS firewall: allow SSH only from owner/QA source IPs; deny other unsolicited inbound
IPv4 AND IPv6. Verify host firewall likewise, preserving SSH before changes; do not
blindly flush rules. Inspect Docker rules because published ports can bypass UFW.
Verify 3000/8000/8001/8002/5432/6379/8443 are unreachable externally. No firewall
mutation is automated here. Provision swap manually only after checking free disk.

## Images and release manifest (off-host)

From the reviewed release SHA on a trusted build host, build these three images using
Dockerfile, services/llm_gateway/Dockerfile and frontend/Dockerfile respectively. Tag
with the full SHA and label org.opencontainers.image.revision with that SHA. Push to
a private owner-approved registry; record immutable RepoDigests and build/CI provenance.
Use a scoped pull-only registry token on staging, entered securely with password-stdin.
Select scanned PostgreSQL 16-alpine, Redis 7-alpine and Caddy 2-alpine digest references.
Do not buy registry services or publish images publicly without owner authorization.

Copy staging.env.example to /etc/mihur-staging/release.env (root-owned mode 0600).
Fill all image digests and the full release SHA; generate a fresh 32-byte hex password
with a secure secret manager or `openssl rand -hex 32`. Never reuse production secrets.
Keep prior manifests securely outside Git for rollback, preserving the DB password.
Do not run/attach `docker compose config` without --quiet or raw docker inspect/env:
they expose credentials. These files and full logs must never be committed/uploaded.

## Deployment sequence (only after secure access and isolation verification)

Checkout the reviewed release SHA on staging with a clean working tree. Use a root-owned
checkout when running through sudo; do not add global Git safe.directory wildcards.
Each command below runs from the checkout. No command builds an image or addresses pilot.

```sh
sudo python3 deploy/staging/control.py preflight
sudo python3 deploy/staging/control.py pull
sudo python3 deploy/staging/control.py start-db
sudo python3 deploy/staging/control.py migrate
sudo python3 deploy/staging/control.py seed
sudo python3 deploy/staging/control.py start
sudo python3 deploy/staging/control.py smoke
sudo python3 deploy/staging/control.py metrics
```

For updates: preserve a staging-only backup first, `stop` the application, then pull,
migrate, seed (only if required), start and smoke. Never run migration concurrently
with API, or downgrade schema automatically. Seed is repository seed_sprint1.py;
it creates synthetic curriculum content, not proof of Ontario/Maryland pilot coverage.
Muse creates only synthetic parent emails in example.invalid and anonymous child
nicknames; no invitations, real child records or copied production snapshots.

On QA workstation: `ssh -N -L 8443:127.0.0.1:8443 STAGING_SSH_ALIAS`.
Extract only Caddy's public root certificate using docker compose cp from
/data/caddy/pki/authorities/local/root.crt through the verified stack. Verify fingerprint
out-of-band. Trust that CA in a dedicated test browser/profile (never share its private
key). Use https://localhost:8443. curl --cacert verifies healthz/backend-health; never
count a curl -k result as verified TLS. Internal smoke intentionally does not claim TLS
or browser verification. On first startup Caddy CA setup/health remains a runtime gate.

## Muse handoff and measured evidence

Muse independently executes browser journey under #300 and #298 against that tunnel.
Include parent registration/login, synthetic student, practice/hints, independent
assessment isolation, deterministic mastery and parent progress. Exercise gateway
/v1/render (not just /ready) with synthetic prompts and verify fallback result. Separately
verify Redis PING, all container health, HTTPS/cookies, frontend routes, and error paths.
A paid provider would need a separately reviewed egress/secret configuration and test;
this isolated fallback baseline does not establish external-provider readiness.

Capture UTC timestamp, release SHA, all image digests, resource IDs (sanitized), executed
commands, expected/observed results, test counts and reviewer. Run metrics at idle,
during 1 then 3 concurrent synthetic sessions and after 15 minutes; record peak RAM,
CPU, disk growth, swap-in/out (`vmstat 1 60`), restarts and OOM events (`journalctl -k`).
Polling samples are not exact peaks: state interval. Stop load on OOM, sustained swap,
<256 MiB available RAM, increasing restarts, errors or unacceptable latency. Record actual
latency and agree SLA with Engineering Lead; do not invent a passed performance target.
Review logs for secrets/test tokens before attaching evidence. No agent signoff implied.

## Non-destructive backup/restore drill (#298)

Run only after recording source project/volume and synthetic provenance. Stop application
writers using control.py stop. Rerun preflight. Use the fixed Compose invocation from
control.py (local socket, fixed project, explicit env/config) for pg_dump of **only**
mihur_staging as mihur_staging. Store custom-format archive in a root-only staging backup
directory outside Git; `pg_dump -Fc --no-owner --no-privileges` and SHA-256 the file.
Never source .env.pilot or run the existing restore_db.sh.

Preview exact commands/IDs in #298 before execution. Create a uniquely named NEW
standalone postgres container using the SAME DB digest, `--network none`, no published
ports, no host mounts, and a fresh tmpfs /var/lib/postgresql/data (size=256m) with 320m
container RAM limit. Use only synthetic local trust authentication for this networkless
throwaway container; no credentials copied. Assert name does not exist before creation.
Create a new empty `mihur_restore_<timestamp>` DB. Stream archive with docker exec -i
and `pg_restore --exit-on-error --no-owner --no-privileges` into that new target only.
No --clean, DROP, overwrite, schema downgrade, production source or source restoration.
Keep source application writers stopped for consistent comparison, and run drill with all application
services stopped to fit RAM. Container tmpfs is disposable and not a recovery strategy.

Compare schema/Alembic revision, per-table row counts AND ordered primary-key row-content
hashes for every application table; include the synthetic fixture rows and restored
foreign-key constraints. Matching row counts alone are insufficient. Record backup SHA,
archive size, restore exit status/duration and integrity comparison. Failed comparisons
are FAIL; do not silently accept partial restore. Stop and retain the disposable container
for inspection; cleanup requires an explicit scoped preview and cannot touch source.
While the drill container exists, control.py intentionally rejects the foreign container:
remove only that recorded disposable container after authorized cleanup, then rerun
preflight before resuming staging. Full drill commands/evidence are pending target review.

## Rollback and stop conditions

If a deployment fails, stop proxy/API via control.py stop and retain DB/volumes/evidence.
Before migration, rollback is prior reviewed checkout plus prior image manifest, followed
by start/smoke. After migration, restore no data in place: Engineering Lead must verify
old code is compatible with current schema before an image-only rollback. Otherwise
leave staging stopped and prepare a NEW isolated environment/restore target for review.
Never use deploy.sh for rollback (it fetches branch head), alembic downgrade, down -v,
docker system prune or restore over the current database. Production remains out of scope.

## Evidence and Definition of Done

| Gate | Current status |
|---|---|
| Local safety guard tests | See PR execution evidence |
| Compose validation / exact-head CI / AppSec | Pending GitHub runs |
| VPS identity, CPU/RAM/disk inventory | BLOCKED: secure access not supplied |
| Measured 2 GB feasibility | NOT MEASURED |
| Remote deployment, TLS and full gateway smoke | NOT EXECUTED |
| Fresh-target backup/restore integrity | NOT EXECUTED |
| Muse / Engineering Lead / PO / PM acceptance | PENDING |
| Production deployment / external family access | NOT AUTHORIZED |

PR preparation is not release approval. Publish meaningful transitions in #302/#278,
attach execution evidence to #298, and link independent acceptance in #301.
