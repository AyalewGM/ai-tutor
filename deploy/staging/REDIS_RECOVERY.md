# Redis anonymous-volume recovery

Initial staging runtime on 2026-10-17 created an anonymous Redis /data volume.
All six services reported healthy, but inventory rejected the anonymous mount before
smoke tests. Redis's upstream image declares /data as a volume even with snapshot
and AOF persistence disabled. Compose must override it explicitly.

The fix mounts the project-scoped redis_data volume and adds only that exact name
to the existing allowlist. Foreign/anonymous volumes and externally backed drivers
remain rejected. PostgreSQL and proxy volumes are unchanged. Redis persistence stays
disabled; this volume is not a database backup.

## Existing failed first deployment

Do not merely edit release.env's SHA, dirty the checkout, or bypass inventory. After
review/merge, build the new exact main release using Build staging images and retain
the previous manifest securely. Use the emitted application digests and matching
clean checkout; preserve the existing database password and support-image digests.

The old guard also blocks stop, so recovery needs a bounded manual maintenance step:
use the fixed local Docker socket, project mihur-staging, /etc/mihur-staging/release.env
and this standalone compose.yml. Stop proxy, frontend, tutor-api, llm-gateway and
redis only. Leave db running; do not rerun migration or seed for this config-only fix.

Before removing anything, inspect the Redis container's project/service labels and
mounts. Record its one anonymous /data volume ID; assert it is the originally
observed ID and no other container uses it. Remove only the stopped Redis container
without -v, preserving its old volume. Confirm again that the recorded volume is
unattached and contains only disposable synthetic staging Redis data. Then remove
only that exact anonymous volume with docker volume rm (no force). Do not remove
mihur-staging_database, proxy_data or proxy_config. Never prune or use down -v.

Provide the operator the exact container/volume commands only after checking the
live inventory and reviewed release. Any discrepancy is a stop condition. If data
provenance is uncertain, retain the volume and halt recovery.

After the old anonymous volume is removed and release alignment is verified, run
control.py preflight, pull, start, smoke, metrics. start creates the named Redis
volume. Verify a second preflight succeeds with running containers. Full browser,
TLS, resource load and backup/restore acceptance remain separate.

No remote recovery was performed by author; local guard tests only. Docker Compose
validation and container lifecycle execution require CI/target evidence.
