# Definition of Done

A feature is Done only when all applicable checks pass.

## Product
- Problem statement is documented.
- Research basis is linked.
- User story and acceptance criteria are explicit.
- Delivered behavior matches the intended learner or parent outcome.

## Architecture
- Data model, API, UI, AI-provider, and operational impacts are reviewed.
- Important tradeoffs are documented.
- The LLM does not silently take ownership of mastery, progression, or assessment decisions that should remain testable application logic.

## Engineering
- Backend and frontend implementation is complete for the agreed vertical slice.
- Error handling and fallback behavior are defined.
- Database changes use migrations.
- No secrets are committed.

## Quality
- Unit tests pass.
- Integration tests pass.
- Relevant end-to-end scenarios pass.
- Regression suite passes.
- Pedagogical behavior is tested, including hints, independent work, mastery checks, and remediation where applicable.

## Operations
- CI is green.
- Environment configuration is documented.
- Health checks and useful logs exist for new runtime dependencies.
- Deployment or rollback concerns are documented when applicable.

## Acceptance
- QA signs off on the acceptance criteria.
- Product Owner accepts the learner-facing behavior.
- Project Manager marks the feature accepted and may advance automatically to the next prioritized backlog item.
