"""Read-only observability query services."""

from __future__ import annotations

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.models.enrollment import EnrollmentRegistry, EnrollmentStatus
from app.models.merkle import BlockchainAnchor, MerkleBatch
from app.models.verification import RejectionLog, VerificationLog
from app.schemas.observability import DashboardSummaryResponse


def list_verification_logs(
    db: Session,
    *,
    limit: int,
    offset: int,
    node_id: str | None = None,
    session_id: str | None = None,
) -> list[VerificationLog]:
    stmt = select(VerificationLog)
    if node_id:
        stmt = stmt.where(VerificationLog.node_id == node_id)
    if session_id:
        stmt = stmt.where(VerificationLog.session_id == session_id)
    stmt = stmt.order_by(VerificationLog.id.desc()).limit(limit).offset(offset)
    return list(db.execute(stmt).scalars().all())


def get_verification_by_id(db: Session, verification_id: int) -> VerificationLog | None:
    return db.get(VerificationLog, verification_id)


def list_rejection_logs(
    db: Session,
    *,
    limit: int,
    offset: int,
    node_id: str | None = None,
    session_id: str | None = None,
    rejection_code: str | None = None,
) -> list[RejectionLog]:
    stmt = select(RejectionLog)
    if node_id:
        stmt = stmt.where(RejectionLog.node_id == node_id)
    if session_id:
        stmt = stmt.where(RejectionLog.session_id == session_id)
    if rejection_code:
        stmt = stmt.where(RejectionLog.rejection_code == rejection_code)
    stmt = stmt.order_by(RejectionLog.id.desc()).limit(limit).offset(offset)
    return list(db.execute(stmt).scalars().all())


def list_merkle_batches(
    db: Session,
    *,
    limit: int,
    offset: int,
    status: str | None = None,
) -> list[MerkleBatch]:
    stmt = select(MerkleBatch)
    if status:
        stmt = stmt.where(MerkleBatch.status == status)
    stmt = stmt.order_by(MerkleBatch.id.desc()).limit(limit).offset(offset)
    return list(db.execute(stmt).scalars().all())


def list_blockchain_anchors(
    db: Session,
    *,
    limit: int,
    offset: int,
    status: str | None = None,
) -> list[BlockchainAnchor]:
    stmt = select(BlockchainAnchor)
    if status:
        stmt = stmt.where(BlockchainAnchor.confirm_status == status)
    stmt = stmt.order_by(BlockchainAnchor.id.desc()).limit(limit).offset(offset)
    return list(db.execute(stmt).scalars().all())


def dashboard_summary(db: Session) -> DashboardSummaryResponse:
    total_verified = db.execute(select(func.count(VerificationLog.id))).scalar_one()
    total_rejected = db.execute(select(func.count(RejectionLog.id))).scalar_one()
    active_nodes = db.execute(
        select(func.count(EnrollmentRegistry.id)).where(EnrollmentRegistry.enrollment_status == EnrollmentStatus.active)
    ).scalar_one()

    latest_merkle_root = db.execute(select(MerkleBatch.merkle_root).order_by(desc(MerkleBatch.id)).limit(1)).scalar_one_or_none()
    latest_anchor_status = db.execute(
        select(BlockchainAnchor.confirm_status).order_by(desc(BlockchainAnchor.id)).limit(1)
    ).scalar_one_or_none()

    return DashboardSummaryResponse(
        total_verified=total_verified,
        total_rejected=total_rejected,
        active_nodes=active_nodes,
        latest_merkle_root=latest_merkle_root,
        latest_anchor_status=latest_anchor_status.value if latest_anchor_status else None,
    )
