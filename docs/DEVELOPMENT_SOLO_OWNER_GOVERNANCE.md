# Solo-owner governance for the Ontario development release

**Status: owner accepted the development-only governance model; implementation is
not installed or operationally authorized.** This PR implements the detached owner
verifier, native development execution adapter and runtime package-permission
adapter for review. No real key, protected policy, runtime grant, operator pins or
release authorization is provisioned by this source change. No deployment,
publication, learner modification or activation is authorized by merging it.
Production/default validation retains the existing six-signature contract.

## Which requirements change

The six Ed25519 roles and distinct non-author principals are an enforced **project
security contract**, introduced by publisher commit
`16fe5d90fbe42a528f5775271f3dbacf5f395531`. `CONTENT_PUBLISHER.md` describes it as a
deliberate new release contract. Inspected issues
[#462](https://github.com/AyalewGM/ai-tutor/issues/462),
[#433](https://github.com/AyalewGM/ai-tutor/issues/433) and specialty charters require
independent technical review and owner authorization, but do not prescribe six
external cryptographic identities. No inspected external source establishes that
six-signature mandate; this finding is limited to inspected evidence, not a legal
opinion or waiver of an undiscovered contract.

The accepted development-only model preserves five real, separate, non-author
Codex reviews: Math, Pedagogy, Standards, Security and Muse QA. One owner-held
detached signature accepts their exact evidence and authorizes a bounded release
plan. Agent reviews are not human approvals, GitHub `APPROVED` events or
independently authenticated specialist signatures. A sole owner cannot approve
their own GitHub PR. No shared main/production branch rule is relaxed and no
approval event is fabricated.

Child privacy, parental consent, school agreements where applicable and other
holds in `docs/security/PILOT_COMPLIANCE_CHECKLIST.md` and
[#436](https://github.com/AyalewGM/ai-tutor/issues/436) remain. Owner release
acceptance cannot self-certify legal compliance or replace a required external
review. Ontario's partial-practice standards scope, no full coverage credit and
no mastery/progression/reward credit remain mandatory.

## Native trust boundary: required before use

A repository file, username, `github.actor`, prompt or local approval JSON cannot
prove human authorization when an agent has equivalent credentials. GitHub
exposes deployment approval through authenticated APIs, so UI approval is not a
human-presence boundary if an agent holds an equally capable token.

The owner must enroll and independently verify all of the following through the
trusted IONOS console or a separately owner-controlled privileged connection:

1. A passphrase-protected owner signing key on an owner-only device, outside agent-readable files and every agent-accessible SSH agent. Do
   not reuse the unlocked staging-inspection key. No additional reviewer account,
   signing service or persistent runner is required.
2. The authenticated repository/owner identities must match pinned numeric IDs
   `1367979340` / `22088298` for `AyalewGM/ai-tutor`. Accept the exact reviewed
   operator/verifier SHA and enroll the owner's public key. Those identifiers in
   an agent-controlled file alone are not authentication.
3. Install the fixed native entrypoint at
   `/usr/local/lib/mihur-development-release/development_release.py` with its
   root-owned `authorization.py` and `control.py` siblings. Protected operator pins
   bind their actual installed bytes, and the policy's `operator_pins_sha256`
   binds those pins to the owner-signed authorization. Paths, modes, native
   preflight and action allowlists remain part of the independently reviewed
   operator adapter; never execute a checkout script with broad sudo authority.
4. Native policy/context/state are under
   `/etc/mihur-staging/development-owner/`; private replay/state directories are
   root-owned `0700`. Policy/context files are single-link regular root-owned
   canonical JSON, `0644` or `0600`, below descriptor-pinned protected ancestors.
5. Remove the agent's ability to replace the verifier, pins, policy, context or
   replay state. **Current broad staging sudo/root access fails this condition.**
   Restrict or disable only the existing inspection public key while preserving
   the owner's other authorized keys. A fixed `ssh-request` forced command may
   expose only independently reviewed read-only metadata operations; never
   arbitrary shell, Python, paths, Docker exec/socket access or sudo. Until that
   restricted path is verified, use the owner console and disable broad agent
   access. Inspect other credentials for root/deployment/approval bypass power.

No server configuration is changed by this PR. Root-owned files do not protect
against an agent retaining root. Neither unit tests nor a boolean in a policy
prove that the live capability boundary exists. If it cannot be established,
authenticated solo-owner execution remains blocked.

## One detached owner authorization

On the OWNER-ONLY device, create a passphrase-protected key and sign exact
canonical authorization bytes. The agent must not run these commands or receive
the private key or passphrase:

```bash
ssh-keygen -t ed25519 -f /OWNER-ONLY/mihur-development-release -C mihur-owner-release
ssh-keygen -Y sign -f /OWNER-ONLY/mihur-development-release \
  -n mihur-development-owner-release-v1 /OWNER-ONLY/release-authorization.json
```

Use a nonempty passphrase. Transfer only the public key and detached signature.
No private key, passphrase or forwarded SSH-agent socket may enter an agent
workspace or CI. Tests generate fixture-only keys inside a disposable namespace;
they are never release identities and must never be enrolled.

Canonical JSON is UTF-8 with sorted keys, compact separators and no duplicate
keys, nonfinite numbers or trailing bytes. Strict V1 field sets are defined by
`scripts/ops/development_release_authorization.py`; unknown fields are rejected.
The envelope binds:

- Numeric repository/owner IDs, repository name and the current policy SHA256.
- Exact source commit/tree, package and runtime digests, all six immutable
  API/gateway/frontend/PostgreSQL/Redis/proxy image references, and the complete
  five-lane technical-evidence bundle digest.
- Literal `development`, `https://dev.mihureducation.com`, database and role
  `mihur_staging`, plus the actual PostgreSQL cluster system identifier.
- `host_sha256`: the native machine-ID SHA256
  `3ee0437dd6184c8f150d0530093391fe7499cce86999f3c1a2e67dc0daec1c4b`, defined as
  `SHA256(Path('/etc/machine-id').read_text().strip().encode('utf-8'))`.
  This is not the independently verified SSH ED25519 host-key fingerprint
  `SHA256:u3DFEz6/ESWWukGThMlhqZdp6707zgMcfNxDpOFpAeY`; strict SSH verification
  retains that separate pin.
- An exact ordered `deploy`, `publish`, `deploy` then `publish`, or `rollback`
  plan; issue time, operation expiry (maximum one hour), a fresh random 256-bit
  nonce and a distinct owner-signed `runtime_expires_at`.

The policy additionally bounds `max_runtime_seconds` to at most 604800 seconds
(seven days). The operation verifier requires
`expires_at <= runtime_expires_at <= issued_at + max_runtime_seconds`. A one-hour
operation token does not disable authorized ordinary learner reads after an
hour; the separate, bounded runtime permission remains revocable until its own
expiry. Extending it requires fresh owner authorization.

`package_sha256` is the existing publisher digest of the actual manifest excluding
`review_evidence`, using `content_publishing.canonical()` / `digest()`. It is not
an arbitrary JSON hash. No token promotes pending/provisional content: the actual
package must explicitly retain accepted partial-practice standards bounds and
staging activation; source/tree/runtime bind generator bytes, modes and seeds.

The expected native context comes from actual reviewed files, immutable images,
machine/database identity and fresh authenticated exact-head CI checks with
expected App IDs. A prompt, ambient `APP_ENV`/`DATABASE_URL` or agent assertion is
not authority. Pure `verify()` cannot prove that a caller-supplied context is
trusted. The standalone CLI remains verify-only and performs no release effects;
the fixed native operator adapter must separately enforce preflight and execution.

The technical bundle requires exact source/package identity, producing session
IDs and five distinct non-author reviewer sessions, each with scoped verdict and
SHA256 of a nonempty bounded real transcript artifact. Deterministic checks prove
subject binding, completeness and artifact integrity, not that arbitrary session
labels occurred or independent judgment was sound. Preserve real captured review
sessions and exclusions; the owner must examine and sign acceptance of that
bundle. Never invent missing evidence or treat agent-provided CI JSON as an
authenticated GitHub check.

## Operation replay and runtime permission are different

The native adapter cryptographically verifies the owner envelope, performs actual
native reinspection and atomically reserves its nonce **before the first effect**.
`reserve_nonce()` locks the protected directory, uses `O_EXCL | O_NOFOLLOW`, and
fsyncs the record and parent. A nonce cannot authorize another action or retry.
A crash, partial write, fsync failure or uncertain operation burns the nonce.
Inventory first, then obtain a fresh signed continuation or rollback; never erase
consumption state to retry. If nonce state is lost or rolled back, revoke or rotate
the owner policy before any operation resumes; never reinitialize nonce state as
an approval-recovery shortcut.

After verified native publication authorization, the host issues a protected
`MIHUR_DEVELOPMENT_RUNTIME_GRANT_V1` receipt binding policy hash, verified envelope
hash/nonce/time, original owner-signed `owner_runtime_expires_at`, actual runtime
expiry and exact release context. During initial QA the native adapter may shorten
actual permission to the minimum of that owner limit, operation expiry and five
minutes from verification. Only a passing learner probe may extend actual
permission up to the original signed limit; no new authority or general renewal
mechanism is introduced. Runtime always requires
`now < runtime_expires_at <= owner_runtime_expires_at <= verified_at + max_runtime_seconds`.
API mounts only
root-owned `policy.json`, `context.json`, `grant.json` as a read-only `0755`
`/run/mihur/development-owner` directory and separately binds the actual native
machine ID read-only at `/run/mihur/host-machine-id`. The directory also contains
the exact original `authorization.json` and detached `authorization.sig`.
Admission checks genuine procfs mount metadata for exact read-only host bind
roots `/etc/mihur-staging/development-owner` and `/etc/machine-id`; image-rootfs,
tmpfs/anonymous-volume lookalikes, missing or nested replacement mounts deny.
Unsupported OS/architecture/filesystem layouts fail closed. No host socket or owner
private key is mounted. File ownership is meaningful only after agent root access
has actually been removed.

`content_publishing.validate()` keeps its complete six-signature implementation.
The explicit `authorize_package()` caller selects development permission only
when the fixed native mounts exist. No mount uses the default validator; partial,
malformed, symlinked, writable or non-read-only development state denies without
fallback. The development adapter first performs structural checks, then requires
accepted partial-practice staging disposition, empty six-role `review_evidence`
(no fabricated reviewers), exact package/runtime digests and the current protected
policy/grant/context. Grant actions must include `publish`: deploy-only or
rollback authorization grants no package permission.

Every publication, selection and scoring permission revalidates those files,
policy revocation, grant state and runtime expiry without positive caching. It
also cryptographically verifies the original owner SSHSIG v1 Ed25519 proof over
the exact canonical envelope and namespace, current policy, release bindings and
owner-signed runtime limit. Merely image-baked root-owned read-only JSON cannot
supply host admission or replace that proof. The implementation follows
[OpenSSH PROTOCOL.sshsig](https://github.com/openssh/openssh-portable/blob/master/PROTOCOL.sshsig)
with bounded decoding, supported hash algorithms, exact key/namespace and no
trailing fields; API verification uses the existing cryptography dependency,
without a runtime OpenSSH executable. It
reads actual database identity using `current_database()`, `current_user` and
`pg_catalog.pg_control_system().system_identifier`; environment variables, DSN
text and database names alone are insufficient. API code does not execute OpenSSH,
consume one-use operation tokens or claim to re-inspect Docker itself: immutable
image/source attestation belongs to the protected native context, while API
checks its actual generator/runtime bytes, machine ID and database cluster.

## Release sequence and remaining operator gates

1. Independently review this exact combined implementation and deterministic
   rejection tests; retain real Math/Pedagogy/Standards/Security/Muse evidence.
   Production/default approvals remain unchanged; no self-`APPROVED` is fabricated.
2. Owner performs the native enrollment and capability-boundary ceremony above,
   verifies installed operator pins and read-only runtime mounts, and confirms
   the inspection credential cannot obtain broad root or signing authority.
3. Use only an explicitly reviewed development-only candidate-image path for the
   exact #501/#505 source SHA. It must build privately without deployment secrets
   before the final owner grant, so that the grant binds final image digests.
   Existing production/main image workflows and protections remain unchanged;
   this source change does not perform a registry build.
4. Recollect exact-SHA technical reviews and mandatory CI/AppSec/CodeQL; verify
   actual isolation and fresh backups/restore evidence. Present the exact source,
   package, images, host/database, actions and evidence tuple for one final owner
   authorization. Neither accepted governance nor a previous activation condition
   replaces that exact-release authorization.
5. Execute only the signed plan through the fixed native adapter. Verify actual
   approved-question selection, rational submission/feedback, no mastery credit
   and access denials on the deployed development SHA before claiming student
   availability. Preserve earlier conditional activation authorization without
   widening its scope.

Native enrollment, privileged-boundary verification, final artifacts and exact
owner authorization remain outstanding. This implementation must not be reported
as installed, operationally authorized or evidence of student availability.

## References

- [GitHub deployment approval API](https://docs.github.com/en/rest/actions/workflow-runs#review-pending-deployments-for-a-workflow-run): capable API tokens are not human-presence proof.
- [OpenSSH detached signing](https://man.openbsd.org/ssh-keygen.1): namespace-separated owner signing and allowed-signers verification.
- Project holds remain in `CONTENT_PUBLISHER.md`, the specialist charters and
  `PILOT_COMPLIANCE_CHECKLIST.md`; no legal certification is claimed.
