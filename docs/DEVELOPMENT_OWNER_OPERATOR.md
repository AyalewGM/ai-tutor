# Development owner gate: installation proposal and exact-release operation

This is a development-only extension of the existing staging operator. It is not
a service, reviewer account or orchestration queue. No command below has been run
against the VPS by this change. An owner signing a policy or release is not an
independent technical reviewer; real, separately produced Codex evidence remains
required. Existing production/default six-signature validation stays in force.

## Required owner-controlled boundary

The owner must first review the exact implementation revision and its independent
Security/Engineering verdicts and CI. Enrollment is performed through the trusted
IONOS console or a separately owner-controlled connection. Do not use an
agent-accessible shell to assert that the agent no longer has root.

The signing key remains passphrase protected on an owner-only device, outside
this server, the agent machine and agent-accessible SSH agents. Do not reuse the
unlocked staging-inspection key. Only its public key and public detached release
signatures are transferred. No new Linux or reviewer account is required.

The independently verified SSH server fingerprint remains
`SHA256:u3DFEz6/ESWWukGThMlhqZdp6707zgMcfNxDpOFpAeY`. The authorization's
`host_sha256` instead means SHA256 of the stripped UTF-8 `/etc/machine-id` text,
currently `3ee0437dd6184c8f150d0530093391fe7499cce86999f3c1a2e67dc0daec1c4b`.
They identify different things and must not be substituted for one another.

## Exact privileged enrollment operations requiring owner execution

Do not run this block with an unspecified checkout. `REVIEWED` below denotes an
owner-verified, immutable checkout of the accepted implementation, whose file
hashes were compared with the accepted PR. It is not an environment variable that
the installed gate trusts. The owner supplies the literal path locally.

1. Create root-owned directories `/usr/local/lib/mihur-development-release` and
   `/etc/mihur-staging/development-owner`, mode `0755`. Create
   `/var/backups/mihur-content`, and its `owner-authorizations` child, root-owned
   mode `0700`. Create an empty root `0600` `owner-authorizations/operation.lock`
   during enrollment; unsigned requests do not create it. Do not remove existing
   backups or nonce receipts.
2. Copy these exact reviewed bytes, root-owned mode `0644`:

   | Reviewed source | Installed destination |
   |---|---|
   | `scripts/ops/development_release_authorization.py` | `/usr/local/lib/mihur-development-release/authorization.py` |
   | `deploy/staging/control.py` | `/usr/local/lib/mihur-development-release/control.py` |
   | `deploy/staging/development_release.py` | `/usr/local/lib/mihur-development-release/development_release.py` |

   Use `install -o root -g root -m 0644` for each copy, not an agent-owned symlink.
   The Python entrypoint is invoked explicitly with `-I -S -B`; it does not need
   an executable bit. The owner verifies all three installed SHA256 values.
3. Write compact canonical JSON without a trailing newline to
   `/etc/mihur-staging/development-owner/operator-pins.json`, root `0644`, with
   exactly `entrypoint_sha256`, `authorization_sha256`, `control_sha256` and the
   hashes of those installed files. The fixed loader reads the bytes, checks
   ownership/ancestors/link counts/hashes, and compiles the verified bytes; it
   does not load an unverified `.pyc` or candidate module.
4. Enroll root `0644` `policy.json` in that same directory. Its strict schema is
   defined by `development_release_authorization.POLICY_FIELDS`. Pin the actual
   owner's public `ssh-ed25519` key; verified repository `1367979340` and owner
   `22088298`; the fixed development URL, database/role and machine digest; an
   operation lifetime of at most one hour; runtime permission at most seven days;
   and `operator_pins_sha256`, the canonical JSON digest of `operator-pins.json`.
   Compare the owner/public-key fingerprint on the separate owner device and
   trusted console. A username, JSON field or prompt alone does not enroll an
   owner. Example/template values and fixture keys are not valid enrollment.
5. Restrict only the existing staging inspection authorized-key line whose
   fingerprint is `SHA256:6gJXneY2kh/lh3QGLrDLIwWw9l1pRAZqRBn4Bbu+s0o`.
   Preserve every other authorized key. Through the trusted console use a line
   prefix equivalent to:

   ```text
   restrict,command="/usr/bin/sudo -n /usr/bin/python3 -I -S -B /usr/local/lib/mihur-development-release/development_release.py ssh-request" ssh-ed25519 EXISTING_INSPECTION_PUBLIC_KEY
   ```

   `restrict` must disable PTY, forwarding and user RC execution on the installed
   OpenSSH version. Verify these restrictions through the trusted console. The
   fixed program never evaluates `SSH_ORIGINAL_COMMAND`; it consumes a bounded
   canonical JSON request from stdin. Restrict any other agent-held route to
   unrestricted sudo/root, Docker, policy/state files or release-environment
   administration. Do not assert that the boundary exists merely from a Boolean
   field. Keep the owner's independent administrative access working.
   Changing `authorized_keys` restricts new authentications; it does not revoke
   already authenticated SSH channels or existing forwarding. From the trusted
   IONOS console, preserve a working owner recovery connection, inventory actual
   agent SSH sessions/forwarding and authorized-key fingerprints, and terminate
   only the reviewed agent sessions. Verify that no other agent-held key,
   privileged runner or release credential retains unrestricted authority. Do
   not use a global process-kill command or automatically terminate connections.
6. Test the restricted inspection identity: arbitrary shell, file/SFTP/SCP,
   forwarding, interpreter and Docker commands must no longer work. A request
   containing only `{"mode":"inspect"}` may return fixed public deployment,
   candidate, database-cluster and image metadata; no private key, credentials,
   learner data, arbitrary path or command is available. A `check` or
   `execute-plan` request requires a real owner signature. Failed tests are a
   release hold; never weaken the restrictions to make the command succeed.

Root can replace local keys, verifier or state. If the agent still has root by
any route, this mechanism has **not** established authenticated owner authority.
No unit test can prove the absence of those live capabilities.

## Inert candidate and independent evidence preparation

Prepare a separate root-owned clean checkout at `/opt/mihur-staging-candidate`.
Both active and candidate must be standalone root-owned clones, including all
Git metadata with no symlinks, shared common directory, alternates, writable
entries or helper/filter/include/URL-rewrite configuration. Only the fixed HTTPS
origin and ordinary clone/branch configuration are accepted. Global/system Git
configuration, non-HTTPS protocols, external helpers and redirects are disabled.
It is data only before authorization: the collector parses literal AST/JSON and
hashes fixed files, and never imports candidate Python. Leave the active
`/opt/mihur-staging`, `release.env`, containers and existing accounts unchanged.
Create root-protected canonical `/etc/mihur-staging/development-candidate.json`
with exactly the desired `source_sha` and six `images` digest references. All
three application images must be under Mihur's existing GHCR staging repository,
labelled with that source SHA and already locally available for inspection. This
bounded Ontario plan does not change PostgreSQL/Redis/proxy images; they must
match the current release. Artifact preparation is not deployment authority.

Keep the candidate's current base-ref objects available for read-only ancestry
verification. Native CI checks resolve the current GitHub PR and current base
ref, require the base to be an ancestor of the candidate, and prove that the
GitHub test-merge tree equals the release head tree. They do not mistake
historical normalized `base.sha` metadata for the current base. Record head and
test-merge SHAs separately. Required exact-head `test`, `containers`, Semgrep,
Trivy and CodeQL checks must actually succeed from their pinned GitHub App IDs.
Missing CodeQL on an unprotected stacked base is a hold, not a waiver. The owner
can arrange default CodeQL execution for the development base without changing
production rules; a claimed success or skipped job is insufficient.

Capture real five-lane technical evidence for the exact source/package. The
owner must inspect its content and provenance; byte hashes/session labels alone
cannot prove that a Codex reviewer ran independently. Use the existing isolated
restore procedure, not restoration into the active database cluster. Store a
fresh root `0600` canonical record at
`/var/backups/mihur-content/development-restore-evidence.json` with exactly:

```text
schema: MIHUR_DEVELOPMENT_RESTORE_EVIDENCE_V1
created_at: integer UTC Unix timestamp
source_database: mihur_staging
database_cluster_id: actual pg_control_system system_identifier string
archive: /var/backups/mihur-content/<unique-hex-name>.dump
archive_sha256: actual archive SHA256
restore_verified: true (only after actual separate-cluster verification)
disposable_restore: true
```

The native gate requires that record to be no older than one hour and verifies
the root-only archive bytes, cluster identity and fixed backup location. Do not
manufacture it from a prompt or treat these field names as restoration evidence.
Private archives and operator inputs stay outside the API's public proof mount.

## One exact owner authorization and fixed execution

The owner independently reviews and signs the canonical authorization on the
owner-only device, with namespace `mihur-development-owner-release-v1`. It binds
the precise source/tree/package/runtime/evidence/policy digests, all immutable
images, database cluster/role, development machine/URL, exact ordered actions,
operation expiry, explicit runtime expiry and unique nonce. Public request
transport may be relayed by the agent; possession of that public signature does
not permit changing its subject or replaying its effects.

The read-only runtime projection also contains the original owner-signed
`authorization.json` canonical envelope and `authorization.sig` detached signature.
Runtime readers must authenticate those bytes and actual kernel bind mounts,
not merely image file ownership or a directory name.

The package digest is the existing publisher's canonical manifest payload hash,
excluding `review_evidence`. For publication its committed activation and bounded
standards acceptance must already be accepted; signing a pending package does
not promote it. No fabricated six-role signatures are inserted.

`ssh-request` accepts only `inspect`, `check`, or `execute-plan`. The latter two
require exactly `mode`, base64 `envelope`, base64 `signature`, canonical-object
`evidence` and five SHA256-to-base64 public `artifacts`. Total request size is
bounded by the verifier's `MAX_BYTES`; no remote filenames or commands exist.
The root-console form uses those four public-data file arguments instead. All
execution is serialized in the private nonce directory. Preliminary signature
verification authenticates the owner before expensive metadata/network checks;
it is not falsely labelled native context verification. Native target and fresh
GitHub evidence are then collected independently and verified again.

Only these fixed plans exist:

- `deploy`: reserve the nonce, revoke prior development content permission,
  stop the old application stack, fetch/check out the exact signed revision,
  preserve the existing DB secret while updating only release/image pins, and
  run existing pull/start-db/migrate/start controls. No content seeding occurs.
- `publish`: require the actual current signed source/images/runtime/cluster,
  reserve, issue a short provisional grant, invoke only the existing container
  publisher and synthetic learner probe, and extend to the signed runtime expiry
  only after the probe succeeds.
- `deploy` followed by `publish`: deploy first, re-inspect actual new source,
  image bytes/digests and database identity, then perform publication. A target
  image label alone is not runtime proof.
- `rollback`: revoke permission and metadata-disable only the exact signed
  package on the current signed source/images. It does not restore a database,
  alter learner histories, or switch images. Restoring prior images requires a
  fresh `deploy` authorization for those exact artifacts.

Nonces are reserved before first release effects and never cleared on uncertain
outcomes. Failure revokes the runtime grant. If filesystem revocation fails, the
gate attempts to stop only the previously inspected exact API container ID,
image and source; it never stops a wildcard collection or restores data. If both
mechanisms fail, the result is an explicit emergency hold requiring owner-console
intervention, not a claim of successful revocation. Provisional permission is
capped at five minutes and operation expiry even when the signed runtime period
is longer. Runtime permission checks re-read revocation and expiry; ordinary
learner requests never consume an operation nonce.

No failed or interrupted plan is blindly retried. Inspect actual state, obtain
a fresh owner-signed continuation/rollback and repeat mandatory preflight.
Successful command execution is not independent Muse acceptance or verified
Ontario student availability. The actual approved-package learner journey and
all applicable privacy/consent holds remain separate release requirements.
