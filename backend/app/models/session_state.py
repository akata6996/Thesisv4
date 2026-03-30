"""Current enforcement session state model."""

from __future__ import annotations

from sqlalchemy import CheckConstraint, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.common import utcnow, uuid4_str


class SessionState(Base):
    __tablename__ = "session_state"
    __table_args__ = (CheckConstraint("id = 1", name="ck_session_state_singleton"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    current_session_id: Mapped[str] = mapped_column(String(36), default=uuid4_str, nullable=False, index=True)
    session_started_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    reset_counter: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)
