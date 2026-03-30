"""Node enrollment registry models."""

from __future__ import annotations

import enum

from sqlalchemy import DateTime, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.common import utcnow, uuid4_str


class EnrollmentStatus(str, enum.Enum):
    active = "active"
    revoked = "revoked"


class EnrollmentRegistry(Base):
    __tablename__ = "enrollment_registry"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4_str)
    node_id: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(128))
    pubkey_fingerprint: Mapped[str | None] = mapped_column(String(128), nullable=True)
    enrolled_by_user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    enrollment_status: Mapped[EnrollmentStatus] = mapped_column(
        Enum(EnrollmentStatus, name="enrollment_status"), default=EnrollmentStatus.active, nullable=False, index=True
    )
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    revoked_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
