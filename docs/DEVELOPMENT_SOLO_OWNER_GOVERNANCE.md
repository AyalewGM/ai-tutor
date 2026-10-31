# Proposed solo-owner governance for the Ontario development release

**Status: PROPOSED / INACTIVE.** This PR introduces a verification primitive and a
reviewable policy design. No existing publisher, learner-runtime validator,
deployment entrypoint or workflow accepts a development-owner authorization.
Merging this proposal does not activate it or authorize a release. Production's
existing six-signature policy and default fail-closed behavior remain unchanged.

## Why a separate policy is proposed

The six Ed25519 roles and distinct non-author principals are an enforced **project
security contract**, introduced by publisher commit
`16fe5d90fbe42a528f5775271f3dbacf5f395531`. `docs/CONTENT_PUBLISHER.md` describes the
signing requirement as a deliberate new release contract. Inspected project
issues [#462](https://github.com/AyalewGM/ai-tutor/issues/462),
[#433](https://github.com/AyalewGM/ai-tutor/issues/433) and the specialist charters
require independent technical evidence and owner authorization, but do not
prescribe six external cryptographic identities. No inspected external source
establishes a six-signature mandate; this is an evidence-limited finding, not a
legal opinion or a waiver of an undiscovered contract.

The development-only proposal replaces that human/signer multiplicity with five
real, separate, non-author Codex technical reviews and **one owner-held detached
signature** accepting their exact evidence and authorizing a bounded operation.
Agent reviews are never described as human, GitHub `APPROVED`, or authenticated
specialist signatures. A sole owner cannot supply their own GitHub PR approval.
The proposal does not relax shared main/production branch rules or fabricate one.

Child privacy, consent, school agreements where applicable and other legal holds
in `docs/security/PILOT_COMPLIANCE_CHECKLIST.md` and
[#436](https://github.com/AyalewGM/ai-tutor/issues/436) remain. A sole-owner policy
cannot self-certify legal compliance or substitute for a required external review.

## Non-negotiable trust boundary

A username, `github.actor`, prompt, local approval JSON or repository file cannot
prove human owner authorization when an agent can use equivalent credentials.
GitHub also exposes deployment approval through authenticated APIs; an accessible
token with that authority defeats a UI-only assumption.

Before any development adapter is activated, the owner must establish and verify:

1. A passphrase-protected owner signing key on an owner-only device or hardware
   token, outside agent-readable files and all agent-accessible SSH agents. **Do
   not reuse the unlocked staging-inspection key.** No additional account,
   reviewer identity, signing service or persistent runner is required.
2. Through the trusted IONOS console or a separately owner-controlled privileged
   connection, compare the repository's authenticated GitHub owner/repository IDs
   with the pinned `22088298` / `1367979340`, accept the exact reviewed policy and
   verifier SHA, and enroll the owner's public key. This is the identity-binding
   ceremony; those numbers inside an agent file alone are not authentication.
3. A root-owned fixed verifier/entrypoint and public policy outside writable
   checkouts, with a root-owned `0700` replay directory and `0600` receipts.
   Public policy/context files must be regular single-link root-owned files,
   mode `0644` or `0600`, with protected, descriptor-pinned ancestors.
4. Remove agents' ability to replace that verifier, policy, context or replay
   state. **Current broad staging sudo/root access fails this condition.** One
   bounded operator proposal is to restrict only the existing inspection public
   key to a root-owned fixed read-only forced command, preserving the owner's
   other authorized keys. That command must allow fixed metadata operations only,
   never arbitrary shell, Python, paths, Docker exec, socket access or sudo.
   No server configuration is changed by this PR. Inspect all other agent-held
   credentials for root, environment-approval or deployment bypass authority.

A root-owned file does not protect against an agent that still has root. Tests
cannot prove this live capability boundary. An unchecked boolean in a policy is
not evidence that it exists. If this boundary cannot be established, authenticated
solo-owner release execution remains blocked.

## Detached authorization and deterministic checks

The implementation is `scripts/ops/development_release_authorization.py`.
Canonical JSON is UTF-8, sorted keys, compact separators, no duplicate keys,
non-finite numbers or trailing bytes. The owner signs the exact canonical bytes
using OpenSSH's namespace-separated detached signing:

```bash
# OWNER-ONLY device; the agent must never run this or receive the private key.
ssh-keygen -t ed25519 -f /OWNER-ONLY/mihur-development-release -C mihur-owner-release
ssh-keygen -Y sign -f /OWNER-ONLY/mihur-development-release \
  -n mihur-development-owner-release-v1 /OWNER-ONLY/release-authorization.json
```

The first command prompts for a passphrase; use a nonempty passphrase. Public-key
transfer to the trusted console is permitted. Private keys, passphrases and SSH
agent sockets must not enter agent workspaces or CI. Test keys are explicitly
synthetic, generated only in a disposable environment, and must never be enrolled.

The strict V1 authorization binds:

- Repository full name and numeric repository/owner IDs; the pinned policy digest.
- Exact source commit and tree, package and runtime SHA256, all six immutable
  API/gateway/frontend/PostgreSQL/Redis/proxy image references and digests.
- The complete five-lane technical-evidence bundle digest.
- Literal `development`, `https://dev.mihureducation.com`, database
  `mihur_staging`, and the independently inventoried development machine-ID SHA256
  `3ee0437dd6184c8f150d0530093391fe7499cce86999f3c1a2e67dc0daec1c4b`.
  This is `SHA256(Path("/etc/machine-id").read_text().strip().encode("utf-8"))`,
  not an SSH host key. Strict SSH inspection separately retains the verified
  ED25519 host-key fingerprint
  `SHA256:u3DFEz6/ESWWukGThMlhqZdp6707zgMcfNxDpOFpAeY`.
- An exact ordered plan from `deploy`, `publish`, `deploy` then `publish`, or
  `rollback`; issue/expiry times (maximum one hour), and a fresh random 256-bit nonce.

`package_sha256` is the existing publisher digest of the actual manifest excluding
`review_evidence`, using `content_publishing.canonical()` / `digest()`; it is not
an arbitrary JSON hash. The token never promotes pending/provisional status: the
future adapter must retain accepted partial-practice standards bounds, while the
exact source/tree and runtime digest bind generator bytes, modes and seed bounds.

The policy's schema is `MIHUR_DEVELOPMENT_OWNER_POLICY_V1`; its fields are the
fixed scope above plus `owner_public_key`, `revoked`, `max_age_seconds` and `schema`.
The authorization schema is `MIHUR_DEVELOPMENT_OWNER_AUTHORIZATION_V1`.
The module's `POLICY_FIELDS`, `AUTH_FIELDS` and `BINDINGS` define the exact field
sets; unknown fields, mutable tags and changed bindings are rejected.

The trusted expected context is independently collected by the operator from the
actual reviewed checkout, images, protected machine/database configuration and
fresh authenticated GitHub CI evidence. It is not supplied by a prompt, ambient
`APP_ENV`/`DATABASE_URL`, or an agent's assertion. The pure verifier deliberately
cannot prove that a caller-supplied context is trusted. Its result is not itself a
capability or release receipt. The verify-only CLI reads fixed protected policy
and context files under `/etc/mihur-staging`; missing configuration fails closed.

The evidence bundle schema `MIHUR_CODEX_TECHNICAL_EVIDENCE_V1` requires the exact
source SHA/package digest, nonempty producing session IDs and five distinct
non-author reviewer sessions (`math`, `pedagogy`, `standards`, `security`, `qa`).
Each review records its scoped verdict and SHA256 of the real captured transcript
artifact, including exclusions. The verifier checks completeness, separate session
labels, subject/hash equality and actual artifact bytes. It cannot authenticate
that a session occurred or prove independent judgment from strings. Preserve real
session evidence; the owner must examine and sign acceptance of that bundle. Do
not invent missing reviews. Existing trusted GitHub collection must still verify
fresh exact-head checks and their expected App IDs; this primitive does not turn
agent-provided CI JSON into authenticated check evidence.

## Replay and effect ordering

`verify()` is read-only and does not reserve a nonce. The future trusted adapter
must call `reserve_nonce()` **before the first effect**, under the existing
operator serialization boundary. That primitive locks a protected directory,
creates one nonce file using `O_EXCL | O_NOFOLLOW`, and fsyncs the record and
parent. One global nonce cannot be reused with another payload, action or retry.
A crash, partial write, fsync failure or uncertain operation leaves it consumed;
there is no automatic cleanup or retry. Inventory first, then obtain a fresh
owner-signed continuation or rollback authorization. Never delete a reservation
merely to retry. Ordinary learner selection/scoring must not consume operation
nonces.

The CLI supplied by this proposal is verify-only: successful output explicitly says
`VERIFIED_PROPOSAL_ONLY`, no deployment, no publication and no nonce reservation.
No command in this PR deploys, publishes, changes a learner record or activates
content. The function's fixture `owner_uid` hooks are not exposed by that CLI.

## Required next review and activation sequence

1. Independently review this exact proposal SHA and rejection/concurrency tests;
   obtain explicit owner acceptance of the development-only policy. No self-PR
   `APPROVED` event is required or fabricated. Production approvals are unchanged.
2. Owner performs and documents the key/trust-boundary ceremony above. Verify
   the restricted inspection credential can no longer execute privileged actions
   or read signing material; verify protected policy/verifier/state ownership.
3. Separately review a bounded adapter to the existing development entrypoints:
   `deploy/staging/control.py`, `deploy/staging/publish_content.py`,
   `scripts/ops/publish_content.py`, and the environment-aware caller of
   `content_publishing.validate()` / `publish()` / `permitted()`. Keep the current
   six-signature validator unchanged for default/production. No agent-writable
   flag or environment variable may select the alternative policy.
4. That adapter must distinguish one-use operation authorization from persistent,
   revocable runtime permission for the exact package. All published selection,
   scoring, hints and Workspace checks must revalidate the approved development
   package; production must reject development permissions. Unknown contexts and
   missing policy fail closed. Required tests include actual publication/runtime
   revocation and ordinary learner reads without operation-token consumption.
5. A separately reviewed **development-only** candidate-image build may consume
   the exact reviewed #501/#505 candidate SHA without fabricating a main merge or
   owner PR approval. Build privately, without deploy secrets, before the final
   owner grant so the grant can bind final immutable image digests. Existing
   production/main build workflows and protections stay unchanged. No registry
   build or release-workflow modification is performed by this proposal. The existing
   AppSec scan additionally covers PRs targeting the stacked #501 branch.
6. Recollect exact-SHA technical reviews and mandatory CI/AppSec/CodeQL, verify
   isolation/backups and immutable artifacts, then present the final exact
   source/package/image/environment/action/evidence tuple for the owner's one
   detached authorization. Verify and atomically reserve it immediately before
   the approved effects. Release execution still requires that exact authorization.
7. Execute only the signed plan. Verify actual approved-question selection,
   rational submission/feedback, no mastery credit and access denials on the
   deployed development SHA before claiming student availability. Preserve the
   existing conditional activation authorization, but do not expand its scope.

Until steps 1–4 are genuinely complete, the existing six-signature publisher stays
in force and the Ontario release remains blocked. This staged proposal is not
claimed to have established an operational solo-owner authorization system.

## Reference boundaries

- [GitHub deployment approval API](https://docs.github.com/en/rest/actions/workflow-runs#review-pending-deployments-for-a-workflow-run): approval can be an API operation, so an agent-held capable token is not human-presence proof.
- [OpenSSH detached signing](https://man.openbsd.org/ssh-keygen.1): signing namespaces and allowed-signers verification; signing key remains owner-controlled.
- Project requirements remain in `CONTENT_PUBLISHER.md`, the specialist charters
  and `PILOT_COMPLIANCE_CHECKLIST.md`. No assertion of legal certification is made.
