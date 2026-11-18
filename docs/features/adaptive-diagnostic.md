# Strand-Level Adaptive Diagnostic ("Knowledge Check")

Extends the existing per-target-skill diagnostic (F-002, `app/diagnostic_api.py`,
`app/services/diagnostic_controller.py`) into a curriculum-wide adaptive
assessment that reports readiness by strand — the capability that anchors
IXL's product (Real-Time Diagnostic) and that we currently lack.

Design constraint inherited from F-002: **not a long benchmark exam.** We
exploit the prerequisite DAG and live mastery evidence so the number of
questions stays small and adaptive. The diagnostic must never label a child
with a global grade number; it reports skill/strand readiness with evidence.

## Goals

1. Probe multiple skills across the learner's enrolled curriculum in one
   resumable session (~15–25 items typical, bounded by `max_questions`).
2. Report per-strand readiness (Strong / Developing / Emerging / Not probed)
   plus the deepest meaningful prerequisite gap per strand.
3. Produce a parent-facing "knowledge map" report with recommended first
   skills — reusable as the placement report parents currently don't get.
4. Keep the diagnostic *continuous*: unanswered branches accumulate evidence
   from normal practice, so re-diagnosis is incremental, not a retest.

## Non-goals

- No grade-level score or percentile (V1 constraint from F-002 stands).
- No IRT item calibration — deterministic rules on existing mastery +
  difficulty signals first; revisit after real response data exists.
- No LLM authority over placement, scoring, or strand classification.
- Diagnostic items remain unassisted (no hints, no step-work), matching the
  existing `diagnostic_eligible` gating in `ProblemContentMetadata`.

## What we reuse

- `diagnostic_controller.py` — prerequisite-descent probe, misconception-directed
  descent, `max_questions` bound.
- `SkillPrerequisite` weighted DAG + `curriculum_scope` isolation.
- `ProblemContentMetadata.diagnostic_eligible` — fail-closed item gating.
- `StudentSkill.mastery_score` / `confidence_score` + `MasteryEvent` ledger —
  diagnostic evidence is written as `DIAGNOSTIC_EVIDENCE` events today.
- `CurriculumExpectation.strand` — strand grouping already exists in the
  expectation layer.
- `reviews_due` / decay model — confidence decay can reuse the forgetting
  half-life so "stale" strand estimates show reduced confidence.

## Proposed flow

1. **Entry**: LearnEntry "Check where {name} stands" (alongside Placement
   check). Optional starting goal (target skill) or free-roam.
2. **Target selection**: rank candidate skills by information value —
   `uncertainty(1 - confidence)` × `centrality(outgoing prerequisite edges)` —
   restricted to `content_ready` skills with ≥ N diagnostic-eligible items.
3. **Probe**: serve the controller's adaptive items for the chosen target;
   descend/ascend the graph exactly as today. Per-strand stop rule: stop
   when the branch's classification confidence is sufficient.
4. **Classify**: each probed skill → ready / not-ready + evidence;
   each strand aggregates its member skills with a coverage denominator
   (e.g., "3 of 12 skills probed").
5. **Report**: strand cards with readiness, the deepest gap per strand, and
   "start here" recommendations feeding `recommend_next_skill`.
6. **Continuity**: subsequent practice writes normal `ATTEMPT_EVIDENCE`;
   the report recomputes live rather than freezing a snapshot.

## Data model (sketch)

- `DiagnosticCampaign` — learner, curriculum, started/ended, question count,
  resumable session id (reuse `TutorSession` with a campaign pointer or a
  `DIAGNOSTIC` session kind).
- `DiagnosticSkillResult` — campaign, skill, verdict, evidence attempt ids,
  confidence.
- Strand aggregation is computed, not stored (strands come from
  `CurriculumExpectation`).

## API sketch

- `POST /diagnostic/campaigns` → `{campaign_id, session_id}`
- `POST /diagnostic/campaigns/{id}/respond` (reuse existing respond shape)
- `GET /diagnostic/campaigns/{id}/report` → strands + gaps + recommendations
- `GET /learners/{id}/knowledge-map` → latest campaign report or live
  mastery-derived readiness when no campaign exists

## Phased rollout

- **P0** — multi-target probing within one campaign using the existing
  controller machinery; report page (learner-facing, simple strand list).
- **P1** — parent-facing knowledge map section on the dashboard; report
  recompute from live evidence; "deepest gap" narrative per strand.
- **P2** — confidence decay on stale evidence; re-check nudges ("it's been
  4 weeks since we checked fractions"); seed campaign targets from review
  schedule.
- **P3 (research)** — evaluate IRT-style calibration only if deterministic
  rules prove insufficient with real data (deferred per F-002).

## Open questions

- Strand definition: use `CurriculumExpectation.strand` as-is, or a
  coarser curated strand taxonomy? Some curricula have sparse expectation
  coverage (MTH1W has 39/43 expectations unmapped).
- How much diagnostic-eligible content exists per skill? Skills thin on
  `diagnostic_eligible` items may need `warm_problem_banks` coverage first
  — worth auditing before P0.
- Resume semantics: a campaign may span days; how does it interact with the
  existing single-`ACTIVE`-session invariant?
