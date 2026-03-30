"""Authentication routes for local operator/viewer access."""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_operator
from app.models.admin import AdminActionType
from app.models.user import User
from app.schemas.auth import BootstrapRequest, LoginRequest, TokenResponse, UserMeResponse
from app.services.admin_audit_service import append_admin_action
from app.services.auth_service import AuthError, authenticate_user, bootstrap_operator_if_empty

router = APIRouter()


@router.post("/bootstrap", response_model=UserMeResponse, status_code=status.HTTP_201_CREATED)
def bootstrap_first_operator(payload: BootstrapRequest, db: Session = Depends(get_db)) -> UserMeResponse:
    try:
        user = bootstrap_operator_if_empty(db, username=payload.username, password=payload.password)
    except AuthError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return UserMeResponse(id=user.id, username=user.username, role=user.role.value, is_active=user.is_active)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    try:
        token = authenticate_user(db, username=payload.username, password=payload.password)
    except AuthError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    user = db.query(User).filter(User.username.ilike(payload.username)).first()
    if user is not None:
        append_admin_action(
            db,
            actor_user_id=user.id,
            action_type=AdminActionType.user_login,
            target_type="auth",
            target_id=user.id,
            action_payload_json=json.dumps({"username": user.username}),
        )

    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserMeResponse)
def me(current_user: User = Depends(get_current_user)) -> UserMeResponse:
    return UserMeResponse(
        id=current_user.id,
        username=current_user.username,
        role=current_user.role.value,
        is_active=current_user.is_active,
    )


@router.get("/operator-check")
def operator_check(_: User = Depends(require_operator)) -> dict[str, str]:
    """Simple guard endpoint to validate operator-only dependency wiring."""
    return {"status": "operator-ok"}
