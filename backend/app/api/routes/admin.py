"""Phase 4 admin APIs: node enrollment and session reset."""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_operator
from app.models.admin import AdminActionType
from app.models.user import User
from app.schemas.admin import (
    NodeEnrollmentRequest,
    NodeEnrollmentResponse,
    NodeRegistryItem,
    SessionResetRequest,
    SessionResetResponse,
)
from app.services.admin_audit_service import append_admin_action
from app.services.enrollment_service import EnrollmentError, enroll_node, list_nodes
from app.services.session_service import reset_enforcement_session

router = APIRouter()


@router.post("/nodes/enroll", response_model=NodeEnrollmentResponse, status_code=status.HTTP_201_CREATED)
def enroll_node_endpoint(
    payload: NodeEnrollmentRequest,
    db: Session = Depends(get_db),
    operator: User = Depends(require_operator),
) -> NodeEnrollmentResponse:
    try:
        row = enroll_node(
            db,
            node_id=payload.node_id,
            display_name=payload.display_name,
            pubkey_fingerprint=payload.pubkey_fingerprint,
            enrolled_by_user_id=operator.id,
        )
        append_admin_action(
            db,
            actor_user_id=operator.id,
            action_type=AdminActionType.node_enroll,
            target_type="node",
            target_id=row.node_id,
            action_payload_json=json.dumps(payload.model_dump()),
            auto_commit=False,
        )
        db.commit()
        db.refresh(row)
    except EnrollmentError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except Exception:
        db.rollback()
        raise

    return NodeEnrollmentResponse(
        id=row.id,
        node_id=row.node_id,
        display_name=row.display_name,
        pubkey_fingerprint=row.pubkey_fingerprint,
        enrollment_status=row.enrollment_status.value,
        created_at=row.created_at,
    )


@router.get("/nodes", response_model=list[NodeRegistryItem])
def list_nodes_endpoint(
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[NodeRegistryItem]:
    rows = list_nodes(db, limit=limit, offset=offset)
    return [
        NodeRegistryItem(
            id=row.id,
            node_id=row.node_id,
            display_name=row.display_name,
            enrollment_status=row.enrollment_status.value,
            created_at=row.created_at,
            revoked_at=row.revoked_at,
        )
        for row in rows
    ]


@router.post("/session/reset", response_model=SessionResetResponse)
def reset_session_endpoint(
    payload: SessionResetRequest,
    db: Session = Depends(get_db),
    operator: User = Depends(require_operator),
) -> SessionResetResponse:
    try:
        state = reset_enforcement_session(db)
        append_admin_action(
            db,
            actor_user_id=operator.id,
            action_type=AdminActionType.session_reset,
            target_type="session_state",
            target_id=str(state.id),
            action_payload_json=json.dumps({"reason": payload.reason, "new_session_id": state.current_session_id}),
            auto_commit=False,
        )
        db.commit()
        db.refresh(state)
    except Exception:
        db.rollback()
        raise

    return SessionResetResponse(
        current_session_id=state.current_session_id,
        session_started_at=state.session_started_at,
        reset_counter=state.reset_counter,
    )
