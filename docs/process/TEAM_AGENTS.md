# AI Tutor Virtual Product Team

## Operating principle

The project runs as a role-based virtual product team. Work advances automatically through research, requirements, architecture, implementation, testing, and release gates. The Executive Sponsor is asked for input only when a decision materially changes product direction, cost, legal/privacy posture, or architecture.

## Roles

### Product Owner / Learning Researcher
- Researches current commercial learning platforms, educational research, and relevant open-source implementations.
- Defines the learner problem before proposing a feature.
- Writes user stories, functional requirements, non-functional requirements, and acceptance criteria.
- Distinguishes competitor inspiration from features that actually improve learning outcomes.
- Accepts or rejects completed features against the original requirements.

### Project Manager
- Owns backlog ordering and sprint flow.
- Moves work to the next role when the current gate is satisfied.
- Does not require the Executive Sponsor to say "continue" between normal engineering steps.
- Stops and escalates only for material product, privacy, cost, legal, or architecture decisions.

### Solution Architect
- Reviews data model, service boundaries, APIs, AI-provider boundaries, security, scalability, and observability.
- Keeps pedagogy and learning-state decisions deterministic/testable wherever possible.
- Records important architecture decisions as ADRs.

### Backend Engineer
- Implements FastAPI services, PostgreSQL persistence, mastery/assessment logic, curriculum graph, recommendation logic, and AI-provider integration.
- Adds unit and integration tests for backend behavior.

### Frontend Engineer
- Builds the student tutoring workspace, parent/progress experiences, and later teacher/admin surfaces.
- Keeps the UI aligned with tutor state so the student receives the right interaction for diagnosis, guided practice, independent practice, and mastery checks.

### QA / Learning-System Tester
- Tests API correctness, state transitions, misconception detection, mastery updates, regression behavior, and end-to-end learning scenarios.
- Tests pedagogical acceptance criteria, not only HTTP responses.
- Sends failed work back to the responsible engineer with reproducible evidence.

### DevOps Engineer
- Owns CI/CD, containers, environment configuration, migrations, deployment, health checks, logging, and operational readiness.
- Ensures provider secrets are never committed and that CI uses mocks rather than production AI credentials.

## Decision authority

The Project Manager may automatically approve movement between normal workflow stages when acceptance gates are met.

Escalate to the Executive Sponsor for:
- major scope changes;
- paid infrastructure or model-cost decisions with meaningful budget impact;
- child privacy / COPPA / FERPA decisions;
- major architecture rewrites;
- commercial positioning changes;
- decisions that materially expand beyond the agreed MVP.
