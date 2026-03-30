"""Verification and rejection log models."""

from __future__ import annotations

from sqlalchemy import CheckConstraint, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.common import utcnow


class VerificationLog(Base):
    __tablename__ = "verification_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String(36), index=True)
    node_id: Mapped[str] = mapped_column(String(128), index=True)
    gateway_received_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)
    device_timestamp: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    payload_canonical_json: Mapped[str] = mapped_column(Text, nullable=False)
    payload_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    validation_profile_version: Mapped[str] = mapped_column(String(32), nullable=False)
    prev_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    curr_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)


class RejectionLog(Base):
    __tablename__ = "rejection_log"
    __table_args__ = (CheckConstraint("rejection_code <> ''", name="ck_rejection_code_non_empty"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String(36), index=True)
    node_id: Mapped[str] = mapped_column(String(128), index=True)
    gateway_received_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)
    device_timestamp: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    payload_canonical_json: Mapped[str] = mapped_column(Text, nullable=False)
    rejection_code: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    rejection_reason: Mapped[str] = mapped_column(Text, nullable=False)
    rule_version: Mapped[str] = mapped_column(String(32), nullable=False)
