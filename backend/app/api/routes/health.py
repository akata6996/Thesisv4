"""Health and readiness routes."""

from fastapi import APIRouter
from sqlalchemy import text

from app.db.session import SessionLocal

router = APIRouter()


@router.get("/live")
def liveness() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/ready")
def readiness() -> dict[str, str]:
    """Readiness includes a lightweight database check."""
    with SessionLocal() as session:
        session.execute(text("SELECT 1"))
    return {"status": "ready"}
