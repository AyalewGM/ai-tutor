# Staging deployment workflow — reviewed rollout required

`Deploy staging` provides one hosted workflow to plan a release and relay an
already prepared, owner-signed **deploy-only** request to the installed native
operator. Planning is the default and needs no VPS credential. Execution is off
unless the protected environment explicitly enables it. This PR does not enroll
credentials, alter the VPS, or authorize production or content publication.

## What this implements, and what it does not

The workflow identifies frontend, backend, database, content and unknown/operator
changes from the actual current release to the selected main commit. It downloads
the exact successful image-build run's current-attempt artifact, not a mutable tag
or manually copied image digest. Deletions and both sides of renames are included.
Classification is advisory: a frontend path may still change authentication,
privacy or learner behavior. It must never automatically waive reviews.

For execution, it verifies the signed release matches the prepared candidate and
build manifest, calls the native gate's `check`, then `execute-plan` exactly once,
re-inspects the deployed SHA and images, and checks HTTPS `/healthz`,
`/backend-health` and `/`. A successful summary reports the actual release; a
planning result never claims deployment. Browser and learner acceptance remain
Muse QA work.

The current native operator has **no frontend-only deployment primitive**. It
requires all three application images to carry the same source SHA and always
runs the migration service. Its five-role review, owner signature, host isolation,
backup/restore and expiration checks still apply even for frontend changes.
This workflow does not silently remove them. The native `rollback` operation
revokes content permission; it does not roll back images. Automatic image or
schema rollback is therefore deliberately unavailable here.

Consequently this is an orchestration improvement, **not yet an end-to-end
one-click routine release**. Candidate preparation, genuine evidence assembly,
isolated restore and owner signing remain prerequisites. Removing those from
routine frontend releases requires a separately reviewed native authorization
policy and a frontend-only execution mode. An environment approval alone is not
a substitute for the owner signature under today's policy.

## One-time owner setup (after independent review)

1. Create `staging-deployment`, restrict it to protected `main`, require an owner
   reviewer and disallow self-review where available. Do not activate before the
   installed native verifier and its pins match the reviewed implementation.
2. Establish the owner/agent privilege boundary using
   `DEVELOPMENT_OWNER_OPERATOR.md`; a forced command does not revoke old sessions.
   Keep the independent owner console working.
3. Enroll only the restricted inspection SSH credential in environment secret
   `STAGING_INSPECTION_KEY`. The script checks its fingerprint. Do not use the
   owner's administrative or signing key. If the existing inspection private key
   cannot be located, leave execution disabled; rotate/enroll a new restricted
   identity through a reviewed change to the pinned client fingerprint.
4. Store a single independently verified known-hosts entry for `40.160.97.126` in
   `STAGING_KNOWN_HOSTS`. Its fingerprint must match the pinned server key.
   `ssh-keyscan` output alone is not identity verification. Strict verification
   stays enabled; no accept-new or insecure TLS option exists.
5. Ensure the hosted runner can reach SSH under an explicitly approved network
   policy. The existing owner-IP-only firewall rule will block hosted runners.
   This PR does not open SSH globally or change firewall rules. A restricted
   tunnel/static-egress design needs separate setup if required.
6. Set environment variable `STAGING_DEPLOY_ENABLED=true` only after testing the
   restricted identity and reviewing the above. No private signing key enters
   GitHub, the runner or the VPS.

## Per-release operation

1. Merge reviewed code. Wait for exact-main CI/AppSec, then run **Build staging
   images**. Note its numeric run ID. Build completion does not deploy anything.
2. Select **Deploy staging → plan**, on main, supplying the actual active release
   SHA and build run ID. Review its change categories and maintenance implications.
   If main advanced, build the new reviewed main or stop; do not relabel images.
3. Prepare the exact candidate and existing six image pins; preserve infrastructure,
   database password and MFA key. Assemble real reviewer artifacts. Finish the
   access-boundary checks before entering the one-hour restore/signing window.
4. Execute the existing isolated backup/restore drill from the staging README;
   compare schema, revision, per-table counts and primary-key row-content hashes.
   Never manufacture a `restore_verified` receipt or restore over the active DB.
5. On the owner-only Mac, sign the exact native authorization with actions
   `["deploy"]`. Package its envelope, signature, evidence and artifacts into the
   native canonical `execute-plan` JSON (maximum 65,536 bytes). This input is
   public authorization evidence, not a place for secrets or learner records.
6. Select **Deploy staging → deploy** with the same active SHA, build ID and signed
   request. The protected environment reviewer checks this exact release. The
   native gate rejects expired signatures/restore receipts, changed candidates,
   failed checks and replayed nonces. Approve within their validity window.
7. Confirm the final deployed SHA and public smoke results, then perform Muse
   browser smoke testing. The workflow never seeds or publishes learning content.

## Failure and recovery

A failed plan/check has not authorized deployment. If execution was attempted,
connection loss or timeout is an uncertain outcome, not proof of no changes.
Do not use GitHub's rerun button with the same authorization. Inspect through the
owner console, record actual source/images/migration revision and obtain a new
reviewed authorization before any continuation. No automatic SSH retries occur.
After migration, assess backward compatibility before changing images. Never
restore a database in place, downgrade automatically or remove source volumes.

## Validation scope

Repository tests use synthetic Git, GitHub, SSH and HTTP seams. They verify
classification, exact artifact and signed-request binding, refusal before mutation,
execution ordering, no replay/retry, and post-deploy identity checks. They do not
prove network reachability, environment protection, private-key custody, live
restore integrity, native signature validity or live deployment success. A real
owner-authorized staging exercise remains a rollout requirement.
