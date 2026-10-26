# Mihur Content Publisher — first staging slice

Parent: #462. Scope: one signed two-step rational equation family from merged
#489, mapped to existing `MATH.EE.EQUATION.TWO` / `MTH1W.C.ALG.EQ2`.
The initial manifest is **pending**. Nothing in this PR grants student release.
Merged #472 data and #495 inverse operations remain inactive follow-on adapters;
#494/#496 provide the reused exact-rational scorer and trust-boundary contracts.

## One command after release setup

From the verified deployed checkout on the dedicated staging VPS:

```bash
sudo python3 deploy/staging/publish_content.py publish --sha <40-character-deployed-main-SHA>
```

Equivalent GitHub entry point: **Mihur Content Publisher**, `publish`, exact
`release_sha`. It requires main HEAD, successful CI/AppSec at that SHA, the
protected `staging-content-publisher` environment and a dedicated runner labelled
`mihur-staging-publisher`. No deployment secrets are accepted as workflow inputs.
The runner must have access only to the staging host and the fixed operator
entry point. Keep `/opt/mihur-staging` root-owned and unwritable by the runner;
do not allow arbitrary Python/script paths through sudo. Never attach this
runner to PR jobs. Existing host isolation rules in `control.py` still apply.

A pure, database-free preview also works before provisioning the host:

```bash
python -m scripts.ops.publish_content dry-run
```

The workflow's dry-run uses a hosted runner. Preview explicitly reports pending
approvals and never treats a structurally valid manifest as authorization.

## One-time review trust configuration

Create `/etc/mihur-staging/content-review-policy.json`, root-owned mode 0644,
inside the root-owned staging configuration directory. This file contains only
public keys and author identities; it must be readable by the non-root API user
and writable only by the deployment owner. Bind it read-only as configured in
Compose. Never place private signing keys in this file or on the runner/API.
Unreadable or absent policy fails closed.

Policy shape (public keys only):

```json
{
  "authors": {"<generator_sha256>": ["mihur-content-author"]},
  "keys": {
    "math-review-key-1": {
      "principal": "independent-mathematics-reviewer",
      "roles": ["math"],
      "public_key": "<base64 raw Ed25519 public key>"
    }
  }
}
```

The deployment owner verifies the real author identities and reviewer authority
before provisioning this policy. The author list is checked against the external
policy, so an author cannot escape separation by editing the manifest. Assign
trusted principals for `math`, `pedagogy`, `standards`, `security`, `qa`, and
`release`. Never provision an author as an independent reviewer of their work.
Key removal immediately denies subsequent selection and scoring.

Before reviewers sign, set manifest activation to `staging`. Keep the reviewed
content SHA, generator SHA-256, runtime contract SHA-256, family, skill mapping,
modes and seed bounds exact. Runtime hashing covers the publisher, selector,
scoring paths, API adapters, probe, host command and workflow. Any change requires
fresh signatures. The host also verifies that the original generator at the
reviewed content commit matches the manifest and is an ancestor of the release.

Each reviewer evaluates their gate and signs the canonical envelope containing
`manifest` (excluding `review_evidence`), `role`, and `evidence_url`. The URL points
to their exact-revision GitHub verdict, not an author's claim. An offline helper:

```bash
python -m scripts.ops.sign_content_review content_packages/mth1w-signed-two-step-v1.json \
  --role math --key-id math-review-key-1 \
  --evidence-url https://github.com/AyalewGM/ai-tutor/pull/NUMBER#REVIEW \
  --private-key /secure/offline/math-review.pem --output /secure/reviewed-package.json
```

Collect the six signed attestations in one manifest and commit it through review.
The helper does not generate keys, claim a verdict, or configure trust. Test keys
are ephemeral fixtures and are never production authorization. Signed evidence
is a deliberate new release contract: historical bounded draft comments cannot
be silently widened to deployment permission.

## What publication does

1. Lock publisher operations; run existing dedicated-host/Compose preflight.
2. Require exact checkout, release file, running API image digest and image SHA.
3. Validate manifest and signatures before any live database mutation.
4. Dump staging to a retained, private custom-format backup; verify its archive;
   restore the whole dump into a uniquely named disposable database with
   `--exit-on-error`; drop only that disposable database.
5. Lock the publishing transaction. Require the existing active MTH1W curriculum,
   skill and canonical mapping. Register the family once and insert deterministic
   Problem IDs with per-mode metadata. Refuse conflicts or disabled prior rows.
6. Use the existing learner selector and `record_evidence` route with the reused
   `score_fraction` exact scorer. No parallel engine or manual SQL activation.
7. Provision a new synthetic family, authenticate, and exercise the **running API**
   through diagnostic, guided and independent practice, feedback, fresh questions,
   persisted attempts and replay rejection. Never reuse an actual family.
8. If the probe fails, disable this package's metadata and report failure. Preserve
   every variant and all synthetic/real attempts, diagnostics and mastery records.

The finite first slice has 12 questions per permitted mode, 36 total. The author
generator is reused without rewriting its mathematics. Mode pools have distinct
mathematical fingerprints. Pool exhaustion fails closed; this PR does not grant
the generic legacy generator authority to create additional rational questions.
Unhinted independent correctness alone does not bypass existing mastery gates.

The report provides package-level counts per local skill: `stored`, `generated`
(materialized generated variants), `authorized`, and `learner_selectable` per mode
for a fresh learner. Individual history further narrows selection. The synthetic
probe records how many were actually completed. Counts are not proof of complete
skill depth or all-17-skill readiness. `staging_learner_verified` is true only after
the live HTTP probe succeeds. Browser, keyboard, fraction-entry UX and screen-reader
acceptance remain separate; HTTP success does not grant those reviews.

## Rollback and failure handling

```bash
sudo python3 deploy/staging/publish_content.py rollback --sha <same-deployed-main-SHA>
sudo python3 deploy/staging/publish_content.py report --sha <same-deployed-main-SHA>
```

Rollback takes a verified backup and sets only this package's learning-mode flags
to false. It never deletes Problems, attempts, diagnostics, mastery, variants or
family accounts. A retry is insert-idempotent, but it cannot silently re-enable a
rolled-back package. Re-enable requires a reviewed release decision and a follow-up
change; do not edit SQL or widen the legacy catalog snapshot policy.

Backups and successful release receipts stay under `/var/backups/mihur-content`.
Do not upload backups to Actions artifacts. A rejected signature means obtain the
missing independent gate or fix the trust configuration. Mapping conflict means
resolve the existing canonical mapping through Standards review. Image/SHA mismatch
means deploy the exact reviewed image through the existing release procedure.
Backup or restore failure means publication must stop. Probe failure means inspect
the retained synthetic history, correct the implementation, and re-review it.
Failure output redacts credentials and answer keys.

## Validation and release boundary

Author tests use a private synthetic database and ephemeral review keys. They cover
signature tampering, self-approval, exact rational alternatives, mode isolation,
learner selector and authenticated route, replay, feedback, no private JSON fields,
reseed preservation and metadata-only rollback. CI runs them with the repository
suite; they are not independent approvals or real staging evidence.

Before release, obtain exact-SHA independent Mathematics, Pedagogy, Standards,
Security, QA and Engineering release decisions on the implementation PR, configure
trusted policy and protected environment/runner, build/deploy the exact image,
then execute the command. Do not claim student readiness until live staging and
required browser/QA reviews have passed. Only after that success extend this same
publisher with reviewed data (#472) and inverse-operation (#495) adapters.
