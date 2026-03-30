"""Administrative audit models."""

from __future__ import annotations

import enum

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.common import utcnow


class AdminActionType(str, enum.Enum):
    node_enroll = "node_enroll"
    node_revoke = "node_revoke"
    session_reset = "session_reset"
    export_request = "export_request"
    user_login = "user_login"


class ExportStatus(str, enum.Enum):
    queued = "queued"
    completed = "completed"
    failed = "failed"


class AdminActionLog(Base):
    __tablename__ = "admin_action_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    occurred_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)
    actor_user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    action_type: Mapped[AdminActionType] = mapped_column(Enum(AdminActionType, name="admin_action_type"), index=True)
    target_type: Mapped[str] = mapped_column(String(64), nullable=False)
    target_id: Mapped[str] = mapped_column(String(64), nullable=False)
    request_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    action_payload_json: Mapped[str] = mapped_column(Text, nullable=False)
    prev_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    curr_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)


class AuditExport(Base):
    __tablename__ = "audit_exports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    requested_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)
    requested_by_user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    export_type: Mapped[str] = mapped_column(String(64), nullable=False)
    filter_json: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[ExportStatus] = mapped_column(Enum(ExportStatus, name="export_status"), index=True, default=ExportStatus.queued)
    artifact_path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    artifact_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    completed_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
