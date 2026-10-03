# AI Tutor — Master Product Backlog

This file is the **master coordination document** for Ayalew, Devin, ChatGPT/autopilot, and other contributors.

GitHub Issues hold detailed requirements/research and Pull Requests hold implementation evidence, but this file owns the high-level product status and execution order. Before starting work, read this file first, then inspect the linked issue/PR and current `main`.

## Status model

`PLANNED → RESEARCHING → READY → IN PROGRESS → PR/QA → DONE`

`BLOCKED` may be applied at any stage. `DONE` requires the applicable checks in `docs/qa/DEFINITION_OF_DONE.md`; a merged PR or green CI alone is not sufficient.

## Current execution

> Reconciled 2026-10-02 against GitHub and `main` at `38a70b09`. F-026 is the active private-family release gate. Closed historical issues are not active merely because an older version of this file said otherwise.

| Priority | Work item | GitHub | Status | Current evidence / next gate |
|---|---|---|---|---|
| P0 | F-026 Private Family Pilot Release Candidate | Issue #107; PRs #108–#111 merged | **IN PROGRESS — ACTIVE RC GATE** | Explore Topics, pilot operations, telemetry hardening and synthetic-family E2E are merged. Significant post-gate product work landed through PRs #121 and #123–#128, so prior RC acceptance must be rerun against current `main`. Next: exact-head CI/regression, adaptive-step correctness, family/curriculum isolation, Security/Data Impact, QA/PO/PM acceptance, VPS/backup-restore verification, then explicit owner go-live approval before inviting real families. |
| P0 | F-027 Pre-pilot gap closure | Issue #122; PRs #121, #123–#128 merged; PR #129 open | **PR/QA — CONVERGE INTO F-026** | Typed item kinds, Learn panels, parent reporting, gamification depth, content warming, PWA, placement diagnostic and stepwise adaptivity are substantially implemented. Issue text is stale where it calls within-problem adaptivity deferred: PR #128 implemented it. Do not add new competitive features before pilot; verify/accept shipped scope. PR #129 (parent step-work trails) needs privacy/data-impact and RC-value review before merge. |
| P1 after RC | Avatar visual redesign/polish | Avatar infrastructure shipped in PR #126 | **DEFERRED POST-PILOT** | Selection/persistence/allowlist are acceptable for the private pilot. Owner considers the current artwork non-final; do not spend F-026 time redesigning it. |
| P1 after RC | Product/UX follow-ups discovered by pilot | Pilot feedback | **DEFERRED POST-PILOT** | Prioritize from observed family friction and learning evidence rather than feature-for-feature competitor chasing. |
| P2 after RC | Business Model, Pilot Economics & Deployment Strategy | Issue #12 | **RESEARCHING / OWNER-GATED** | Revisit pricing, buyer and public-beta decisions after private-pilot evidence. |

## Canonical GitHub issue ledger

**Use the GitHub issue number + full title to disambiguate work.** Historical feature numbers evolved independently in older backlog iterations, so an `F-019` label alone is not a safe identifier.

| Issue | Work item | Status |
|---|---|---|
| #2 | F-001 Prerequisite-Aware Adaptive Linear Equations | DONE |
| #3 | F-002 Adaptive Diagnostic Placement | DONE |
| #5 | F-003 Graduated Hint Ladder and Productive Struggle | DONE |
| #6 | F-002 Adaptive Diagnostic Placement duplicate/continuation | DONE |
| #8 | F-004 Independent Mastery Gate | DONE |
| #10 | F-005 Parent Profiles, Child Management, and Progress Dashboard | DONE |
| #11 | F-006 Hierarchical Curriculum Registry and Jurisdiction Isolation | DONE |
| #12 | EPIC Business Model, Pilot Economics & Deployment Strategy | RESEARCHING |
| #15 | F-007 Pilot Curriculum Content Packs and Standards-Aligned Ingestion | DONE |
| #17 | F-008 Student Learning Experience & Tutor UI | DONE |
| #18 | F-009 Parent Progress Intelligence & Actionable Insights | DONE |
| #19 | F-010 Learning Analytics & Deterministic Intervention Engine | DONE; 2026-09-20 PO regression guidance carried into F-021 |
| #20 | F-011 Pilot Observability, Learning KPIs & Unit Economics | DONE |
| #21 | F-012 Proposed Maryland Mathematics Grade Expansion Framework | DONE / research framework |
| #22 | F-007A Authoritative Pilot Content Packs & Maryland Course Decision | DONE |
| #24 | F-013 Containerized Microservice Architecture & Deployment | DONE |
| #28 | F-014 F-011 Observability Completion & Pilot Hardening | DONE |
| #30 | F-015 Ontario Grade 9 MTH1W Curriculum Pack | DONE |
| #35 | F-016 Private Pilot Launch Readiness | DONE |
| #37 | F-017 Pilot Web Application & Family/Learner Onboarding | DONE |
| #39 | F-018 Private Pilot Privacy Controls & Data Lifecycle | DONE |
| #41 | F-019 MD/DC/VA Grades 6–7 & High-School-Entry Math Expansion | DONE |
| #42 | F-020 Dynamic Math Visualization & Instructional Animation Engine | DONE |
| #43 | Fix MTH1W canonical curriculum seeding and learner skill discovery | DONE |
| #45 | F-021 MTH1W fine-grained skill graph and adaptive problem variation | DONE |
| #46 | F-022 Goozam-family UI/UX redesign for learner and parent experience | DONE |
| #55 | F-030 Learner Gamification & Badge System (evidence-backed awards) | DONE |
| #81 | F-013 Production UI Template, Design System & Pilot Experience | DONE |
| #86 | F-023 Commercial learner dashboard & tutoring workspace polish | DONE |
| #90 | F-024 DMV Grades 1–5 Curriculum Expansion & Elementary Learning Experience | DONE |
| #91 | F-025 Ontario MTH1W Classroom-Aligned Algebra Content Expansion | DONE |
| #107 | F-026 Private Family Pilot Release Candidate | **IN PROGRESS — ACTIVE RC GATE** |
| #122 | F-027 Pre-pilot gap closure — item types, learn panels, parent reporting, gamification, content depth | **PR/QA — CONVERGE INTO F-026** |

## Repository implementation ledger

The entries below describe capabilities already present in the repository. Their historical F-numbers are retained for traceability and **must not be used to infer the identity of newer GitHub issues with the same F-number**.

| Historical ID | Capability | Status |
|---|---|---|
| F-001 | Prerequisite-aware adaptive linear equations | DONE |
| F-002 | Diagnostic placement and readiness | DONE |
| F-003 | Graduated hint ladder / productive struggle | DONE |
| F-004 | Independent mastery gate | DONE |
| F-005 | Student tutor workspace | DONE |
| F-006 | Progress and learning explanation | DONE |
| F-007 | Spaced review / retention | DONE |
| F-010 | Broader misconception catalog | DONE |
| F-011 | Difficulty-aware mastery and adaptive progression | DONE |
| F-012 | Retention visibility | DONE |
| F-013 | Continuous diagnostic placement | DONE |
| F-014 | Psychometric evidence model (BKT-lite) | DONE |
| F-015 | Parametric problem generation | DONE / expanded further by PR #50 |
| F-016 | Browser auth and learner onboarding flow | DONE |
| F-017 | Problem-aware fallback coaching | DONE |
| F-018 | Learner workspace visual polish | DONE / further UI work tracked in Issue #46 |
| F-021 | MTH1W fine-grained subskill graph (9 atomic subskills chained under strand anchors, generator-typed problems, strand misconceptions, expectation mappings) | DONE in repo on `adaptive_response` — Issue #45 acceptance/DoD still open |
| F-022 | Missed-template re-serving (generator metadata on GENERATED problems; `regenerate_variant` re-serves missed items with fresh parameters at same difficulty) | DONE in repo on `adaptive_response` |
| F-023 | LLM word-problem contextualization (`/v1/contextualize` gateway endpoint; LLM writes narrative over code-owned parameters/answer with number-faithfulness validation; Gemini provider live) | DONE in repo on `adaptive_response` |
| F-024 | Fine-grained subskills extended to MCPS_MATH_8 (5), MCPS_MATH_7 (6), MCPS_ALGEBRA_1_2026_27 (6); placement now descends into anchor subskill chains | DONE in repo on `adaptive_response` |
| F-025 | Problem-family identity + family-aware equivalence + content-readiness gating (GENERATOR_FAMILIES registry; solution.family/parameters on generated rows; (family, params) dedup; last-family rotation in selection; `SkillChoice.content_ready` gates the picker) | DONE in repo on `adaptive_response` |
| F-026 (rolls up to F-030) | Gamified learner presentation layer — React workspace (`/app/`): streak + best-streak chips, score chip, confetti burst on correct answers, badge medallion on skill completion | DONE on `UI_1` |
| F-027 (rolls up to F-030) | Persisted evidence-backed badges — `learner_awards` table (migration 0017), `services/awards.py` catalog (FIRST_CORRECT, STREAK_3/5, LEVEL_UP, SKILL_MASTERED, GAP_FIXED, FRESH_EYES) evaluated in `respond()` from committed evidence only; `RespondOut.new_awards` + workspace `awards` shelf; React badge toast + shelf UI | DONE in repo on `UI_1` — rewards economy (points, leaderboards) remains deferred |
| F-028 (rolls up to F-030) | Badge collection page — `GET /learner-workspace/sessions/{id}/badges` returns full catalog with earned state, per-skill instances, and streak progress; React `/learn/:sessionId/badges` grid (earned vs locked, progress bars) linked from workspace shelf | DONE on `UI_1` |
| F-029 (rolls up to F-030) | Skill mastery map — `GET /learner-workspace/sessions/{id}/skill-map` returns every curriculum skill ordered by difficulty with mastery score/status/active flag; React `/learn/:sessionId/map` renders an IXL-style color-coded tile grid (mastered/in-progress/not-started) with "You are here" marker | DONE on `UI_1` |
| F-032 | Step-aware tutor voice — `TutorContext.step_evidence` (previous line, attempted line, classifier code, invalid streak) reconstructed from persisted `WORK_STEP` turns by `stepwork.latest_step_evidence`, cleared once the learner corrects the line; fallback voice quotes the learner's own line and names the move from hint level 2 / EXPLAIN_CONCEPT via per-code templates; gateway `RenderRequest.step_evidence` carries a compact description with an instruction to refer to the line without re-grading it. Also: algebra visuals (see F-020 row); misconception-depth pass — step classifier now emits ALG_001/ALG_002 (unlike terms merged / constant sign dropped, equations + expressions), EQ_003 (multiplied by coefficient), EQ_004 (coefficient treated as addend), DIST_002 (distribution sign flip), ARITH_001 (right move, wrong value), FRAC_001 (common denominator, unscaled numerators) alongside EQ_001/EQ_002/DIST_001/NUM_003/WP_001, each with feedback + tutor-voice templates and catalog rows seeded on every step-capable pilot curriculum | DONE in repo on `feature/f-032-step-aware-voice-visuals` |
| F-033 | Daily goal + session recap + math keypad — `students.daily_goal_questions` (migration 0022) + `PATCH /learner-workspace/sessions/{id}/daily-goal`; goal chip (done/target today, UTC day) in workspace header; `GET …/summary` recap derived from persisted evidence (attempts, correct/solo, XP incl. badge XP, SmartScore start→now on `starting_mastery`, skills practiced, misconceptions seen + resolved-after-flag, session awards, minutes); React "Wrap up" recap dialog + "Keep practicing"/"Done for now"; `MathKeypad` inserts tokens at cursor into the free-text answer and StepWork draft inputs | DONE in repo on `feature/f-032-step-aware-voice-visuals` |
| F-034 | Remediation voice — workspace `focus.primary_skill_name` + honest banner when `in_remediation`: "Stepping back on purpose: practicing X first makes Y much easier" (SPACED_REVIEW gets a "quick review" variant). Learner sees the plan instead of a silent skill swap | DONE in repo on `feature/f-032-step-aware-voice-visuals` |
| F-035 | Escalation-policy research audit — immediate flagging, 4-rung ladder, and 2+2 intervention thresholds confirmed against literature (Mathan & Koedinger; Koedinger & Aleven assistance dilemma; Beck & Gong wheel-spinning); changed: hint escalation requires an intervening attempt (`attempt_since_last_hint`, trigger `REPEAT_LEVEL`) to block click-through to bottom-out; reveal feedback gained a self-explanation cue (Renkl & Atkinson fading). Deferred: per-skill wheel-spinning detector for the parent surface, response-time abuse model (blocked by data minimization), prior-knowledge-adaptive cadence | DONE in repo on `feature/f-032-step-aware-voice-visuals`; see docs/adr/ADR-015 |
| F-036 | Content deployment pipeline — `scripts/ops/seed_all_curricula.py` orchestrates all 20 seeds in dependency order (jurisdiction curricula → canonical map → elementary packs → authored word/MC/learn layers → answer-kind backfill, `--warm` opt-in for generator deepening); `deploy.sh` runs it after `migrate` so authored content actually reaches the pilot DB; Dockerfile now ships `docs/curriculum/packs` (previously the pack loader could not run in the API image) | DONE in repo on `feature/f-032-step-aware-voice-visuals` |
| F-037 | Photo intake MVP — `POST /sessions/{id}/work-photo/scan` (multipart image → `photo_ocr` provider → editable lines; image never persisted); pluggable OCR (Mathpix via `MATHPIX_APP_ID`/`MATHPIX_APP_KEY`, `stub` for dev, disabled → 503); conservative asciimath/LaTeX→checker normalization with `needs_review` flags; StepWork "Check a photo of written work" flow with confirm-and-edit review panel feeding confirmed lines through the ordinary `/work-step` endpoint so OCR output is never graded directly (ADR-016) | DONE in repo on `feature/f-032-step-aware-voice-visuals`; needs Mathpix keys to enable in prod |
| F-038 | Skill type-breadth deepening — `scripts/ops/deepen_skill_breadth.py` attaches grade-gated companion problem types (arithmetic↔word problems, equation strands→SOLVE_EQUATION/ALGEBRA_WORD_PROBLEM, fraction/geometry/time families) to skills carrying ≤2 types; fixed-point companion closure + fingerprint dedup make it idempotent; runs as an orchestrator step before `--warm`, which now generates 4 variants × 5 difficulties per skill (dev DB: ~18k problems, median 59/skill, median 3 types/skill) | DONE in repo on `feature/f-032-step-aware-voice-visuals` |
| F-039 | CPA pedagogy layer + reverse-Socratic challenges — `tutor_sessions.cpa_level` (ABSTRACT→PICTORIAL→CONCRETE, migration 0023): 2 consecutive invalid steps downgrade one rung, 2 valids or a solve recover; PICTORIAL/CONCRETE emit `step_visual` specs anchored at the learner's latest accepted line (`CPAVisualizer` renders via ADR-014 spec types); `misconceptions.py` central taxonomy (code→name+Socratic hint+visual cue); `pedagogy_engine.craft_flawed_step` plants real-catalogue errors after 3 valid streaks; `REVERSE_CHALLENGE` turns resolve spotted/missed/unresolved server-side (ADR-017) | DONE in repo on `feature/f-032-step-aware-voice-visuals` |
| F-031 | Stepwise work checking (within-problem adaptivity) — `services/stepwork.py` grades each submitted work line by mathematical equivalence (proportional normalized polynomials for equations; value-equality + simplified-form for expressions; bounded SymPy fallback widens syntax to `x^2`/decimals while keeping native-Poly semantics); model→compute checking for WORD_PROBLEM (model line must evaluate to canonical answer); ALGEBRA_WORD_PROBLEM declare→setup→solve state machine (declarations format-checked, setup equation must solve to canonical — wrong model → WP_001 — solve steps reuse equation equivalence); graduated 1→retry/2→targeted/3→reveal intervention derived server-side from persisted `WORK_STEP` tutor turns; step errors raise `assistance_level`; classified step misconceptions feed `record_evidence` as fallback; `StepWork` UI gated by `supports_steps`; parent dashboard `step_trails` + `recent_patterns` (7-day top-misconception aggregate) | DONE — PRs #128, #129; see docs/adr/ADR-013-stepwise-work-checking.md; thresholds audited in ADR-015 |

## Remaining historical backlog capabilities

These older backlog entries remain useful product capabilities but do not own the same identifiers as newer GitHub issues. Before implementation, create or link a uniquely identified canonical GitHub issue and update this master table.

| Historical label | Capability | Status |
|---|---|---|
| old F-008 | Worksheet / Photo Problem Intake | PARTIAL — photo→confirm→check MVP landed as F-037 (ADR-016); full worksheet persistence, multi-problem page detection, and per-stroke feedback remain out of scope |
| old F-019 | React Learner Frontend (Vite + React + TypeScript service) | DONE — Vite+React+TS app in `frontend/`, served by nginx with same-origin `/api/` proxy. Login, learn entry, diagnostic, learner workspace (state stepper, mastery ring, SmartScore, step work, scratch pad, visuals), badges, skill map, parent dashboard (step trails, recent patterns), parent settings, privacy all ported; Playwright e2e runs against the React app. Server-rendered pages removed (PR #129). |
| old F-020 | Missed-Template Re-serving with fresh parameters | IMPLEMENTED — see ledger row F-022 |
| old F-009 | Mathematical Visualization | NOT IMPLEMENTED; concept overlaps newer Issue #42 |

## Deferred until after private MVP validation

- gamification rewards economy (points, XP, leaderboards, purchases) — PO override 2026-09-20: the badge *presentation layer and evidence-backed award ledger* moved forward under F-030 (see Current execution; data-impact gate required); the rewards economy remains deferred;
- native mobile applications;
- voice-first tutoring;
- school/district roster and LMS integration;
- multi-subject expansion;
- agentic pedagogy that can override deterministic learning controls (explicitly disallowed unless product architecture is intentionally changed).

## Product and architecture guardrails

- Application code owns pedagogy, mathematics, answer truth, prerequisite logic, progression, mastery and curriculum mapping.
- LLMs are constrained to permitted language/explanation/hint roles and may not silently become the authority for assessment or mastery.
- Follow **define once, map many** for reusable canonical math concepts/problem generators while preserving explicit jurisdiction/version mappings.
- Learner mastery/evidence remains scoped to the exact curriculum/version; shared concepts never silently transfer mastery across jurisdictions.
- Do not copy proprietary tutoring question banks or assets.
- Use synthetic/minimized data in tests, fixtures, logs, prompts and screenshots; never commit real child data or secrets.

## Security & data-impact gate

Every feature that collects, stores, transmits, derives, profiles, exports or displays learner/parent data must document: data collected, purpose, storage, authorized access, retention/deletion, third-party/LLM flow, and whether a less-data alternative exists. Security/Compliance may block DoD for material unresolved privacy/security risk. COPPA, FERPA/PPRA (school deployments/education records), Canadian/PIPEDA youth privacy and applicable state/provincial obligations are applicability questions requiring appropriate review; unresolved high-risk legal interpretation is escalated to Ayalew.

## Synchronization rule

1. Read this file before starting or resuming work.
2. Inspect current `main`, the canonical GitHub issue and any open/recent PR before implementing, so parallel Devin/autopilot work is not duplicated.
3. Record detailed research, acceptance criteria, data-impact/security findings and implementation evidence on the canonical issue/PR.
4. After any material merge, scope change, block, acceptance or completion, update this file in the same work cycle.
5. A merged PR does not automatically close a feature. Mark `DONE` only after the applicable Definition of Done and issue acceptance criteria are evidenced.

_Last synchronized: 2026-10-02; reconciled against GitHub issue/PR state and `main` at `38a70b09`. F-026 #107 is the active release-candidate gate; F-027 #122 is pre-pilot convergence work, not a new expansion track. Avatar visual redesign is explicitly deferred until after the private pilot. Merged feature ledger additions from `feature/f-032-step-aware-voice-visuals`: F-032 (step-aware voice + algebra visuals + expanded step classifier codes), F-033 (daily goal + session recap + math keypad), F-034 (remediation voice banner), F-035 (escalation-policy audit, ADR-015), F-036 (all-curricula seed orchestrator + deploy wiring), F-037 (photo intake MVP, ADR-016; old-F-008 → PARTIAL), F-038 (skill type-breadth deepening), F-039 (CPA pedagogy layer + reverse-Socratic challenges, ADR-017)._
