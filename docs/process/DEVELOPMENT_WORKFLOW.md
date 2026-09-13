# Development Workflow

## Feature loop

1. Product Owner researches the learner problem, current products, educational evidence, and relevant open-source implementations.
2. Product Owner writes user stories, requirements, and acceptance criteria.
3. Project Manager selects the next backlog item based on learning impact, MVP fit, dependencies, and implementation cost.
4. Solution Architect defines data, API, UI, AI, security, and operational impacts.
5. Backend and Frontend engineers implement the smallest complete vertical slice.
6. QA tests technical behavior and tutoring behavior. Failed work returns to engineering automatically.
7. DevOps verifies CI, migrations, configuration, deployment readiness, and observability.
8. Product Owner verifies the completed feature against the original acceptance criteria.
9. If Definition of Done is satisfied, the Project Manager accepts the feature and selects the next backlog item automatically.

## Required feature specification

Each feature must include:
- problem statement;
- research basis;
- user story;
- functional requirements;
- non-functional requirements when relevant;
- acceptance criteria;
- architecture impact;
- QA scenarios;
- Definition of Done checklist.

## Handoff rules

- No engineering handoff without acceptance criteria.
- Code completion alone does not make a feature Done.
- QA failure sends work back to the responsible engineer.
- CI failure blocks acceptance.
- A technically correct feature that violates the intended tutoring behavior is not Done.

## Sponsor escalation

Routine implementation decisions do not require sponsor approval. Escalate only for major scope changes, meaningful recurring cost changes, privacy/compliance decisions, commercialization strategy changes, or major architecture reversals.
