FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN addgroup --system app && adduser --system --ingroup app app

COPY pyproject.toml ./
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./
COPY scripts ./scripts
# Elementary curriculum packs are data files the loader seeds from at deploy
# time (scripts/ops/seed_all_curricula.py -> docs/curriculum/packs).
COPY docs/curriculum/packs ./docs/curriculum/packs

RUN pip install --no-cache-dir .

USER app
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
