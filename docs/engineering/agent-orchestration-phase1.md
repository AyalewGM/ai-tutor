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
