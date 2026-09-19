from fastapi import FastAPI

from app.adaptive_api import router as adaptive_tutor_router
from app.adaptive_response_api import router as adaptive_response_router
from app.api import router as tutor_router
from app.auth import session_identity_middleware
from app.auth_api import router as auth_router
from app.core.settings import settings
from app.diagnostic_api import router as diagnostic_router
from app.hint_api import router as hint_router
from app.learner_web import router as learner_web_router
from app.onboarding_api import router as onboarding_router
from app.parent_api import router as parent_router
from app.parent_settings_web import router as parent_settings_web_router
from app.parent_web import router as parent_web_router
from app.services.llm_bootstrap import configure_tutor_engine
from app.telemetry_api import router as telemetry_router
from app.workspace_api import router as learner_workspace_router

configure_tutor_engine()

app = FastAPI(title=settings.app_name, version="0.1.0")
app.middleware("http")(session_identity_middleware)
app.include_router(auth_router, prefix=settings.api_prefix)
app.include_router(onboarding_router, prefix=settings.api_prefix)
app.include_router(tutor_router, prefix=settings.api_prefix)
app.include_router(adaptive_tutor_router, prefix=settings.api_prefix)
app.include_router(adaptive_response_router, prefix=settings.api_prefix)
app.include_router(diagnostic_router, prefix=settings.api_prefix)
app.include_router(hint_router, prefix=settings.api_prefix)
app.include_router(parent_router, prefix=settings.api_prefix)
app.include_router(learner_workspace_router, prefix=settings.api_prefix)
app.include_router(telemetry_router, prefix=settings.api_prefix)
app.include_router(parent_web_router)
app.include_router(parent_settings_web_router)
app.include_router(learner_web_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
