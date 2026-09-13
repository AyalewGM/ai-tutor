# Sprint 1 Development

## Scope

Sprint 1 implements the first vertical slice of the adaptive tutoring backend for MCPS Grade 8 distributive-property practice.

The application, not the language model, owns pedagogical state, mastery, misconception history, and tutoring actions.

## Local setup

```bash
docker compose up -d postgres
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
python scripts/seed_sprint1.py
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/docs` for Swagger UI.

## Run tests

```bash
pytest
```

## Sprint 1 endpoints

- `GET /health`
- `POST /api/v1/tutor/sessions`
- `POST /api/v1/tutor/sessions/{session_id}/respond`

## First supported learning slice

Skill: `M8.ALG.DIST` — Distributive Property.

Seed problems include `3(x+4)`, `2(x+5)`, `4(x-3)`, `5(x+2)`, and `-2(x+6)`.

The evaluator explicitly recognizes `DIST_001`, where a learner distributes the outside multiplier to only one term, for example `3(x+4) -> 3x+4`.

## Architecture rule

The deterministic state machine chooses actions such as `GIVE_HINT`, `REMEDIATE`, `START_MASTERY_CHECK`, and `MARK_MASTERED`. A future LLM adapter will turn those actions into natural tutoring language while respecting constraints from the application.

## Next work

1. Add Alembic migrations instead of startup `create_all`.
2. Add TutorTurn and MasteryEvent persistence.
3. Add problem selection that excludes already-used problems and respects target difficulty.
4. Add structured LLM TutorEngine behind an interface, with deterministic fallback.
5. Add API integration tests using an isolated test database.
6. Expand the skill graph only after the distributive-property loop is stable.
