FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN addgroup --system app && adduser --system --ingroup app app
RUN pip install --no-cache-dir \
    "fastapi>=0.115,<1.0" \
    "uvicorn[standard]>=0.30,<1.0" \
    "openai>=1.0,<3.0" \
    "google-genai>=1.0,<2.0"

COPY services/llm_gateway ./services/llm_gateway

USER app
EXPOSE 8001

CMD ["uvicorn", "services.llm_gateway.main:app", "--host", "0.0.0.0", "--port", "8001"]
