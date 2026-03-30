"""Session reset and session-state domain service."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.common import utcnow, uuid4_str
from app.models.session_state import SessionState


def ensure_session_state(db: Session) -> SessionState:
    row = db.get(SessionState, 1)
    if row is None:
        row = SessionState(id=1)
        db.add(row)
        db.commit()
        db.refresh(row)
    return row


def reset_enforcement_session(db: Session) -> SessionState:
    row = ensure_session_state(db)
    row.current_session_id = uuid4_str()
    row.session_started_at = utcnow()
    row.reset_counter += 1
    db.commit()
    db.refresh(row)
    return row
