"""Schemas for Phase 4 admin operations."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class NodeEnrollmentRequest(BaseModel):
    node_id: str = Field(min_length=3, max_length=128)
    display_name: str = Field(min_length=1, max_length=128)
    pubkey_fingerprint: str | None = Field(default=None, max_length=128)


class NodeEnrollmentResponse(BaseModel):
    id: str
    node_id: str
    display_name: str
    pubkey_fingerprint: str | None
    enrollment_status: str
    created_at: datetime


class NodeRegistryItem(BaseModel):
    id: str
    node_id: str
    display_name: str
    enrollment_status: str
    created_at: datetime
    revoked_at: datetime | None


class SessionResetRequest(BaseModel):
    reason: str = Field(min_length=5, max_length=500)


class SessionResetResponse(BaseModel):
    current_session_id: str
    session_started_at: datetime
    reset_counter: int
