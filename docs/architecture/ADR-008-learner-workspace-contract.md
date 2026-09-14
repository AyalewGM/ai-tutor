# ADR-008: Learner Workspace Contract and Pedagogy Boundary

- Status: Accepted for F-008 implementation
- Date: 2026-09-14
- Feature: F-008 Student Learning Experience & Tutor UI

## Context

F-001 through F-007 established deterministic tutoring state, evidence, hint policy, prerequisite remediation, mastery gates, and strict curriculum scoping. F-008 adds the learner-facing experience without allowing the browser or an LLM to become a second pedagogy engine.

A learner must be able to reload or reconnect to a session and see the same pedagogical state without creating attempts, mastery evidence, tutor turns, or implicit transitions. Assessment states must also remain protected if a custom client bypasses visual controls.

## Decision

### 1. The backend exposes a learner-workspace read model

The workspace endpoint reconstructs the current learner-visible state from persisted session data:

- learner-safe identity and grade;
- curriculum/course context;
- primary and active learning focus;
- current deterministic tutor state;
- current problem and latest coaching message;
- mastery/evidence summary that distinguishes independent from hinted success;
- a bounded list of actions currently permitted by application policy.

The read model intentionally omits governance/provenance internals and does not expose cross-curriculum mappings.

### 2. GET/read operations are pedagogically side-effect free

Reloading the workspace must not create or alter:

- attempts;
- mastery events;
- hint events;
- tutor turns;
- problem selection;
- state transitions;
- prerequisite selection.

The client renders persisted state; it does not advance it.

### 3. The application derives allowed actions

The browser does not infer whether hints or struggle support are permitted. The application derives allowed actions from the persisted tutor state and deterministic policy. Assessment states such as diagnostic and mastery check do not expose hint/struggle actions.

A later client action endpoint must re-check the same server-side policy. UI visibility is never the security or pedagogy boundary.

### 4. LLMs remain language renderers

An LLM may phrase coaching, hints, explanations, or constrained variants only after application code has selected the curriculum, skill, problem objective, tutor state, intervention, and hint level.

The LLM may not choose:

- the curriculum or jurisdiction;
- the active skill or prerequisite;
- the next problem;
- whether help is allowed;
- the hint level;
- mastery or remediation outcomes;
- evidence classification.

### 5. Problem-first interaction

The initial pilot uses a problem-first workspace with contextual coaching. Structured actions such as answer submission, hint request, and `I don't understand` are preferred over unrestricted chat controlling the lesson.

Voice, broad free-form chat, and heavy gamification remain deferred until the core problem -> support -> independent evidence -> mastery flow is accepted.

## Consequences

- Refresh/retry behavior becomes testable and reproducible.
- A future web/mobile UI can remain thin and state-driven.
- Assessment restrictions are represented by backend policy rather than presentation logic.
- Curriculum isolation continues through the learner surface because session scope is revalidated before any workspace data is returned.
- Additional learner actions can be added incrementally without changing the application-owned pedagogy rule.

## QA requirements

1. Repeated workspace GETs return the same pedagogical state and create no evidence or turns.
2. Diagnostic and mastery-check workspaces do not allow hint or struggle actions.
3. Guided/remediation states expose only actions allowed by deterministic policy.
4. A persisted problem outside the active curriculum/skill scope fails closed.
5. Assisted and independent evidence remain distinguishable in learner-facing progress.
6. Existing curriculum-isolation, mastery, remediation, and hint-policy regression suites remain green.
