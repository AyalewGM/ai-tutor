# Mihur Post-Merge Quality Audit — Operating Runbook

**Coordination:** [#433](https://github.com/AyalewGM/ai-tutor/issues/433)  
**State:** proposed review process, not an audit verdict or enabled automation.  
**First snapshot:** `6b66f6651a99cd2ec03b0a51522a98e7d9c15774`; every audit run must independently read/pin *current* `main`.  
**Owner:** Mihur Engineering Lead. Independent QA, Math, Pedagogy, Standards and AppSec retain separate verdicts.

## Objective and non-negotiable boundaries

Audit the merged system for **reproducible** technical, safety, mathematical, pedagogical, accessibility, privacy, security and standards defects. Existing merge approvals, passing workflows, or machine-generated comments do not establish end-to-end correctness.

- **BUILD ONCE → MAP MANY → DEPTH BEFORE BREADTH**: never create duplicate canonical skills, generators or graders to address a jurisdiction-specific symptom.
- Read-only analysis by default; use isolated, synthetic PostgreSQL and browser fixtures for proof. Never touch live families, personal data, production state, secrets or real children.
- Preserve UUIDs, Attempt, DiagnosticAttempt, MasteryEvent, historical learner/variant evidence, approved math definitions and oracle/scorer boundaries. DRAFT/PROVISIONAL/UNKNOWN is **not** learner authority or curriculum coverage.
- No feature or standards activation, PR merges, deployment, new family invitations or schedule enabling by an audit agent. Manual owner release decisions remain independent.
- Never copy protected teaching resources. Do not expose actionable security exploits, student data or secrets in public issues; escalate through an appropriate restricted security path.

## Manual launch using repository custom agents

The six YAML-frontmatter profiles in `.github/agents/` are compatible with GitHub Copilot custom agents (where the repository/account has access). They specify `disable-model-invocation: true` and `user-invocable: true`, so invocation is **manual**. The profiles are not autonomous monitors, background tasks or GitHub Actions workflows; issue creation/merging this runbook does **not** start execution or enable a ChatGPT schedule.

After independently approving and merging the profile PR, an authorized reviewer can open the relevant audit issue (#435–#440), select its matching `Mihur ... Auditor` custom agent in the supported GitHub Copilot interface, and explicitly assign/invoke that issue for a one-time audit. The agent should pin `main`, check previous evidence and report only substantive findings. If this Copilot capability is unavailable in the owner's account, the Markdown files remain self-contained reviewer instructions that can be run manually with an available authorized agent tool; do not misrepresent installation or invocation as complete.

- Engineering: `.github/agents/mihur-bug-hunter.agent.md` → #435
- AppSec: `.github/agents/mihur-security-auditor.agent.md` → #436
- Mathematical: `.github/agents/mihur-math-auditor.agent.md` → #437
- Pedagogical: `.github/agents/mihur-pedagogy-auditor.agent.md` → #438
- Muse QA: `.github/agents/mihur-muse-auditor.agent.md` → #439
- Standards: `.github/agents/mihur-standards-auditor.agent.md` → #440

The six profiles grant only **read**, **search**, and the default repository-scoped read-only GitHub MCP tool set. They grant **no shell (`execute`) or file-edit tool**. Muse alone additionally has localhost-only Playwright access for an already-running, **isolated synthetic** test environment. GitHub's default GitHub MCP tools are read-only; repository-specific MCP overrides, ambient permissions and the test host must still be independently checked before invocation. To execute additional tests, an authorized CI/QA operator must run them in a separate isolated workflow and provide logs; reviewers cite that evidence and never claim local execution they did not perform. Findings are drafted by reviewers, then recorded as issues/comments by an authorized Engineering coordinator (reviewer agents cannot post via the read-only tool set). **Do not allow any reviewer to author changes it later independently approves.**

## Independent lanes and ownership

| Audit lane | Investigate | Fix owner / independent reviewer |
| --- | --- | --- |
| **Engineering / Bug Hunter** | CI and seed regressions; API invariants; transactions; Alembic migration lineage; startup; retry/idempotency; Redis/WebSocket/whiteboard; frontend routing; 2GB staging resources | Backend/Frontend/DevOps authors; Engineering Lead verifies integration and routes QA |
| **AppSec + Child Privacy** | Parent/learner mutual exclusion, session fixation/logout, PIN/role bypass, cross-child and cross-family access, invite concurrency, practice-link leakage, image/PDF uploads, audit/log policy, COPPA readiness | Auth/backend authors; independent AppSec plus privacy/legal when relevant |
| **Independent Math** | Exact rational operations, algebra signs/inequalities, equivalent expressions and equation classes, domain/roots, polynomial division and exponents, seeded truth oracles, trusted scorer; guided versus mastery truth | Algebra/Assessment Backend authors; **Math review-only** and cannot approve own change |
| **Independent Pedagogy** | Observe → Predict → Manipulate → Explain → Practice → Diagnose → Transfer → Verify; targeted Socratic repair, scaffolding/fade, genuine unseen transfer and assessment hint isolation | Content/MVE/Frontend authors; **Pedagogy review-only** |
| **Muse QA + Accessibility** | Actual family 1/2/3-child journeys; same/shared device and logout; learner-only and parent views, linked child, whiteboard pointer/ink, keyboard/AT/reduced-motion/mobile iPad/Chromebook | Engineering owners author changes; **Muse independent verification** |
| **Standards Source-Fidelity** | Publisher URL/version/date and expectation wording, mathematical qualifiers, lettered subparts, course/grade authority; CA/TX/WA/DMV/IL/NY/ON isolation and no speculative mapping credit | Standards Mapping authors; **Standards reviewer review-only** |

**DevOps release lane (separate):** signed/integrity-pinned build artifacts, verified staging HTTPS/allowlist/upstream trust, DB migration/rollback drill, restore proof, synthetic data isolation and resource budget. Passing an audit does not mean a VPS has been configured or a pilot is legally cleared.

## Repeatable audit protocol

1. **Triage, cheaply:** confirm current `main` SHA, changed files/commits since last recorded audit, open defects and existing #278/#337 review decisions. Check required CI/AppSec on that exact SHA. Avoid needless full reruns and duplicate issue creation. An unchanged SHA with no new actionable evidence should yield **NO MATERIAL CHANGE**, without GitHub noise.
2. **Pin an audit session:** record baseline and scope (files/endpoints/grades/learning packages/jurisdictions), question/hypothesis, audit lane, auditor identity, evidence source, environment and prior verdict. Do not assert a result for uninspected files.
3. **Prove:** separately inspect contracts and request an authorized isolated CI/QA runner to execute focused deterministic regression/property tests or synthetic browser reproductions. Muse may use localhost-only Playwright on an already-running verified synthetic stack. Copy the exact command and meaningful output summary, counts, skipped/xfail flags, seed IDs and snapshots. A plausible issue without reproduction is **UNVERIFIED**, not a confirmed vulnerability. Security behavior needing a live-like environment must remain restricted and synthetic.
4. **Classify:** have the authorized Engineering coordinator create **one** bounded finding per distinct defect, using `.github/ISSUE_TEMPLATE/post_merge_audit_defect.md`. Link the discovering session, file/function, baseline SHA, test, actual versus expected behavior, severity, affected release scope, owner and privacy constraints. Search for existing matching findings first.
5. **Fix ownership:** assign to the engineering/content/standards author; never let independent reviewer author the mathematical/pedagogical/standards correction it signs off. Author works on a bounded new correction PR based on *current* `main`; do not resurrect merged historical PR branches.
6. **Verify correction:** exact-head CI and AppSec as relevant, unit/integration/regression (including historical evidence preservation), targeted Math/Pedagogy/Standards/Architecture verdicts when contracts change, and separate Muse QA for learner/browser changes. Reviewer verdict must name the SHA and exact accepted scope.
7. **Post-merge retest:** check merged `main` SHA, pertinent end-to-end regression and no history/assessment or draft-activation regression. Close the issue only with fix PR/merge SHA, test evidence and independent acceptance links. Post a concise material progress summary to [#433](https://github.com/AyalewGM/ai-tutor/issues/433), and coordinate owner dependencies with [#278](https://github.com/AyalewGM/ai-tutor/issues/278).
8. **Release decision:** Engineering/owner may approve *only the specifically verified* pilot/release scope after P0/P1 are resolved and all affected specialty gates are signed off. Deployment and legal/privacy approvals are separate.

### Suggested exact-revision evidence

Read the existing `.github/workflows/ci.yml` and `.github/workflows/security.yml` first. CI already exercises Ruff, canonical alias inventory, Alembic upgrade, synthetic seed, pytest, Gate 4 committed-regression, MVE contract/truth tests, Docker startup and Playwright synthetic E2E. The security workflow uses Semgrep and Trivy; CodeQL runs separately. **Reuse** these results for an unchanged exact SHA; do not imply that static analysis is an authorization/privacy or mathematical proof.

Have an authorized independent CI/QA operator run focused additional tests only when the approved isolated environment is available. For example, in a synthetic provisioned CI database, `pytest -q tests/test_taxonomy_gate4_committed_revision.py -o fail_on_skipped=true`; for a targeted browser test, use the existing `e2e` Playwright runner and synthetic/mocked credentials. Never run database commands against unverified production credentials.

### Audit-session report shape

- **Session:** audit lane, auditor, UTC date, exact `main` SHA, previous accepted baseline/delta.
- **Scope:** packages/endpoints/files and previous issue/review links; explicit exclusions.
- **Evidence:** tools, commands, fixture, environment, exact passed/failed/skipped/xfail counts, SHA or seed; source inspection versus executed tests distinguished.
- **Findings:** issue URL, severity, CONFIRMED or UNVERIFIED, expected/observed, impacted child or mastery boundary, fix owner.
- **Gates:** Security, Engineering/Architecture, Math, Pedagogy, Standards, Muse, DevOps, privacy/legal — `APPROVED`, `CHANGES_REQUIRED`, `PENDING` or `NOT_APPLICABLE_WITH_REASON`.
- **Action:** fix branch/PR or no-change conclusion, release hold(s), next exact test and owner. **No deployment/merge authorization implied.**

## Severity matrix

| Priority | Threshold | Action |
| --- | --- | --- |
| **P0 — Critical** | Confirmed cross-family/child-data disclosure, active credentials exposure, destructive learner-history corruption or practical critical exploit | Stop affected exposure/release and immediately escalate to owner/AppSec; protect details |
| **P1 — High** | Incorrect trusted scoring/mastery, unauthorized parent authority, active invite replay, serious misleading math/pedagogy, broken core parent/learner journey | Block affected feature/pilot; fix and independently verify |
| **P2 — Medium** | Material a11y defect, recoverable functional error, incorrect provisional standards assertion, targeted remediation/transfer weakness without direct exposure | Track and fix before broad rollout; constrained-pilot exception requires documented owner acceptance |
| **P3 — Low** | Cosmetic issue, minor harmless warning, small documentation inconvenience | Track and batch; no automatic release block |

A severity assignment is **provisional** until evidence establishes the actual impact; err toward restricted escalation where child security exposure is credible.

## First audit wave — inspection checklist, not findings

- [ ] Main CI (including post-merge migrations, historical upgrade and no skip of Gate 4) and AppSec baseline complete.
- [ ] Parent/learner cookie authority, logout, PIN and real same-browser isolation across two and three children.
- [ ] Concurrent PostgreSQL single-use invitation and simultaneous practice-pass redemption; revoked and expired pass behavior.
- [ ] Historical learner, attempts, diagnostic, mastery and variant evidence preserved; guided teaching never confers independent mastery.
- [ ] Equations, fractions, exponent laws, polynomial division, geometry, probability and scientific-notation exact seeds/oracles; prove alternate valid answers and misconception classification.
- [ ] Real learner transfer task mathematical distinctness and misconception-preserving fade; keyboard/touch/AT for MVE.
- [ ] Collaboration board access, stale-session writes, live pointer/unfinished ink and worksheet/photo upload paths.
- [ ] IL/NY and other merged draft inventories retain source-review and no-activation flags, with exact publisher evidence where claims are made.
- [ ] 2GB staging proxy HTTPS resource and restore/rollback evidence, without exposing personal data or inviting families.
- [ ] Legal/privacy owner decision for under-13 verifiable parent consent (see `docs/security/PILOT_COMPLIANCE_CHECKLIST.md`); engineering checkbox ≠ legal clearance.

## Independence and authority

A reviewer may report evidence and issue an exact-SHA verdict; the corresponding content/engineering author implements the fix. Audit agents must **not self-approve, merge, activate, deploy or silently restart paused scheduled jobs**. An issue checklist or GitHub document by itself **does not execute an AI agent**. An owner can later connect a runner or authorize a scheduled invocation per lane; default operation is manual/on-demand, state-aware, limited-scope and economical.

See also `docs/process/TEAM_AGENTS.md`, `docs/process/DEVELOPMENT_WORKFLOW.md`, `docs/qa/DEFINITION_OF_DONE.md`, `docs/security/PILOT_COMPLIANCE_CHECKLIST.md` and [#337](https://github.com/AyalewGM/ai-tutor/issues/337).
