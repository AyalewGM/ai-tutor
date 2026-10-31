# Mihur Content Publisher — first staging slice

Parent: #462. Scope: one signed two-step rational equation family from merged
#489, mapped to existing `MATH.EE.EQUATION.TWO` / `MTH1W.C.ALG.EQ2`.
The manifest pins the squash-merged source commit `ddcebf22dff79247bd9b108fd4c650a4fac1c4c3`; its generator bytes match the independently reviewed #489 head `4b2c878d94c5992a1ce657ff4541f3554ab01e14`. This avoids requiring an unmerged branch head to be a main ancestor. The initial manifest is **pending**. Nothing in this PR grants student release.
Merged #472 data and #495 inverse operations remain inactive follow-on adapters;
#494/#496 provide the reused exact-rational scorer and trust-boundary contracts.

## Standards boundary bound into the release

The signed manifest preserves the exact independent #489 Standards decision rather
than treating a generic `standards` signature as full Ontario coverage. It binds
the official Ontario source record, `MTH1W.C1.5` printed pages 118–119,
`PARTIAL_NON_EXHAUSTIVE / PROVISIONAL_NOT_ACCEPTED`, the excluded context-
creation, interpretation and learner-verification evidence, and `MTH1W.C1.4
NOT_MAPPED`. Both `coverage_credit` and `production_taxonomy_activation` are
false. Validation rejects any missing or widened field, and the identical block is
stored with each published Problem's package manifest and metadata provenance.

The checked-in package remains provisional, pending and unsigned. It cannot be
published. After an independent bounded source-fit decision, a separately signed
manifest may set only `standards_provenance.acceptance` to
`ACCEPTED_PARTIAL_PRACTICE`. Its disposition remains `PARTIAL_NON_EXHAUSTIVE`,
coverage credit and production taxonomy activation remain false, and every source
locator, inclusion, exclusion and `C1.4 NOT_MAPPED` field stays exact. This permits
only the existing diagnostic/guided/independent practice modes after all six
independent signatures and staging release authorization pass; no mastery evidence,
full-expectation coverage or production taxonomy activation follows from it.

A Standards signature attests this bounded source-fit disposition only. It does
not convert provisional correspondence into accepted coverage. Full `ACCEPTED`
coverage, changed exclusions, activation flags, new modes or source revisions are
rejected by this slice and require a separate reviewed contract and fresh signatures.
Staging policy and release authority remain Architecture/Engineering responsibilities.


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
  "runtime_authors": {"<runtime_sha256>": ["mihur-runtime-author"]},
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
Each independent role must use a distinct authorized principal and distinct public
signing key; aliases of one key cannot impersonate multiple reviewers. Key removal
immediately denies subsequent selection and scoring.

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
suite and repeats the publisher tests against isolated PostgreSQL schemas; they are not independent approvals or real staging evidence.

Before release, obtain exact-SHA independent Mathematics, Pedagogy, Standards,
Security, QA and Engineering release decisions on the implementation PR, configure
trusted policy and protected environment/runner, build/deploy the exact image,
then execute the command. Do not claim student readiness until live staging and
required browser/QA reviews have passed. Only after that success extend this same
publisher with reviewed data (#472) and inverse-operation (#495) adapters.


### Parser resource bound (PR #501 remediation)

The fraction scorer bounds each raw response, including variable assignment syntax,
to 64 characters before whitespace processing. Decimal/sign/slash validation uses
linear string operations, preserving exact rational equality and signed denominators.
Oversized whitespace and zero-digit near misses fail closed. Regression coverage is
in `tests/test_fraction_assessment_registry.py`; these author tests do not grant
specialist or release acceptance.

The scorer is one of the 14 source files in `RUNTIME_FILES`. Its source change
requires the pending package runtime pin to change from `97f7b01c21bea33942c9ef91e2bb2047cd8b86b4731ed591d108c083ee564373` to `3877ca04d084e449aa09e9d50f547baec4b75f14f350ddf6ca35b5699c10d455`.
The pin was recomputed from that existing inventory using SHA-256 of file bytes and
the existing sorted compact JSON digest format, without importing product modules.
The package remains pending with empty review evidence; no signatures, approvals,
activation, content identities, or learner records were added or changed.


### Persisted transfer feedback after reload (PR #501 remediation)

Recovery now returns the stored boolean transfer outcome only after checking a
unique result, matching attempt and regenerated transfer identity, valid issuance,
completed guided success, and non-credit/unhinted metadata. Successful reloads can
continue to the separate verification task; failed outcomes remain feedback-only.
Malformed, mismatched, or duplicate results fail closed. This grants no XP,
independent evidence, mastery credit, or publication authority.

Because `app/adaptive_response_api.py` is in the existing runtime inventory, the
pending unsigned package pin changes from `3877ca04d084e449aa09e9d50f547baec4b75f14f350ddf6ca35b5699c10d455` to `fafcf9db918e4b665adb92a9c2482176f6f36b0551d2516425c22d947192e270`.
The digest was computed from source-file bytes without importing product code;
review evidence remains empty and activation remains pending.

The signed author list must exactly match the union of generator and runtime authors in the deployment-owned policy. Missing runtime provenance fails closed; runtime contributors cannot approve their own release. Published answer feedback records an Attempt but does not advance mastery, focus, review, difficulty, or mastery events.
