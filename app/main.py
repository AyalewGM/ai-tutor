from fastapi import FastAPI
from sqlalchemy import text

from app.adaptive_api import router as adaptive_tutor_router
from app.adaptive_response_api import router as adaptive_response_router
from app.api import router as tutor_router
from app.auth import session_identity_middleware
from app.auth_api import router as auth_router
from app.auth_web import router as auth_web_router
from app.core.database import SessionLocal
from app.core.observability import configure_logging, request_logging_middleware
from app.core.settings import settings
from app.diagnostic_api import router as diagnostic_router
from app.hint_api import router as hint_router
from app.learner_web import router as learner_web_router
from app.middleware.pii_sanitizer import PIISanitizerMiddleware
from app.onboarding_api import router as onboarding_router
from app.parent_api import router as parent_router
from app.parent_settings_web import router as parent_settings_web_router
from app.parent_web import router as parent_web_router
from app.privacy_api import router as privacy_router
from app.services.llm_bootstrap import configure_tutor_engine
from app.telemetry_api import router as telemetry_router
from app.workspace_api import router as learner_workspace_router

configure_tutor_engine()
configure_logging()

app = FastAPI(title=settings.app_name, version="0.1.0")
app.add_middleware(PIISanitizerMiddleware)
app.middleware("http")(session_identity_middleware)
app.middleware("http")(request_logging_middleware)
app.include_router(auth_router, prefix=settings.api_prefix)
app.include_router(onboarding_router, prefix=settings.api_prefix)
app.include_router(tutor_router, prefix=settings.api_prefix)
app.include_router(adaptive_tutor_router, prefix=settings.api_prefix)
app.include_router(adaptive_response_router, prefix=settings.api_prefix)
app.include_router(diagnostic_router, prefix=settings.api_prefix)
app.include_router(hint_router, prefix=settings.api_prefix)
app.include_router(parent_router, prefix=settings.api_prefix)
app.include_router(privacy_router, prefix=settings.api_prefix)
app.include_router(learner_workspace_router, prefix=settings.api_prefix)
app.include_router(telemetry_router, prefix=settings.api_prefix)
app.include_router(auth_web_router)
app.include_router(parent_web_router)
app.include_router(parent_settings_web_router)
app.include_router(learner_web_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/ready")
def ready() -> dict[str, str]:
    """Readiness check: verify DB connectivity and Alembic head consistency.

    Returns 200 when the application can serve traffic, 503 otherwise.
    Used by Docker health checks and load balancers.
    """
    from alembic.config import Config as AlembicConfig
    from alembic.script import ScriptDirectory

    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
            db_version = db.scalar(text("SELECT version_num FROM alembic_version"))

        alembic_cfg = AlembicConfig("alembic.ini")
        head = ScriptDirectory.from_config(alembic_cfg).get_current_head()
        if db_version != head:
            return {
                "status": "not_ready",
                "reason": f"alembic version mismatch: db={db_version} expected={head}",
            }
        return {"status": "ready"}
    except Exception as exc:  # noqa: BLE001 — readiness must never crash
        return {"status": "not_ready", "reason": str(exc)[:200]}
