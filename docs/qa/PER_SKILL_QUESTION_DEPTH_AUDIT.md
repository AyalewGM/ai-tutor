# Mihur: per-skill question depth and repetition audit

Tracking issue: **[#446](https://github.com/AyalewGM/ai-tutor/issues/446)**. Baseline: `main@ecb8ad8d6e0acf5388e03bbc6dea14a9f5bb2913`.

## What is measured

Run `python -m scripts.audit_persisted_question_depth --database-url "$TEST_DATABASE_URL" --source-sha "<exact SHA>" --output /tmp/mihur-depth.json` against a **separately provisioned local, migrated, fully seeded synthetic PostgreSQL database**. This is an opt-in, READ-ONLY instrument. It refuses non-local database hosts and sets the database transaction read-only. It never reads or modifies parent/learner/attempt/mastery/variant tables. Never use it against a live production or real-family database.

The JSON contains **one row for every active curriculum-local skill**, including zero-problem skills; grouped grade/course statistics; and a sorted `thin_populated_priority` of populated skills with fewer than six distinct mathematical tasks (a *triage threshold*, not a release acceptance standard).

**QA-only fixtures:** the Sprint 1 marble-bag skill `MCPS_MATH_8 / M8.PROB.MARBLE_QA` is explicitly seeded for accessibility regression, not curriculum depth. Count it in the inventory, exclude it from instructional thin-skill priorities, and never use fixture absence/presence as official standards evidence.

Per local skill:
- grade or course; jurisdiction; curriculum code and version; local skill code and name;
- canonical code and mapping type (explicitly **NOT independently reviewed**), enabling reuse without jurisdiction-specific generators;
- stored curated/generated rows, non-extension selection upper bound, unique mathematical task keys, duplicate rows, conflicting answers and **complete-task reuse across diagnostic/guided versus independent/mastery pools** (mode labels alone do not confer fresh transfer);
- stored problem types, tagged families, difficulty tiers, metadata declaration counts for diagnostic/guided/independent/mastery and missing-mode metadata;
- legacy generator **sample execution** of implemented types already backed by stored problems, plus deterministic canonical family sample uniqueness by approved-code *candidate* (no assumed deployment route);
- repetition/cross-session assessment-risk flags and separate Math, Pedagogy, rendering and Muse QA = **NOT ASSESSED**.

**Graphical equivalence:** identical short text on different graph parameters/visual specs is *not* automatically considered a duplicate. The task key includes stored parameters/choices/visual payload. This still does **not** prove correct graphs or rendering.

## What must not be conflated

| Evidence | May claim | Must NOT claim |
| --- | --- | --- |
| Existing registered canonical `FAMILIES` | a generator spec exists | mapped learner availability or verified math |
| Legacy `GENERATORS` sampled on seeded problem types | a few deterministic calls execute | all seeds/answers correct or accessible |
| Stored local `Problem` rows | distinct persisted mathematical tasks | sufficient grade depth or assessment modes |
| `ProblemContentMetadata` mode fields | declared mode candidates | current selector enforces the flags |
| Current `select_next_problem` | stored non-extension queries, current-session attempted-ID exclusions and generator fallback | prevention of repeats across learner sessions |
| Passing CI | tested contracts executed | complete correctness, curriculum source fidelity, teaching depth, or real-device behavior |

**Existing selector concern to assess before deeper content:** `app/services/problem_selection.py` filters extension eligibility but not the `ProblemContentMetadata` diagnostic/guided/independent/mastery flags, and excludes attempted IDs only for a supplied session. Don't add a superficial quantity of questions while these learner-evidence and repetition semantics remain unverified; Assessment Backend and Frontend own any selector/scorer fixes and independent QA gates.

## Work order

1. **Engineering/QA audit:** run in the isolated *fully seeded* grade 1–9/Algebra I test environment, archive the exact-SHA JSON and actual seed commands. Report every active local skill (including 0), do not infer missing curriculum rows from generator-only registry. Review seed-script idempotence by rerunning seeded content on disposable DB and comparing row counts and stable IDs; fail if history or canonical ownership changes.
2. **Prioritize populated/thin rows first:** start from `thin_populated_priority` and inspect mathematical task repetitions, contexts, representation variation, answer kinds, visualization, errors and spacing. A one-template number swap is not adequate depth. Build a bounded full task matrix per canonical skill with actual learner-visible routes.
3. **Curriculum Content (#311/#312):** enrich original Grades 1–5 and 6–8 canonical *question families* (concrete/visual/symbolic and contextual/reasoning/unseen transfer), preserve exact oracles and misconception-specific Socratic remediation. No state-specific cloned content.
4. **Algebra Content (#313/#306/#337):** enrich Grade 9/Algebra I shared linear/equation/exponent/polynomial/scientific-notation and modeling families; preserve exact rational scoring, negative signs, variables-both-sides, meaningful fresh transfer and hints/evidence isolation.
5. **Standards Mapping (#377):** independently resolve missing DC and Virginia Grade 8 official requirements and verified canonical mappings. Keep original versions and source qualifiers; a pending mapping does not block building *already accepted shared mathematics*, but cannot activate new standards credit or invent Grade 8 scope.
6. **Assessment Backend / Frontend:** verify learner route selection across all modes, no guided→mastery leakage, nonrepeating progression across sessions, generator fallback, idempotent problem variants and scoring/rendering of every new answer kind.
7. **Independent Math → Independent Pedagogy → Muse QA → Engineering:** exact-head verdicts, focused property tests for seeds, renderer and keyboard/screen-reader tests, learner-visible integrated journeys, 1/2/3-child isolation as applicable. No self-approval, activation, production seeding, migration or merge before required gates.

**No report count generated solely from registry specs or seed-file text qualifies as a verified populated skill count.** The opt-in database report must run successfully and its source SHA, synthetic seed coverage and test environment be recorded before quantitative depth claims. Draft findings are triage evidence, not green curriculum coverage.

## Acceptance per improved skill

Record: one canonical skill identity, every approved mapping that reuses it, provenance and authorship, exact seed and family IDs, varied mathematical structures/contexts/visuals, deterministic answer oracle and misconception classification, diagnostics/hints, independent/mastery/review pools, unique unseen transfer, allowed answer forms, blocked alternatives, keyboard/screen-reader representation, exact scorer and rendered E2E evidence. Measure distinct **mathematical tasks** as well as text and numbers. Confirm old learner UUID, attempts, diagnostic attempts, mastery and variant history remain byte-for-byte untouched in a synthetic rollback/reseed regression. No broad claims of readiness for any unreviewed grade/skill.
