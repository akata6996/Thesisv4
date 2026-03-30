"""Phase 5 read-only observability endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.observability import (
    BlockchainAnchorItem,
    DashboardSummaryResponse,
    MerkleBatchItem,
    RejectionLogItem,
    VerificationDetailResponse,
    VerificationLogItem,
)
from app.services.observability_service import (
    dashboard_summary,
    get_verification_by_id,
    list_blockchain_anchors,
    list_merkle_batches,
    list_rejection_logs,
    list_verification_logs,
)

router = APIRouter()


@router.get("/verification-log", response_model=list[VerificationLogItem])
def verification_log_list(
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    node_id: str | None = Query(default=None),
    session_id: str | None = Query(default=None),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[VerificationLogItem]:
    rows = list_verification_logs(db, limit=limit, offset=offset, node_id=node_id, session_id=session_id)
    return [
        VerificationLogItem(
            id=row.id,
            session_id=row.session_id,
            node_id=row.node_id,
            gateway_received_at=row.gateway_received_at,
            device_timestamp=row.device_timestamp,
            payload_hash=row.payload_hash,
            validation_profile_version=row.validation_profile_version,
            prev_hash=row.prev_hash,
            curr_hash=row.curr_hash,
        )
        for row in rows
    ]


@router.get("/verification-log/{verification_id}", response_model=VerificationDetailResponse)
def verification_detail(
    verification_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> VerificationDetailResponse:
    row = get_verification_by_id(db, verification_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Verification record not found")

    return VerificationDetailResponse(
        id=row.id,
        session_id=row.session_id,
        node_id=row.node_id,
        gateway_received_at=row.gateway_received_at,
        device_timestamp=row.device_timestamp,
        payload_hash=row.payload_hash,
        validation_profile_version=row.validation_profile_version,
        prev_hash=row.prev_hash,
        curr_hash=row.curr_hash,
        payload_canonical_json=row.payload_canonical_json,
    )


@router.get("/rejection-log", response_model=list[RejectionLogItem])
def rejection_log_list(
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    node_id: str | None = Query(default=None),
    session_id: str | None = Query(default=None),
    rejection_code: str | None = Query(default=None),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[RejectionLogItem]:
    rows = list_rejection_logs(
        db,
        limit=limit,
        offset=offset,
        node_id=node_id,
        session_id=session_id,
        rejection_code=rejection_code,
    )
    return [
        RejectionLogItem(
            id=row.id,
            session_id=row.session_id,
            node_id=row.node_id,
            gateway_received_at=row.gateway_received_at,
            rejection_code=row.rejection_code,
            rejection_reason=row.rejection_reason,
            rule_version=row.rule_version,
        )
        for row in rows
    ]


@router.get("/merkle-batches", response_model=list[MerkleBatchItem])
def merkle_batch_list(
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    status_filter: str | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[MerkleBatchItem]:
    rows = list_merkle_batches(db, limit=limit, offset=offset, status=status_filter)
    return [
        MerkleBatchItem(
            id=row.id,
            batch_uuid=row.batch_uuid,
            session_id=row.session_id,
            from_verification_id=row.from_verification_id,
            to_verification_id=row.to_verification_id,
            leaf_count=row.leaf_count,
            merkle_root=row.merkle_root,
            status=row.status.value,
            created_at=row.created_at,
        )
        for row in rows
    ]


@router.get("/anchors", response_model=list[BlockchainAnchorItem])
def anchor_list(
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    status_filter: str | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[BlockchainAnchorItem]:
    rows = list_blockchain_anchors(db, limit=limit, offset=offset, status=status_filter)
    return [
        BlockchainAnchorItem(
            id=row.id,
            merkle_batch_id=row.merkle_batch_id,
            chain=row.chain,
            tx_signature=row.tx_signature,
            slot=row.slot,
            anchored_at=row.anchored_at,
            confirm_status=row.confirm_status.value,
            error_message=row.error_message,
        )
        for row in rows
    ]


@router.get("/dashboard-summary", response_model=DashboardSummaryResponse)
def dashboard_summary_endpoint(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> DashboardSummaryResponse:
    return dashboard_summary(db)
