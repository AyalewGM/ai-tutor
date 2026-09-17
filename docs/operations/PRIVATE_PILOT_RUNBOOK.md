# Private Pilot Operations Runbook

## Scope

This runbook covers the bounded Maryland/Ontario private pilot. It does not authorize subscriptions, advertising, new curricula, or production use beyond the approved pilot cohort.

## Configuration and secrets

- Copy `.env.example` to a local `.env`; never commit `.env` or credentials.
- Set a strong `POSTGRES_PASSWORD` for any non-local deployment. The Compose default is development-only and must not be used for a pilot host.
- Configure the LLM Gateway provider and provider credential only on the host/runtime secret store. Prefer `fallback` when external language generation is not required.
- Do not put student names, answers, prompts, provider keys, claim tokens, or parent credentials in logs or support tickets.

## Start and verify

```bash
docker compose up -d --build
docker compose ps
curl --fail http://localhost:8000/health
```

The database, LLM Gateway, and Tutor API must be healthy before admitting a pilot session. The LLM Gateway is a language renderer only; provider failure must fall back without changing mastery, progression, intervention, or curriculum decisions.

Apply database migrations before pilot traffic:

```bash
docker compose exec tutor-api alembic upgrade head
```

## Health and privacy-safe logs

- `db`: PostgreSQL `pg_isready` health check.
- `llm-gateway`: `/health` on the internal service network.
- `tutor-api`: `/health` on port 8000.
- Operational logs may include request/correlation identifiers, provider/model identifier, latency, status/error class, and service health.
- Do not log raw prompts, learner answers, child/parent PII, secrets, or child-link claim tokens.

## Backup and recovery

The PostgreSQL named volume is persistent across normal Compose stop/start, but persistence is not a backup.

Before a pilot release or migration, create an encrypted database backup using an operator-controlled destination outside the application containers. Restrict backup access to the pilot operator. Restore must be rehearsed with synthetic data before relying on it for real pilot recovery.

Recovery order:
1. Stop new pilot traffic.
2. Preserve privacy-safe logs and the current deployment version/commit identifier.
3. Restore the last verified database backup if authoritative learning data is damaged.
4. Start dependencies and run migrations appropriate to the restored application version.
5. Verify health checks and a synthetic parent/learner journey before reopening the pilot.

## Rollback

- Keep the last verified application commit/image available during a pilot release.
- If a release changes only application code, redeploy the last verified version and run the synthetic smoke journey.
- If a migration is involved, do not blindly downgrade a database containing pilot evidence. Stop traffic and use the migration-specific recovery plan or restore a verified pre-migration backup.
- LLM-provider degradation is not a reason to alter pedagogical state: use deterministic fallback rendering.

## Incident response

For suspected privacy, authorization, curriculum-isolation, or data-integrity incidents:
1. Stop affected pilot access and preserve evidence without copying child data into GitHub.
2. Rotate exposed credentials/tokens where applicable.
3. Determine affected family/curriculum scope and whether authoritative mastery/intervention evidence was changed.
4. Notify the designated pilot owner and document the incident using minimized identifiers.
5. Do not resume until authorization isolation, curriculum isolation, and authoritative evidence integrity are verified.
6. Escalate legal notification questions to qualified counsel; this runbook is engineering/compliance guidance, not legal advice.

## Lightweight data-impact check

| Question | Pilot answer |
| --- | --- |
| What data is collected? | Account/role data, parent-child relationship data, curriculum enrollment/scope, learner attempts and assistance markers, mastery/intervention evidence, minimized operational telemetry. |
| Why is it needed? | Deliver curriculum-scoped tutoring, distinguish assisted from independent work, authorize parent visibility, recover pilot operations, and measure learning/reliability/unit economics. |
| Where is it stored? | Authoritative application data in PostgreSQL; minimized runtime telemetry/logs in the deployment environment. |
| Retention/deletion | Keep only what is required for the bounded pilot and approved learning evidence. Operational telemetry follows the existing disposable 90-day pilot hypothesis unless a shorter period is operationally sufficient. Pilot exit must include deletion/review of disposable telemetry and an explicit decision for authoritative learning records. |
| Who can access it? | The learner for their learning flow, an explicitly linked/authorized parent for parent views, and least-privileged pilot operators for operations. |
| Third-party/LLM flow | Only the constrained language-rendering payload needed by the configured provider. Billing/marketing data is absent. Raw prompts/answers are not retained as telemetry. Deterministic fallback is available. |
| Less-data alternative | Prefer structured pedagogical decisions, minimized identifiers, aggregate/count telemetry, and deterministic fallback. Do not collect child marketing profiles, ad-tech identifiers, or unrelated demographic attributes. |

## Security/compliance release gate

Before admitting real pilot users, verify:
- parent endpoints reject unlinked children and remain family-scoped;
- curriculum queries remain scoped to the learner's resolved curriculum and never aggregate Maryland/Ontario evidence;
- TLS terminates in front of any remotely accessible pilot endpoint and host/database access is restricted;
- secrets are injected at runtime and absent from repository/history/logs;
- backups are encrypted/access-controlled and restore has been tested with synthetic data;
- dependency/CI checks are green;
- retention/deletion responsibilities and pilot incident owner are assigned;
- external LLM/vendor configuration and data handling are reviewed before enabling a provider.

COPPA applicability must be reviewed for child-directed/under-13 use. FERPA/PPRA questions must be revisited before a school controls or supplies education records. Ontario/Canadian youth-privacy obligations, including PIPEDA/provincial applicability, must be reviewed before the Ontario pilot expands beyond the approved private context. Unresolved legal interpretation requires owner/counsel review before release.
