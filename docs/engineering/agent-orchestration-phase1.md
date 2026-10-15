# Mihur Agent Orchestration — Phase 1 (advisory only)

This GitHub Actions workflow observes PR changes and CI/AppSec completion, then posts an exact-head handoff comment. It **does not execute agents, approve reviews, merge, deploy, or activate drafts**.

## Trust and correctness boundaries

- The privileged `pull_request_target` workflow checks out the **default branch**, never PR head code. Checkout disables credential persistence.
- Token permissions: `contents: read`, `pull-requests: read`, `issues: write`. Only a PR comment is written.
- PR titles and changed paths are **untrusted routing hints**. Mixed standards/content/assessment scopes route to Engineering manual triage; no routing label grants authority.
- CI and AppSec must be the latest matching **exact head SHA and branch** workflow runs, chosen by timestamp, run attempt, and ID. Missing, pending, ambiguous, or overflowing run evidence fails closed.
- `workflow_run` processes all linked PRs; missing links are logged as manual fallback. It never infers associations from arbitrary branches.
- One repository-wide concurrency group serializes handoff writers across both event types. Exact-SHA/state markers, paginated comment scans, and a pre-write head/check re-read reduce duplicates and stale handoffs. GitHub API does not offer an atomic comment insert; in case of transient write failure, re-read and retry at most once.
- More than 1,000 comments or 100 run results produces a manual intervention error, not a speculative approval.
- An author may never independently approve their own work. Human reviewers post exact-SHA independent verdicts. A handoff comment is not an acceptance gate.
- No taxonomy activation, historical learner evidence, mastery, variant, curriculum, or release mutations.

## Operation and rollback

Track coordination in #377 and #278. The orchestrator may be enabled only after exact-head CI/AppSec and independent Architecture/security review of the privileged workflow. To stop it, disable the GitHub Action without changing existing agent schedules.

**Phase 2 remains separate:** authorized runners, identities, least-privilege credentials, isolated execution and independent review enforcement are not implemented in this PR.

## Durable next-run pending recovery

The coordinator records failed or uncertain comment deliveries in `mihur-pending-handoffs.jsonl`, which the workflow uploads as a GitHub Actions artifact (up to 90 days, subject to repository retention policy). A scheduled **hourly** run, as well as every PR/CI/AppSec event, first lists previous pending artifacts, validates their JSONL records, and reconciles each against the **current PR SHA and exact-head checks** before processing new work. Existing exact-SHA/state comments are recognized and not reposted. Stale SHA records are skipped; they are not approvals.

If recovery is still blocked, the new run creates a fresh pending artifact and defers new routing. Missing/unreadable artifacts, malformed records and pagination overflow fail closed. A lost comment POST response is reconciled before retry; an uncertain result never triggers a blind duplicate POST. The repository-wide concurrency group serializes writers.

**Limitations:** GitHub Actions artifacts are retention-limited, not an indefinite database. The hourly schedule reduces loss risk, but prolonged outages, disabled schedules, retention overrides or failed artifact uploads still require manual intervention. The workflow logs pending-delivery warnings; green CI/AppSec is not evidence that a handoff was delivered. No agent execution, approval, merge, mastery credit or activation is performed.

## Explicit delivery outcomes

Delivery returns `DELIVERED`, `ALREADY_PRESENT`, `OBSOLETE`,
`SUPERSEDED_BY_CURRENT_CHECKS`, `DEFERRED`, or `PENDING`. The first four are
terminal outcomes, but superseded is explicitly not delivery of the original marker. Recovery must not infer completion from
an absent or empty local JSONL file: a head/check/draft change can defer a handoff.
Deferred inspections are recorded for later reconciliation. Recoverable unresolved current-event
delivery warns, stops the batch and exits successfully; the workflow's always-upload step preserves
its pending ledger. Every retry revalidates the PR head, branch, draft state and checks.
These outcomes remain advisory routing evidence, never independent acceptance.

Recovery returns an explicit deferred result for recoverable pending delivery. The
caller stops dispatch with exit zero, preserving the ledger through the always-upload
step. Authentication/permission and other persistent HTTP 4xx denials (except transient
408/429), malformed artifacts and unknown outcomes remain blocking errors. This is not
permission to bypass a denial. An unavailable artifact still fails closed.

When current check results change the intended state, confirmed posting or recognition
of the current marker returns `SUPERSEDED_BY_CURRENT_CHECKS`. Structured run-log evidence
records PR/SHA/branch, intended and actual markers, selected check results, actual write
outcome and comment ID/URL. The old marker is never described as delivered. A SHA change
before delivery is obsolete, not a license to write for a different head.
