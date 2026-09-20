# AI Tutor — Master Product Backlog

This file is the **master coordination document** for Ayalew, Devin, ChatGPT/autopilot, and other contributors.

GitHub Issues hold detailed requirements/research and Pull Requests hold implementation evidence, but this file owns the high-level product status and execution order. Before starting work, read this file first, then inspect the linked issue/PR and current `main`.

## Status model

`PLANNED → RESEARCHING → READY → IN PROGRESS → PR/QA → DONE`

`BLOCKED` may be applied at any stage. `DONE` requires the applicable checks in `docs/qa/DEFINITION_OF_DONE.md`; a merged PR or green CI alone is not sufficient.

## Current execution

| Priority | Work item | GitHub | Status | Current evidence / next gate |
|---|---|---|---|---|
| P0 | F-021 MTH1W fine-grained skill graph and adaptive problem variation | Issue #45 / PR #50 | **IN PROGRESS** | PR #50 merged (`107f50f9`) with green CI #439 and meaningful deterministic problem-generation work. F-021 remains open: prove fine-grained MTH1W skills/provenance, multiple materially different problem families, recent-equivalence/exhaustion behavior, evidence-driven selection/prerequisite return, content-readiness gating, cross-jurisdiction negative tests, E2E/pedagogical regression, QA/PO/PM acceptance. |
| P1 parallel | F-022 Goozam-family learner/parent UI/UX | Issue #46 | **IN PROGRESS — PARTIAL** | PR #50 also merged substantial learner/login visual work. Do not mark done until F-022 accessibility, responsive behavior, parent/learner flows, reusable design system and browser regressions satisfy its acceptance criteria. |
| P2 | F-019 MD/DC/VA Grades 6–7 & high-school-entry expansion | Issue #41 | **RESEARCHING / CONTENT BACKLOG** | Authoritative-source and pathway research exists. Curriculum packs still require mapping, original content, ingestion/readiness and isolation acceptance. |
| P2 | F-020 Dynamic Math Visualization & Instructional Animation Engine | Issue #42 | **PLANNED / RESEARCH GATED** | SVG-first deterministic visualization direction defined; implementation and acceptance remain. |
| Parallel | Business Model, Pilot Economics & Deployment Strategy | Issue #12 | **RESEARCHING** | Marketing/PO workstream; pricing, packaging, pilot-to-paid, unit economics and GTM experiments continue without interrupting P0. |

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
| #19 | F-010 Learning Analytics & Deterministic Intervention Engine | DONE |
| #20 | F-011 Pilot Observability, Learning KPIs & Unit Economics | DONE |
| #21 | F-012 Proposed Maryland Mathematics Grade Expansion Framework | DONE / research framework |
| #22 | F-007A Authoritative Pilot Content Packs & Maryland Course Decision | DONE |
| #24 | F-013 Containerized Microservice Architecture & Deployment | DONE |
| #28 | F-014 F-011 Observability Completion & Pilot Hardening | DONE |
| #30 | F-015 Ontario Grade 9 MTH1W Curriculum Pack | DONE |
| #35 | F-016 Private Pilot Launch Readiness | DONE |
| #37 | F-017 Pilot Web Application & Family/Learner Onboarding | DONE |
| #39 | F-018 Private Pilot Privacy Controls & Data Lifecycle | DONE |
| #41 | F-019 MD/DC/VA Grades 6–7 & High-School-Entry Math Expansion | RESEARCHING / CONTENT BACKLOG |
| #42 | F-020 Dynamic Math Visualization & Instructional Animation Engine | PLANNED / RESEARCH GATED |
| #43 | Fix MTH1W canonical curriculum seeding and learner skill discovery | DONE |
| #45 | F-021 MTH1W fine-grained skill graph and adaptive problem variation | **IN PROGRESS — ACTIVE** |
| #46 | F-022 Goozam-family UI/UX redesign for learner and parent experience | **IN PROGRESS — PARALLEL/PARTIAL** |

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

## Remaining historical backlog capabilities

These older backlog entries remain useful product capabilities but do not own the same identifiers as newer GitHub issues. Before implementation, create or link a uniquely identified canonical GitHub issue and update this master table.

| Historical label | Capability | Status |
|---|---|---|
| old F-008 | Worksheet / Photo Problem Intake | NOT IMPLEMENTED |
| old F-019 | React Learner Frontend (Vite + React + TypeScript service) | NOT IMPLEMENTED as described; newer server-rendered UI work does not automatically satisfy this item |
| old F-020 | Missed-Template Re-serving with fresh parameters | NOT IMPLEMENTED |
| old F-009 | Mathematical Visualization | NOT IMPLEMENTED; concept overlaps newer Issue #42 |

## Deferred until after private MVP validation

- gamification system;
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

_Last synchronized: 2026-09-20 after PR #50 merge._
