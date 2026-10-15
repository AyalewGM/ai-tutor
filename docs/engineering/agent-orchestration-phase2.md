# Mihur Phase 2 — execution architecture and isolated pilot

Status: **DRAFT / NON-ACTIVATED**. Coordinates #377 and #278. Phase 1 #396 is merged; security follow-up #401 remains an independent prerequisite to relying on Phase 1 recovery. Phase 1 is advisory, not agent execution.

## Authorized execution mechanism

GitHub events are signals only, never an authorization to run a language model. GitHub Actions can run a trusted dispatcher from the default branch. A real executor must be explicitly provisioned (GitHub App installation/token with scoped permissions; isolated GitHub-hosted runner or dedicated AWS worker; separately provisioned model credentials). Existing ChatGPT chats, scheduled conversations and GitHub comments are **not** independently executable runners. No ChatGPT session credential, model API key, or GitHub write identity is provisioned by this PR.

For production: use GitHub webhook / workflow_run signals to enqueue into a **single durable PostgreSQL task table** (existing Mihur infrastructure), with uniqueness (PR, head SHA, role, revision), transactional claims, lease expiry, attempt counters and an outbox for GitHub publication. Use GitHub App short-lived installation credentials per role; allowlisted operations and checkout at immutable SHA in isolated short-lived workers. Split author, reviewer and release roles into different identities and permission scopes. A review verdict must be independently signed/attributed and validated against the exact current head and evidence. Worker comments cannot themselves grant approval. All PR inputs and model outputs are untrusted.

## Bounded state machine

QUEUED → RUNNING → ACCEPTED / CHANGES_REQUIRED / STALE; expired RUNNING leases are reclaimable up to a retry cap. An accepted content task enqueues math; accepted math enqueues pedagogy; accepted pedagogy enqueues engineering. CHANGES_REQUIRED returns an event to author for a **new SHA** and stops review progression. Engineering is a gate, not merge/deploy authorization.

No learner data, mastery, taxonomy, canonical math, draft activation, merge, or deployment writes.

## Pilot shipped here

`scripts/agent_execution_pilot.py` uses a local SQLite durable ledger and an explicit deterministic demo adapter. To demonstrate the chain locally:

```sh
python scripts/agent_execution_pilot.py --pr 385 --sha aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa --demo
python -m pytest tests/test_agent_execution_pilot.py -q
```

This validates **durable local handoffs**, SHA invalidation, idempotent enqueue, single claim, lease recovery, and failure routing. Demo "ACCEPT" is simulation-only evidence, **not independent acceptance**, and must never be posted as an agent review or used to drive live handoff.

## Security and next implementation gates

1. Independent Architecture/AppSec acceptance and operational verification for #401. Check the redirect fix and cross-host credential handling; confirm pending-artifact recovery is healthy.
2. Obtain explicit owner approval for runner identity, GitHub App scopes, isolation and model-provider credentials (or a documented existing approved runner). Never use PR-code execution under a privileged workflow.
3. Implement a production PostgreSQL lease/outbox implementation with transactionally committed dispatch and external GitHub evidence publishing. Add webhook signature checking, exact-head freshness check, audit attribution, replay suppression and idempotency keys. Keep human review authoritative.
4. Replace the demo adapter with one authorized non-privileged content worker and one truly independent reviewer, proving independent identities and exact-SHA verdicts end-to-end.
5. Independently verify CI, AppSec, architecture, pedagogical boundaries, retry and outage recovery before enabling any event-driven runner.

**Rollback:** Phase 2 is not registered as a workflow or service. No production runner is activated. To disable a future integration, revoke the GitHub App installation/credentials and disable its queue consumer; preserve audit rows.

## Roles

Coverage → Standards Mapping → Content → Mathematical Review → Pedagogical Review → Assessment → Architecture / Frontend-MVE → Muse QA → Engineering/DevOps. This pilot deliberately executes only Content → Math → Pedagogy → Engineering; the full graph requires independently reviewed dependency policies, not inferred from PR titles.

BUILD ONCE → MAP MANY → DEPTH BEFORE BREADTH.
