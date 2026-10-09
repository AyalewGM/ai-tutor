# #282 — Independent canonical skill taxonomy (foundation)

Status: **DRAFT / NOT FOR RUNTIME**. Owner: Curriculum Content; review: Architecture Lead; independent QA: Muse.

## Decision

Mathematical skill existence is represented in an explicit, versioned taxonomy,
not inferred from `app.canonical_problem_families.FAMILIES`. A mathematically
valid skill **may have no generator**. The generator registry describes a
separate capability. A generator does not establish mathematical approval.

Separate gates are required for (1) reviewed mathematical skill, (2) generator
availability, (3) validated practice, (4) independent assessment/mastery
evidence, and (5) reviewed jurisdiction mapping. No gate implies the next.

## Initial implementation boundary

`app/canonical_skill_taxonomy.py` introduces an immutable definition model,
review metadata, explicit version and a read-only capability query. The
production taxonomy is intentionally **empty** until an independent
mathematical review populates definitions. Test-only generatorless skill
examples demonstrate the contract; they are not approved production skills.

No database migration, alias validator change, consumer integration, runtime
coverage claim or mastery rewrite is included. Existing persisted UUID
`skill_id` values, historical attempts and independent variant identifiers
remain untouched. This is an incremental foundation, **not #282 acceptance**.

## Required follow-up before activation

1. Inventory and independently define existing canonical skills; record
   mathematical scope, stable code, version and independent reviewer.
2. Design additive persistence/synchronization preserving existing UUID keys;
   test historical mastery/evidence and independent variant IDs across revisions.
3. Make alias validation resolve against the **reviewed** taxonomy rather than
   generator-derived codes; enforce ALL_OF and draft release fail-closed.
4. Muse independently exercises separation, generatorless definitions,
   assessment readiness, collision/version failures, and historical regression.
5. Engineering Lead approves architecture; exact-head CI/AppSec and independent
   acceptance required before mapping review/runtime use.

No jurisdiction mapping or coverage credit is approved by this PR.
