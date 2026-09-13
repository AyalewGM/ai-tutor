from fastapi import FastAPI

from app.api import router as tutor_router
from app.core.database import Base, engine
from app.core.settings import settings


app = FastAPI(title=settings.app_name, version="0.1.0")
app.include_router(tutor_router, prefix=settings.api_prefix)


@app.on_event("startup")
def create_tables() -> None:
    # Sprint 1 convenience. Replace with Alembic migrations before production deployment.
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
