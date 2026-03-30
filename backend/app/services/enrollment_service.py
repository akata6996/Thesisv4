"""Enrollment registry domain service."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.enrollment import EnrollmentRegistry, EnrollmentStatus


class EnrollmentError(ValueError):
    """Raised when enrollment command is invalid."""


def enroll_node(
    db: Session,
    *,
    node_id: str,
    display_name: str,
    pubkey_fingerprint: str | None,
    enrolled_by_user_id: str,
) -> EnrollmentRegistry:
    """Prepare an enrollment mutation; caller is responsible for commit."""
    existing = db.execute(select(EnrollmentRegistry).where(EnrollmentRegistry.node_id == node_id)).scalar_one_or_none()
    if existing and existing.enrollment_status == EnrollmentStatus.active:
        raise EnrollmentError(f"Node '{node_id}' is already enrolled")

    if existing and existing.enrollment_status == EnrollmentStatus.revoked:
        existing.display_name = display_name
        existing.pubkey_fingerprint = pubkey_fingerprint
        existing.enrollment_status = EnrollmentStatus.active
        existing.revoked_at = None
        db.flush()
        return existing

    row = EnrollmentRegistry(
        node_id=node_id,
        display_name=display_name,
        pubkey_fingerprint=pubkey_fingerprint,
        enrolled_by_user_id=enrolled_by_user_id,
        enrollment_status=EnrollmentStatus.active,
    )
    db.add(row)
    db.flush()
    return row


def list_nodes(db: Session, *, limit: int = 100, offset: int = 0) -> list[EnrollmentRegistry]:
    stmt = select(EnrollmentRegistry).order_by(EnrollmentRegistry.created_at.desc()).limit(limit).offset(offset)
    return list(db.execute(stmt).scalars().all())
