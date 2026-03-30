"""Authentication service logic."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User, UserRole


class AuthError(ValueError):
    """Raised on authentication or bootstrap failures."""


def authenticate_user(db: Session, username: str, password: str) -> str:
    stmt = select(User).where(func.lower(User.username) == username.lower())
    user = db.execute(stmt).scalar_one_or_none()
    if not user or not verify_password(password, user.password_hash):
        raise AuthError("Invalid username or password")
    if not user.is_active:
        raise AuthError("User is inactive")
    return create_access_token(user.id)


def bootstrap_operator_if_empty(db: Session, username: str, password: str) -> User:
    user_count = db.execute(select(func.count(User.id))).scalar_one()
    if user_count > 0:
        raise AuthError("Bootstrap disabled after first user is created")

    user = User(
        username=username,
        password_hash=hash_password(password),
        role=UserRole.operator,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
