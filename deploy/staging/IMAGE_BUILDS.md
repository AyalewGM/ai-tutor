# Build staging images with GitHub Actions

This workflow publishes images; it does not SSH, migrate, seed, deploy, or enable
family access. Use the separate staging README for isolation and runtime gates.

## One-time owner setup

1. Merge the reviewed `Build staging images` workflow to main.
2. In Settings → Environments, create `staging-images`, restrict deployment branches
   to main, and configure owner approval where your GitHub plan supports it.
3. Confirm these GHCR package names are unused (new packages default to private), or
   inspect each existing package and confirm its visibility is **private**:
   `ghcr.io/ayalewgm/ai-tutor/staging-api`, `staging-gateway`, `staging-frontend`.
   The latter two use the same `ghcr.io/ayalewgm/ai-tutor/` prefix.
   Existing packages must grant this repository Actions write access. Do not make
   packages public to resolve permission errors.
4. Add environment variable `STAGING_GHCR_PRIVATE_CONFIRMED=true` only after that
   inspection. This is an owner attestation, not an automated visibility check.
   Recheck visibility before subsequent runs if package settings have changed.
5. Confirm the VPS is x86-64 (`uname -m` returns `x86_64`). This initial workflow
   builds `linux/amd64` only; ARM requires a reviewed platform change.

Publishing uses the automatically supplied GITHUB_TOKEN with packages:write.
No Docker Hub account, registry publishing PAT, SSH key, or VPS secret is needed
in Actions. GitHub Actions/package storage and transfer quotas still apply.

## Build a release

1. Wait for CI and AppSec Baseline **push runs on the main commit** to succeed.
2. Actions → Build staging images → Run workflow → branch **main**.
3. Approve the environment if configured. The workflow checks both required runs
   for the dispatch SHA; PR-only success does not substitute for this check.
4. Wait for the entire job to succeed. Download its `staging-images-*` artifact.
   `application-images.env` contains the release SHA and three immutable image
   references. The JSON files contain build metadata. Record the workflow run URL
   alongside the manifest. No database password is included.
5. Inspect the three GHCR packages to confirm private visibility after first push.

The workflow builds each Dockerfile with its appropriate context on GitHub's runner.
Images are tagged with the full source SHA, but **deploy only the emitted digest**:
rebuilding a SHA can change dependencies/base images and therefore its image digest.
A failure after one push may leave partial package versions; there is no complete
release until all three builds and artifact upload succeed. Rerun after diagnosis;
never combine incomplete outputs from different runs.

## Pull on the dedicated staging VPS

Use a securely supplied personal access token (classic) limited to `read:packages`,
with access to these private packages. Authenticate as root because control.py runs
Docker as root. From a Bash session, without tracing or command-history secrets:

```bash
read -rsp 'GHCR pull token: ' GHCR_PULL_TOKEN; echo
printf '%s' "$GHCR_PULL_TOKEN" | sudo docker login ghcr.io -u YOUR_GITHUB_USER --password-stdin
unset GHCR_PULL_TOKEN
```

Docker stores login credentials in root's Docker configuration unless a credential
helper is configured. Protect that file; never upload it or place it in Git.

Copy the three digest references and release SHA into the root-only
`/etc/mihur-staging/release.env`. Add reviewed PostgreSQL, Redis and Caddy digest
references and the staging-only database password from the existing env example.
The downloaded application manifest is deliberately **not** a complete release.env.
Use a clean checkout of that exact SHA, then follow README preflight/pull/deploy.
Do not run docker compose config without --quiet (it exposes the DB password).

## Limits and remaining gates

Successful image builds are not container smoke tests, vulnerability clearance,
backup/restore validation or deployment authorization. The existing repository
AppSec run is a prerequisite; it is not a scan of the newly built image artifacts.
Dependencies/base image tags in the existing Dockerfiles remain mutable.
No SSH access is configured. dev.mihureducation.com routing/TLS remains a separate
staging change. Real parents/children are outside the synthetic staging baseline.

References: GitHub Docs, “Publishing Docker images” and “Working with the Container
registry” (GITHUB_TOKEN publishing, private-by-default packages, digest pulls and
read:packages authentication).
