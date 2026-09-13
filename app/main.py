from fastapi import FastAPI

from app.adaptive_api import router as adaptive_tutor_router
from app.adaptive_response_api import router as adaptive_response_router
from app.api import router as tutor_router
from app.core.settings import settings
from app.diagnostic_api import router as diagnostic_router
from app.services.llm_bootstrap import configure_tutor_engine

configure_tutor_engine()

app = FastAPI(title=settings.app_name, version="0.1.0")
app.include_router(tutor_router, prefix=settings.api_prefix)
app.include_router(adaptive_tutor_router, prefix=settings.api_prefix)
app.include_router(adaptive_response_router, prefix=settings.api_prefix)
app.include_router(diagnostic_router, prefix=settings.api_prefix)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
