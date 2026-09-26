# F-013 Pilot Hardening Review

Issue: #81 — Production UI Template, Design System & Pilot Experience

## Product / PO acceptance checklist
The F-013 vertical slice covers parent registration/sign-in, learner setup and exact curriculum assignment, learner selection and curriculum-scoped skill discovery, tutoring/practice using application-owned pedagogy, evidence-backed learner progress, and a parent progress view that distinguishes independent mastery from assisted success.

The UI redesign does not change mastery, progression, prerequisites, problem eligibility, curriculum identity, or assessment semantics.

## Accessibility and responsive review
- Core learner/parent controls retain native labels and keyboard-operable form controls.
- Visual skill cards augment rather than replace the accessible skill select.
- Navigation exposes an accessible primary-navigation label and current-page state.
- Status/error/loading content uses status or alert semantics where applicable.
- Core learner and parent layouts collapse for tablet/mobile breakpoints.
- Reduced-motion preference is respected globally.
- Critical state is expressed with text, not color alone.

## Security & Compliance review
- Existing backend authorization remains the authority for family/learner access.
- Synthetic family E2E retains an unrelated-parent negative test against a learner session.
- No new authn/authz bypass, client-side authorization decision, or family lookup was introduced.
- No new third-party frontend dependency, telemetry, session replay, ad SDK, or analytics SDK was introduced.
- No learner/parent payloads are logged by the F-013 UI changes.
- No secrets or real child data are introduced by F-013 tests or fixtures.

## Lightweight data-impact check
F-013 collects no new student or parent fields. It renders existing authorized onboarding, curriculum, skill, tutoring, progress, review, support-area, and recent-activity fields. It introduces no new persistence, retention policy, profiling, model input, or third-party data flow.

## Architecture review
- Shared React design tokens/application shell are reused across learner and parent surfaces.
- Existing APIs/contracts remain authoritative.
- Jurisdiction/course/version curriculum isolation remains unchanged.
- LLM responsibilities remain constrained-language-only; application code retains pedagogical decisions.

## QA gate
The existing Definition of Done remains authoritative. Exact-head CI must pass the Python lint/unit/integration/regression suite, migrations and synthetic seed, deployable container builds and health checks, Playwright learner journey, and Playwright synthetic family journey including unrelated-family isolation.

Do not mark F-013 accepted or merge the hardening PR until exact-head CI is green.
