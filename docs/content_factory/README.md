# Mihur AI Mathematics Content Factory — Pilot V1

**Scope:** Ontario Grade 9 MTH1W multi-step equations; existing shared canonical skill MATH.EE.EQUATION.MULTISTEP. **Current state:** DRAFT_UNVERIFIED, runtime disabled. Coordinates existing #313, #337, #446, #462 and #278. This is not a new Ontario-specific mathematical engine.

## Working vertical slice

The source-grounded blueprint identifies official Ontario 2021 C1.5 as a **candidate**, maintains source/IP boundaries, lists mathematical structures, teaching phases and misconception hypotheses, and refuses unknown family identities.

The executable offline factory samples three **already registered canonical families** across GUIDED and INDEPENDENT modes. It fingerprints mathematical operands, checks repeatable seed generation, reconstructs each original equation and solves it independently with SymPy, checks substitute equality, compares the stored canonical response to its independent oracle, and probes misconception alternatives for false positive / ambiguous attributions. It projects answer-hidden review tasks and tests that independent mode receives no hints.

The report has explicit failing gates for independent reviewers, canonical mapping, production scoring, frontend, external Muse QA and staging/production. **No report can authorize a release.** A nonzero CLI exit is expected if generator mathematics or quality checks fail; do not conceal it or weaken the gate. The existing canonical registry already removes wrong-answer signatures that collide with the correct answer; the factory verifies this safety behavior and deliberately injects an unsafe simulated alternative in a synthetic regression to prove fail-closed detection. Do not report a nonexistent source defect.

## Run safely, without a database

    python -m scripts.math_content_factory --blueprint docs/content_factory/mth1w_eq3_factory.v1.json --seeds 96 --output /tmp/mihur-factory-report.json
    python -m pytest -q tests/test_math_content_factory.py
    ruff check scripts/math_content_factory.py tests/test_math_content_factory.py

No staging, production or family data is needed. No seeding, migrations, local learner access, or API credentials are used.

## One accountable delivery owner

The **Mihur Content Director** is the one point of coordination. Specialist reviewers retain independent decisions but the user no longer has to manually transfer comments.

| Stage | Lead | Measurable output |
| --- | --- | --- |
| Inventory | Director | Current-main SHA, existing accepted/draft/live matrix and exact content gap |
| Official research | Research agent | Official standard version/clause; source URLs; structural demands and licensing boundaries |
| AI design | Question designer | Original, pedagogically distinct blueprints, seed constraints, misconception routes and representations |
| Math production | Python engineer | Deterministic families, exact SymPy/independent oracles, uniqueness and invalid-case proofs |
| Student simulation | Adversarial student agent | Wrong answers, unsupported diagnoses, answer leakage, over-scaffolding, repeated-task stress tests |
| Independent QA | Math and Pedagogy reviewers | Exact-head acceptance of mathematics, differentiation, Socratic hints and unseen transfer |
| Integration | Assessment Backend and Frontend/MVE | Versioned family/scorer/response/mode contract, UI manipulations and keyboard/AT equivalents |
| Pilot gate | Muse + Engineering + DevOps | Synthetic repeated-session learner test, two-pass idempotent seed, history preservation, authorized staging release |

**V1 limitation:** the implemented simulator is **deterministic misconception adversarial testing**, not an actual autonomous AI student-run. Its agent contract is defined in the blueprint for future orchestration. An LLM suggestion can propose a family or misconception but is never a mathematical authority.

## Skill-quality passport

- Target approximately 8–12 genuinely different mathematical families per substantial skill **where the scope justifies them**; changing seed/numbers is never counted as a new family.
- Measure actual distinct mathematical task fingerprints, distributions of difficulty and representation, seed collision rate, original context and genuine transfer.
- Independently check mathematics, restrictions, equivalent answers, misconception collisions, nonzero denominators, negative/rational/no-real/multiple-solution cases when appropriate.
- Require Observe → Predict → Manipulate → Explain → Practice → Diagnose → Transfer → Verify and Concrete → Visual → Symbolic, with actual learner evidence, keyboard, screen reader and reduced motion.
- Diagnose only response-supported misconceptions. Correct the original, then transfer to unseen **target-preserving** mathematics before fading.
- Do not allow assisted success to be counted as independent mastery, or expose teacher answers/oracles in public payloads.
- Separate AUTHORED, MERGED, REVIEWED, REGISTERED, STAGING VERIFIED and PRODUCTION VERIFIED as distinct factual statuses.
- Do not declare readiness without real frontend/MVE, scorer, multi-session Muse and exact-SHA release evidence.

## Copyright / curriculum boundaries

The Ontario Ministry Grade 9 2021 C1.5 page describes creating, solving and verifying equations; source: https://www.dcp.edu.gov.on.ca/en/curriculum/secondary-mathematics/courses/mth1w/c/c1

EQAO Grade 9 assessment resource directory covers released formats and the official framework; source: https://www.eqao.com/the-assessments/grade-9-math/

Both are reference-only. Do not copy or closely paraphrase questions, student/teacher PDFs, diagrams, responses, answer choices or scoring rubrics. Current mapping remains a candidate pending independent Standards source fidelity; no permission to rehost assessment material is claimed.

## Next reusable increments

1. **Content (#313/#337):** fix any factory-discovered wrong-answer collision on the existing canonical family branch; deepen missing *reasoning structures* before increasing raw counts.
2. **Assessment Backend (#462):** agree on one versioned canonical family/scorer/typed response/per-mode manifest. Reuse #459 legacy catalog authorization, but do not grant new families mode authority from draft merges.
3. **Frontend/MVE and Muse (#446):** connect accepted questions to real manipulations, response-state invalidation, multi-session nonrepeat and independent scoring, then run synthetic learner journeys.
4. **Engineering:** check exact-SHA source and review evidence, separate staging and production authorizations and history-safe rollback.

**Absolute boundaries:** this slice does not import the factory into runtime application routes, seed content, create IDs or mappings, grant eligibility flags, rewrite problems or learner history, award mastery, merge or deploy.

## Review routing automation V1 (bounded, offline)

The companion tool `scripts/math_content_orchestrator.py` consumes one
factory JSON quality report plus an evidence manifest containing the exact
content SHA, CI result and independent review links. It deterministically
produces one next accountable owner and one consolidated owner-facing report.
Rejected reviews route back to Content Production; SHA changes invalidate
old approvals. It cannot invoke agents, post comments, merge code, seed a
database, or authorize staging/production.

Example synthetic evidence file:

```json
{
  "content_sha": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "ci": {"sha": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", "status": "success"},
  "math": {"status": "PENDING"}
}
```

Run the coordinator after an authorized integration has obtained its own
verifiable evidence:

```bash
python -m scripts.math_content_orchestrator \
  --factory-report /tmp/mihur-factory-report.json \
  --evidence /tmp/mihur-factory-evidence.json \
  --output /tmp/mihur-single-owner-handoff.json
python -m pytest -q tests/test_math_content_orchestrator.py
```

**V1 is an offline routing-intent layer, not a running cross-agent dispatcher.**
To remove manual switching completely, an Engineering-owned follow-up must
connect it to authenticated GitHub issue/PR events, actual agent invocation
availability, independent-review attestation and audit logging. It must
fail closed and never perform release actions. Do not claim automatic
delegation or reviewer approval before that integration is executed.

## GitHub event listener — read-only Actions integration

The workflow `.github/workflows/mihur-content-director.yml` listens to
`pull_request_target` updates, `pull_request_review` submissions/dismissals,
and manual `workflow_dispatch`. It uses a **trusted main-branch checkout**
and read-only `contents`, `pull-requests` and `actions` permissions.
It does NOT checkout or execute untrusted PR head code, post back to GitHub,
approve a review, assign an agent, or deploy a release.

`scripts/math_content_github_evidence.py` obtains the current PR head SHA
and latest PR-triggered CI status directly from the authenticated GitHub REST
API. It deliberately leaves independent review gates PENDING: a comment,
AI-generated text, or successful CI run is *not* reviewer attestation.
The existing offline orchestrator translates the available evidence into a
single next owner and an Actions Step Summary plus short-lived artifacts.

**Activation requirement:** GitHub does not execute a new workflow merely
because its YAML is proposed on a draft feature branch. The workflow must
first be reviewed and merged into the default branch; run it manually against
PR #484 using the Actions UI, then open/modify a synthetic test PR and confirm
the workflow executes from trusted code. No production or staging activity
is involved. Manual run requires `pr_number`.

**Known scope limit:** until a subsequent authenticated reviewer-attestation
adapter and an explicitly authorized agent-dispatch integration exist, the
coordinator can report review owners but cannot truthfully mark Math,
Pedagogy or Muse as ACCEPTED or claim it actually invoked an agent. Do not
relax this rule to reduce coordination workload.

## Pre-PR entry point — explicit approved issue

The companion GitHub Actions workflow `.github/workflows/mihur-content-intake.yml`
starts *before a content PR exists*. It listens to a maintainer-applied
`mihur-content-request` issue label or to `workflow_dispatch` with an issue
number. The adapter `scripts/math_content_pre_pr.py` requires that the issue
is still open, has that exact label, and is not itself a PR. It treats the
issue body strictly as untrusted data; the V1 pilot scope is pinned to the
existing EQ3 blueprint, never derived from unreviewed instructions.

The Actions job uses trusted default-branch code and read-only GitHub
permissions. It emits a concise owner/next-action report and an audit artifact.
It cannot execute a research/model agent, create a PR, mark a review approved,
change runtime/metadata, or deploy. This is **pre-PR intake and planning**,
not end-to-end autonomous orchestration.

Once the workflows are independently reviewed and merged into main:
1. Open or reuse the appropriate Mihur mathematical content issue.
2. Have an authorized maintainer apply the `mihur-content-request` label,
   or manually run **Mihur Content Factory — pre-PR intake** with that
   already-labelled issue number.
3. Review the workflow's Step Summary. It identifies the Content Director
   as owner of the bounded existing-family/depth-gap analysis.
4. Separate authorized agent-dispatch and branch/PR creation integration
   is still required before agents can implement from that report.

## Explicit coding-agent dispatch (manual and separately approved)

The further workflow `.github/workflows/mihur-copilot-dispatch.yml`
uses GitHub's documented Copilot issue-assignment REST API to hand a
**pre-existing, open, explicitly labelled EQ3 issue** to the Copilot coding
agent. It is intentionally `workflow_dispatch` ONLY — the automated issue
intake never launches coding agents.

**Requirements before enabling:**
1. Engineering and Security must review this workflow, its permissions and
   the issue-to-agent task template. Merge it to the default branch after
   exact-head quality gates.
2. Configure a protected GitHub Actions environment named
   `mihur-content-agent-dispatch` with required reviewers / owner approval.
3. Configure its secret `MIHUR_COPILOT_DISPATCH_TOKEN` with only the minimum
   permissions GitHub currently requires for Copilot issue assignment.
   This is **not** the Actions read-only `GITHUB_TOKEN`.
4. Explicitly mark a single existing bounded content issue with the
   `mihur-content-request` label, then manually run
   **Mihur Math Content Director — explicit Copilot dispatch**, giving its
   issue number and typing `ASSIGN_COPILOT_EQ3`.
5. Check the Copilot assignment, resulting task and draft PR; do not equate
   assignment with task completion, independent approval or content release.

The dispatch code refuses closed/unlabelled/PR issues and prevents
repeat assignment when Copilot is already assigned. It verifies that GitHub
acknowledges assignment. The bounded instructions demand existing-family
reuse, mathematical seed tests, no proprietary content copying, and
independent review before scoring/runtime changes. GitHub will also provide
the agent the original issue description; treat that data as untrusted and
review the proposed PR against the bounded instructions.

**This is a deliberately manually gated first real agent invocation.**
Continuous self-triggering pre-PR dispatch, reviewer attestation, task
completion observation and safe next-agent delegation remain separate
Engineering milestones. No automatic merge, independent self-review,
staging seed or production deployment is enabled.
