# Product Backlog

Prioritization considers learning impact, evidence from product research, MVP fit, dependency readiness, and implementation cost.

## Implemented

### F-001 Prerequisite-Aware Adaptive Linear Equations — DONE
Expand the current distributive-property vertical slice into a small MCPS Grade 8 linear-equation skill/prerequisite graph. Detect prerequisite gaps, enter targeted remediation, verify independent understanding, and resume the original goal.

### F-002 Diagnostic Placement and Readiness — DONE
Use a short adaptive diagnostic to estimate starting mastery and choose the appropriate entry skill/difficulty rather than beginning every learner at the same place.

### F-003 Graduated Hint Ladder and Productive Struggle — DONE
Standardize hint levels across skills and ensure the tutor asks focused questions before revealing worked steps. Track assistance as learning evidence.

### F-004 Independent Mastery Gate — DONE
Separate assisted success from mastery. Require independent problems and a short mastery check before marking a skill mastered.

### F-005 Student Tutor Workspace — DONE
Create the first usable React/Next.js learner interface for session start, problem display, typed responses, tutor messages, hint requests, and progress state.

### F-006 Progress and Learning Explanation — DONE
Expose mastery, evidence confidence, active misconceptions, improvement, and recommended next work in language useful to a parent and student.

### F-007 Spaced Review / Retention — DONE
Schedule review after apparent mastery and lower confidence/mastery when retention evidence shows forgetting. Expanding review intervals (1/3/7/14/30 days), confidence-scaled forgetting decay, review demotion to REVIEW_DUE, and review-due session interception before new instruction.

### F-010 Broader Misconception Catalog — DONE
Ordered misconception-rule registry replacing single hardcoded detection. Fourteen codes shipped across all four seeded curricula: DIST_001–002 (distribution), ALG_001–002 (like-terms and constant signs), EQ_001–003 (inverse operations), REL_001–002 (linear relations), NUM_001–003 (integers and fractions), FIN_001–002 (percent), each with a remediation_strategy that constrains LLM tutoring language. Further rule coverage remains an ongoing content task.

### F-011 Difficulty-Aware Mastery and Adaptive Progression — DONE
Mastery evidence is scaled by problem difficulty relative to learner level (harder success = stronger evidence; easy failure = stronger negative evidence). `current_difficulty` now increases on successful independent progression (cap 10) and decreases when the engine triggers remediation (floor 1), keyed on the pre-focus-policy transition so detours still register struggle.

### F-012 Retention Visibility — DONE
Read-only `reviews_due` projection surfaces due/relearning skills with projected decayed mastery to the parent dashboard (`ChildDashboardOut.reviews_due`) and learner workspace (`LearnerWorkspaceOut.reviews_due`). New `spaced_review_pass_rate` KPI in telemetry.

### F-013 Continuous Diagnostic Placement — DONE
`services/placement.py` recomputes the recommended next skill from live mastery on every read — prerequisite-chain descent resurfaces decayed prerequisites as blockers. Surfaced as `recommended_next` (with READY_TO_START / RESUME_IN_PROGRESS / PREREQUISITE_GAP reason) on the parent dashboard and learner workspace.

### F-014 Psychometric Evidence Model — DONE
`update_mastery` now applies guess/slip parameters (BKT-lite): correct evidence is discounted by guess probability scaled by difficulty, incorrect evidence retains a slip-probability floor. Composes with assistance weighting, difficulty-scaled learning rate, and forgetting decay.

### F-015 Parametric Problem Generation — DONE
`services/problem_generation.py` — IXL-style generator registry keyed by `problem_type` (ARITHMETIC, SIMPLIFY_EXPRESSION, SOLVE_EQUATION, LINEAR_FUNCTION, INTEGER_OPERATIONS, FRACTION_OPERATIONS, WORD_PROBLEM) with difficulty-tiered parameter sampling. Canonical answers computed deterministically; generated problems persist with `source_type=GENERATED`. `select_next_problem` serves unseen curated problems first, excludes all session-attempted problems, generates when the pool is exhausted, and dedups on prompt text.

### F-016 Browser Auth and Learner Onboarding Flow — DONE
`/login` page (register/sign-in, session cookie, `?next=` redirect), `/learn` rewritten to use onboarding APIs with learner/skill dropdowns instead of raw UUIDs, inline learner creation, and 401→login redirects across browser surfaces. Registration IntegrityError moved inside the flush boundary.

### F-017 Problem-Aware Fallback Coaching — DONE
`tutor_engine.fallback_message` now dispatches on problem shape: six 4-rung hint ladders (linear function, equation, fraction, distribution, like-terms, generic) so non-distribution problems no longer receive parentheses language. `EXPLAIN_CONCEPT` shares the dispatch; `REMEDIATE` names the actual skill.

### F-018 Learner Workspace Visual Polish — DONE
Sticky navbar with sign-out, state stepper (Diagnose→Guided→Independent→Mastery→Complete), two-column layout, chat-style coach bubble, SVG mastery ring, correct/wrong problem feedback animations, completion hero, and review-due/next-skill surfaces.

### F-021 MTH1W Fine-Grained Skill Graph — DONE (doc-side; corresponds to GitHub Issue #45)
Nine atomic subskills under the four MTH1W strand anchors with prerequisite chains: B.NUM→INT→FRAC, C.ALG→EXPR→EQ1→EQ2, C.REL→SLOPE(+EQ2)→EVAL, F.FIN→PCT(+FRAC)→APP. Each subskill carries curated problems typed to a registered generator, strand-mapped misconceptions, and expectation-pack mappings. Anchor skills, edges, and problem counts preserved.

### F-022 Missed-Template Re-serving — DONE (implemented inside F-021 scope)
Generated problems persist `{generator, difficulty}` in their `solution` metadata; `regenerate_variant` produces a fresh-parameters variant of the same template and difficulty. `adaptive_response_api` re-serves a variant on incorrect answers to GENERATED problems (same skill), with fallback to normal selection for curated items.

### F-023 LLM Word-Problem Contextualization — DONE
Code samples parameters and computes the canonical answer; the LLM writes only the narrative skin. New gateway endpoint `POST /v1/contextualize` (strict JSON schema, app-computed context) plus `GatewayContextualizer` adapter that rejects narratives missing any parameter number verbatim — the model can never make a problem wrong, only plain. Wired through `configure_tutor_engine` when `AI_PROVIDER=gateway`; deterministic prompt otherwise. Also fixed google-genai shared-httpx-client lifecycle (module-level cached client) — Gemini provider verified live for both `/v1/render` coaching and `/v1/contextualize`.

### F-024 Fine-Grained Subskills for Remaining Curricula — DONE
Applied the F-021 atomic-subskill pattern to all three remaining curricula. MCPS_MATH_8: 5 subskills (INVERSE.ADD→MULT, DIST.POS→NEG, MULTI_STEP.COMBINE). MCPS_MATH_7: 6 subskills (PROP.RATE, PERCENT.OF, EXPR.DIST→COMBINE, EQUATION.ONE→TWO). MCPS_ALGEBRA_1_2026_27: 6 subskills (EXPR.DIST→COMBINE, EQ.ONE→TWO, FN.SLOPE→EVAL). All chained beneath their strand anchors via prerequisites, with curated problems typed to registered generators and strand-specific misconception rows. Exact-count tests updated (10 skills/8 edges/21 problems in each of G7 and A1); placement expectations updated to reflect that mastering an anchor now unlocks its subskill chain before the next strand. Dev DB reseeded and verified idempotent.

## P2 — Content intake and richer math interaction (remaining)

### F-008 Worksheet / Photo Problem Intake — NOT IMPLEMENTED
Accept a worksheet or problem image, extract the problem, map it to a curriculum skill, and enter the normal tutoring workflow without allowing OCR confidence problems to silently become authoritative truth.

### F-019 React Learner Frontend — NOT IMPLEMENTED
Port the learner workspace (then entry/login, then parent dashboard) to the stub `frontend/` service: Vite + React + TypeScript consuming the existing JSON APIs. Unlocks a real coach message thread, animated problem transitions, math-keypad input, and interactive rendering (prerequisite for F-009). Server-rendered pages remain as fallback.

### F-009 Mathematical Visualization — NOT IMPLEMENTED
Introduce graphs/visual representations where they materially improve conceptual understanding, especially linear functions and coordinate relationships. Likely requires a backend render spec on problems plus frontend rendering.

## Deferred until after private MVP validation
- gamification system;
- native mobile applications;
- voice-first tutoring;
- school/district roster and LMS integration;
- multi-subject expansion;
- agentic pedagogy that can override deterministic learning controls.

## GitHub Issues Backlog Status

> Synced from GitHub Issues on 2026-09-20. GitHub Issues are the execution source of truth.
>
> **Important:** feature numbers in this document and feature numbers used by older/newer GitHub issues evolved independently. For example, this file's F-019 is "React Learner Frontend", while GitHub Issue #41 is also labelled F-019 but means "MD/DC/VA Grades 6–7 & High-School-Entry Math Expansion". Use the GitHub issue number and title to disambiguate work.

| Issue | GitHub backlog item | Status |
|---|---|---|
| #2 | F-001: Prerequisite-Aware Adaptive Linear Equations | CLOSED |
| #3 | F-002: Adaptive Diagnostic Placement | CLOSED |
| #5 | F-003: Graduated Hint Ladder and Productive Struggle | CLOSED |
| #6 | F-002: Adaptive Diagnostic Placement (duplicate/continuation issue) | CLOSED |
| #8 | F-004: Independent Mastery Gate | CLOSED |
| #10 | F-005: Parent Profiles, Child Management, and Progress Dashboard | CLOSED |
| #11 | F-006: Hierarchical Curriculum Registry and Jurisdiction Isolation | CLOSED |
| #12 | EPIC: Business Model, Pilot Economics & Deployment Strategy | OPEN — parallel research |
| #15 | F-007: Pilot Curriculum Content Packs and Standards-Aligned Ingestion | CLOSED |
| #17 | F-008: Student Learning Experience & Tutor UI | CLOSED |
| #18 | F-009: Parent Progress Intelligence & Actionable Insights | CLOSED |
| #19 | F-010: Learning Analytics & Deterministic Intervention Engine | CLOSED |
| #20 | F-011: Pilot Observability, Learning KPIs & Unit Economics | CLOSED |
| #21 | F-012 PROPOSED: Maryland Mathematics Grade Expansion Framework | CLOSED |
| #22 | F-007A: Authoritative Pilot Content Packs & Maryland Course Decision | CLOSED |
| #24 | F-013 PROPOSED: Containerized Microservice Architecture & Deployment | CLOSED |
| #28 | F-014 PROPOSED: F-011 Observability Completion & Pilot Hardening | CLOSED |
| #30 | F-015 PROPOSED: Ontario Grade 9 MTH1W Curriculum Pack | CLOSED |
| #35 | F-016: Private Pilot Launch Readiness | CLOSED |
| #37 | F-017: Pilot Web Application & Family/Learner Onboarding | CLOSED |
| #39 | F-018: Private Pilot Privacy Controls & Data Lifecycle | CLOSED |
| #41 | F-019: MD/DC/VA Grades 6–7 & High-School-Entry Math Expansion | OPEN — curriculum expansion |
| #42 | F-020: Dynamic Math Visualization & Instructional Animation Engine | OPEN — planned backlog |
| #43 | Fix MTH1W canonical curriculum seeding and learner skill discovery | CLOSED |
| #45 | F-021: MTH1W fine-grained skill graph and adaptive problem variation | OPEN — fine-grained graph + missed-template re-serving landed in repo (doc F-021/F-022); pattern extended to MCPS G7/G8/Algebra 1 (doc F-024); verify remaining issue scope before closing |
| #46 | F-022: Goozam-family UI/UX redesign for learner and parent experience | OPEN — parallel UI/UX |

### Current execution order

F-021 is the active engineering path. F-022 may proceed in parallel where it does not redefine pedagogy or mastery semantics. F-019 and F-020 remain open backlog work subject to their research/dependency gates. The Business Model epic (#12) remains a parallel Product Owner / Marketing & Growth research track.

### Synchronization rule

When an issue is opened, closed, renamed, superseded, or materially re-scoped, update this status section so the repository backlog remains navigable from one place. Issue status alone does not prove implementation quality; feature acceptance and release still follow `docs/qa/DEFINITION_OF_DONE.md`.

