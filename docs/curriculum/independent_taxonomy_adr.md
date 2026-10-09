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


## Architecture resolution: atomic skills, profiles and historical evidence

Decision date: 2026-10-09. Decision status: **accepted architecture direction,
not mathematical approval and not runtime activation**.

### Identity rule

A canonical skill identity represents one independently assessable mathematical
competency. A bounded numerical domain may define a child skill when it changes
the observable assessment contract. A profile groups skills or evidence
dimensions for reporting; it is not a canonical skill row, cannot receive a
separate mastery event, and is not an alias target.

### Candidate disposition

- `MATH.ARITHMETIC.ADD_SUB_WITHIN_20` is **not an atomic canonical identity**.
  Content should replace it with draft child candidates
  `MATH.ARITHMETIC.ADD_WITHIN_20` and
  `MATH.ARITHMETIC.SUBTRACT_WITHIN_20`. A combined “add and subtract within
  20” result is a noncanonical ALL_OF profile over the two reviewed children.
- `MATH.NUMBER_SENSE.COUNT_COMPARE_TO_120` is **not an atomic canonical
  identity**. Content should replace it with draft candidates
  `MATH.NUMBER_SENSE.COUNT_FORWARD_BY_ONE_TO_120` and
  `MATH.NUMBER_SENSE.COMPARE_WHOLE_NUMBERS_TO_120`. Any combined result is a
  reporting-only ALL_OF profile.
- `MATH.ARITHMETIC.WORD_PROBLEM_WITHIN_20` may remain one draft canonical
  identity because the common competency is contextual one-step modeling.
  Structure and unknown position are required evidence dimensions, not separate
  mastery identities. Arithmetic-only evidence cannot satisfy it.
- `MATH.PLACE_VALUE.TENS_ONES` may remain one draft bounded child identity.
  Ten-as-a-unit, canonical decomposition and digit value are evidence dimensions
  of that competency.

These code dispositions reserve names for continued draft review only. They do
not mark any definition REVIEWED.

### Relationship to historical broad codes

Existing persisted broad codes such as `MATH.NS.ADDITION`,
`MATH.NS.SUBTRACTION`, `MATH.NS.WORD_PROBLEMS`, `MATH.NS.COUNTING`,
`MATH.NS.COMPARE_ORDER`, `MATH.NS.PLACE_VALUE` and
`MATH.NS.COMPOSE_DECOMPOSE` keep their UUIDs and historical meaning. They are
not renamed, rekeyed or silently declared equivalent to the bounded candidates.

After mathematical review, a bounded candidate may carry an explicit
`SPECIALIZES` relation to one or more broad codes. A specialization does not
copy mastery in either direction. Historical mastery on a broad code cannot be
used to infer a new child skill, and new child evidence cannot rewrite an old
broad-skill event.

### No-double-credit and evidence rules

1. One attempt has one primary atomic canonical skill identity. Evidence
   dimensions may be attached to that attempt, but the same attempt cannot
   create duplicate mastery events for a parent and child.
2. ALL_OF profiles are computed views over separately stored atomic results.
   They have no `canonical_skills` row, UUID, mastery event or independent
   variant namespace.
3. Aggregate counts show either the atomic achievements or a selected profile,
   never both as separate mastered skills.
4. Existing mastery, attempt, diagnostic and variant records are immutable.
   Adding reviewed skills is additive only; no retroactive backfill or inferred
   equivalence is allowed.
5. Existing independent variant identifiers remain unchanged. New skills use
   their own identity and variant namespace after authorization.

### Alias authority

The reviewed canonical taxonomy is the only authority for alias targets.
A curriculum alias may resolve to a reviewed atomic skill or to an explicit
ALL_OF set of reviewed atomic skills. It may not target a reporting profile,
DRAFT definition, generator family, or unreviewed broad/child relationship.
UNMAPPED, ambiguous, ALTERNATIVE and partially reviewed mappings remain
fail-closed and confer no coverage or mastery credit.

### Consequences for PR #308

Curriculum Content must revise the candidate set and scope cards to reflect the
two decompositions while preserving the independently reviewed word-problem
evidence matrix. Independent Mathematical Review must review the new atomic
definitions. Muse must verify additive persistence, UUID/evidence invariance,
ALL_OF fail-closed behavior and no-double-credit contracts on the exact head.
The production taxonomy remains empty until those gates and an explicit
activation decision are complete.

No jurisdiction mapping or coverage credit is approved by this PR.
