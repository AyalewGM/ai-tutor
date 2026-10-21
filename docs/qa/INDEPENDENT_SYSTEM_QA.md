# Mihur Independent System QA — executable audit runbook

**Tracking:** [#465](https://github.com/AyalewGM/ai-tutor/issues/465), [six-lane audit #433](https://github.com/AyalewGM/ai-tutor/issues/433), [Engineering board #278](https://github.com/AyalewGM/ai-tutor/issues/278).  
**Agent:** `.github/agents/mihur-independent-system-qa.agent.md`  
**Status:** agent definition and repeatable procedure, **not** evidence of an executed audit.

## What is new

The six existing auditors focus on source review or authorized localhost browser inspections; this seventh role is an **independent system QA test operator**. Its configured tools include shell execution so it can actually run the existing Python, TypeScript, Docker and Playwright suites *where an isolated runner is available*. It reads current `main` and **every open PR** each invocation, then prioritizes executable tests by risk. It does not author fixes or claim independent specialist approvals. A profile merged to `main` becomes manually selectable in compatible GitHub Copilot environments; creating it does not schedule anything or provision an isolated runner.

## 1. Mandatory environment guard before tests

Print a nonsecret runner fingerprint (OS, Python, Node, Docker/Compose availability, selected browser, current git SHA). Check that repository checkout and all environment files are **test-only**. Do not print environment variable values. Check all configured PostgreSQL/Redis/API hosts and credentials through a safe hostname/port policy: allow only explicitly provisioned disposable test containers or localhost, never public, staging, production or family-linked hosts. No real child, parent, attempt or mastery records are allowed.

Before commands that can write data (`alembic`, `seed_*.py`, `pytest`, `docker compose up`, Playwright), verify a **separate disposable** PostgreSQL/Redis/database and no real family users. A localhost port on a developer machine is not automatically disposable: isolation must be proven. Disconnect staging/production credentials, use test-only secrets and restrict network egress. Keep all test outputs under a disposable workspace, never in the tracked source tree; inspect code before executing any script from a PR. If any condition is unknown, **skip mutation-capable execution**, evaluate exact-head CI logs and mark `NOT_EXECUTED`.

No permissions to deploy, edit repository configuration, rerun workflows, migrate real databases, invite families or update real learner history. Never run anything against `dev.mihureducation.com` just because it is called dev.

## 2. Snapshot the entire review universe

Before touching a PR, get the full 40-character `main` HEAD and list *every* open PR, including drafts:

```sh
git rev-parse HEAD
gh pr list --state open --limit 200 \
  --json number,title,headRefOid,baseRefName,isDraft,url
```

If `gh` is unavailable, use the authorized read-only `github/*` tool. If the list is paged, exhaust pagination; without complete enumeration report `INCOMPLETE_PR_INVENTORY`. The main SHA and every PR SHA must be independently verified from origin, not a previously authored PR body. Fetch exact-head CI/AppSec/CodeQL, reviews, changed files, base/merge-base and existing findings. Recheck the PR head before reporting so newer pushes invalidate earlier evidence. Do not report a PR as merged based on remembered state.

Create a coverage ledger with a **main row** and **one row for EVERY open PR**; include these fields:

| Field | Required value |
| --- | --- |
| identity | main or PR number, exact 40-hex SHA, base main SHA, branch/draft |
| change | touched paths, implementation lane, risks, conflicts/rebase state |
| independent evidence | current SHA Math/Pedagogy/Standards/AppSec/Muse/Engineering scope, missing approvals |
| CI | exact-head per-job conclusion and failures, skipped/xfail counts where available |
| agent execution | `EXECUTED`, `CI_EVIDENCE_ONLY`, `SOURCE_INSPECTION_ONLY`, `NOT_EXECUTED` or `BLOCKED` |
| evidence | command/artifact/runner/fixture/seed and pass/fail/skip/xfail |
| disposition | confirmed defects, release gates, owner and next action |

An unchanged PR can reuse existing **same-SHA** evidence, but still gets a row and risk appraisal. Documentation-only drafts still require source-fidelity/authority review; no automatic execution or learner activation.

## 3. Detached, exact-SHA test checkout (only in safe runner)

Use a **separate disposable clone or detached worktree for each tested target**. Never modify the developer's `main` or a historical merged PR branch. An illustrative safe clone flow:

```sh
QA_DIR="$(mktemp -d)"
git clone --no-local https://github.com/AyalewGM/ai-tutor.git "$QA_DIR/repo"
cd "$QA_DIR/repo"
git fetch origin main
git switch --detach "$EXPECTED_40_HEX_SHA"
test "$(git rev-parse HEAD)" = "$EXPECTED_40_HEX_SHA"
# Tests may now run ONLY after the isolated database/browser guard above.
```

For an open PR fetch `refs/pull/N/head` into the *disposable clone*, independently check its `HEAD` equals the listed full SHA, then compare `git diff --name-status` to the current main merge base. A PR result is not valid for its successor SHA. A successful test in one branch says nothing about sibling PRs.

Do not execute arbitrary PR scripts or a changed CI workflow with repository production secrets. Tests in a disposable, unprivileged environment remain a separate authorization requirement.

## 4. Run actual tests, not just file searches

**Use the existing committed QA/CI as baseline**, including `.github/workflows/ci.yml`, `.github/workflows/security.yml`, `docs/qa/DEFINITION_OF_DONE.md`, and `docs/qa/POST_MERGE_QUALITY_AUDIT.md`. The appropriate command set depends on safe resources and touched files; never fabricate a full run.

| Area | Executable checks / meaningful assertions |
| --- | --- |
| Backend static/unit | `ruff check .`; `pytest -q`; focused `pytest -q tests/<relevant_test>.py`. Examine `xfail`, skips and warnings. |
| Alembic and seeds | In **disposable PostgreSQL only**: `alembic upgrade head`, source-defined seed scripts, second-run content-ID/row diff, historical learner/Attempt/DiagnosticAttempt/MasteryEvent invariants, rollback/restore **only when separately authorized**. |
| Canonical/Math | `python scripts/validate_canonical_alias_map.py`; targeted mathematical generator/answer contract tests, adversarial seeds and independent exact-oracle reconstruction (do not use scorer as its own oracle). |
| Frontend/MVE | `cd frontend && npm ci && npm run build && npm run check:mve && npm run test:mve`; exact authorized capability, keyboard model state, no answer leaks to assessment. |
| Browser | On an **isolated running localhost app**: `cd e2e && npm ci && npx playwright test`; examine E2E route mocking and distinguish fully integrated from synthetic mocked assertions. Existing `node e2e/mve-guided-browser.mjs`, `node e2e/equation-learning-flow-browser.mjs`, `node e2e/learn-together-browser.cjs` are additional focused checks where applicable. |
| Family/session | Invite-only parent registration + consent + PIN, 1/2/3 kids, separate opaque links, replay/expiry/revoke, same-browser and different-browser sessions, denied sibling/foreign-family access, logout, parental access isolation and rate limiting. |
| Assessment | Guided Socratic prompts do not count as independent evidence, learner and session bound exact scoring, alternate equivalent forms, unsupported IDs fail closed, draft content inactive, fresh unseen transfer. |
| Whiteboard/operations | Nginx/Caddy/WebSocket public Host vs Origin static checks; **only when DevOps authorizes isolated endpoint**: successful 101/relay, unauthorized Origin/board rejection, upload limits, reconnect, keyboard/AT state. Public staging validation belongs to DevOps and independent Muse, not this agent. |
| Security | Review same-SHA CodeQL/Semgrep/Trivy outcomes and scoped security regression tests; do not confuse a green baseline with a penetration test, privacy/legal consent acceptance or approved deployment. |
| Standards | Official source/version/citation/full clause parity and canonical mapping boundaries. If original issuer evidence is unavailable, mark `INSUFFICIENT_EVIDENCE`, never claim official coverage. |

Recommended efficient strategy: inspect diff and exact-head workflows for *every* PR first; run focused test cases for changed code PRs (and high-risk negative scenarios), then a complete isolated main smoke and full regression if resources permit. If insufficient resources, prioritize P0/P1 and mark remaining rows **NOT_EXECUTED** with reason. Do not silently lower coverage.

## 5. No implicit approval, exact reporting

Each finding needs: `CONFIRMED`/`UNVERIFIED`/`KNOWN`, P0–P3, exact HEAD, file and line, command/seed/fixture, actual vs expected result, blast radius, cross-family/learner/history risk, implementation owner, independent reviewer and release blocker. Use `NOT_EXECUTED` when tests were not run; do not relabel a CI run as your own. Capture test counts, SHA-pinned workflow links, environment/browser version, timestamp and skips/xfails. Do not publish secrets, personal data, private link tokens or exploitable security proof.

The output to the Engineering coordinator must include the **full main+all-open-PR matrix**, prioritized defects, regression requests, verified/rejected hypotheses and named follow-up owners. Existing six specialists issue their own independent verdicts; this agent cannot approve its own code or waive those gates. The coordinator alone creates findings and assigns fixes using the existing [post-merge audit template](../../.github/ISSUE_TEMPLATE/post_merge_audit_defect.md).

**Release state:** A draft-only file, unapproved mapping, tool-based Boolean release preflight or green CI is not a learner-facing route. No changes to learner history, production, invited families, deployment, billing, taxonomy or mode permissions are authorized by running this audit.
