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
- OpenAI and Gemini runtime adapters
- structured tutor-generation output with deterministic fallback when a provider is absent or fails
- PostgreSQL-backed integration testing in GitHub Actions

## Architecture principle

The application owns pedagogical decisions. The state machine determines the learning state and pedagogical action before the `TutorEngine` generates student-facing language. An LLM provider is therefore a constrained language-generation component, not the authority over mastery, assessment, or progression.

## AI provider configuration

Copy `.env.example` to `.env` and choose one provider. The official SDKs read their credentials from the environment, so keys are never stored in application source.

OpenAI example:

```env
AI_PROVIDER=openai
OPENAI_API_KEY=your-local-key
OPENAI_MODEL=gpt-5
```

Gemini example:

```env
AI_PROVIDER=gemini
GEMINI_API_KEY=your-local-key
GEMINI_MODEL=gemini-3.8-flash
```

To force deterministic language generation without an external model:

```env
AI_PROVIDER=fallback
```

The `.env` file is ignored by Git and must never be committed.

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
