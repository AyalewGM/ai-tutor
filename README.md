# AI Tutor

Adaptive AI tutoring platform focused first on curriculum-aware mathematics mastery.

## Sprint 1 vertical slice

The first supported learning skill is MCPS Grade 8 distributive property (`M8.ALG.DIST`).

The backend currently provides:

- FastAPI tutor session and response endpoints
- PostgreSQL persistence with Alembic migrations
- curriculum, skill, mastery, misconception, problem, attempt, tutor-turn, and mastery-event models
- deterministic misconception detection for partial distribution (`DIST_001`)
- assistance-aware mastery updates
- deterministic tutor state transitions
- adaptive next-problem selection
- a structured, provider-agnostic `TutorEngine`
- validated tutor generation output with deterministic fallback when an LLM provider is absent or fails
- PostgreSQL-backed integration testing in GitHub Actions

No external LLM provider is wired into the runtime yet. Sprint 1 therefore runs with the deterministic tutor-language fallback while preserving the provider interface for the next integration step.

## Architecture principle

The application owns pedagogical decisions. The state machine determines the learning state and pedagogical action before the `TutorEngine` generates student-facing language. An LLM provider is therefore a constrained language-generation component, not the authority over mastery, assessment, or progression.

## Local development

Start PostgreSQL:

```bash
docker compose up -d db
```

Install dependencies:

```bash
pip install -e '.[dev]'
```

Apply migrations and seed the Sprint 1 content:

```bash
alembic upgrade head
python scripts/seed_sprint1.py
```

Run the API:

```bash
uvicorn app.main:app --reload
```

Run quality checks:

```bash
ruff check .
pytest -q
```

API documentation is available at `/docs` while the service is running.
