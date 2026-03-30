"""Append-only audit logging service for privileged/admin actions."""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.admin import AdminActionLog, AdminActionType
from app.services.hash_chain import compute_chain_hash


def _next_prev_hash(db: Session) -> str | None:
    stmt = select(AdminActionLog.curr_hash).order_by(AdminActionLog.id.desc()).limit(1)
    return db.execute(stmt).scalar_one_or_none()


def append_admin_action(
    db: Session,
    *,
    actor_user_id: str,
    action_type: AdminActionType,
    target_type: str,
    target_id: str,
    action_payload_json: str,
    request_id: str | None = None,
) -> AdminActionLog:
    prev_hash = _next_prev_hash(db)
    record_for_hash: dict[str, Any] = {
        "actor_user_id": actor_user_id,
        "action_type": action_type.value,
        "target_type": target_type,
        "target_id": target_id,
        "action_payload_json": action_payload_json,
        "request_id": request_id,
        "prev_hash": prev_hash,
    }
    curr_hash = compute_chain_hash(record_for_hash)

    row = AdminActionLog(
        actor_user_id=actor_user_id,
        action_type=action_type,
        target_type=target_type,
        target_id=target_id,
        action_payload_json=action_payload_json,
        request_id=request_id,
        prev_hash=prev_hash,
        curr_hash=curr_hash,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row
