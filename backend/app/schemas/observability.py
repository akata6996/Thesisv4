"""Schemas for Phase 5 observability APIs."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class VerificationLogItem(BaseModel):
    id: int
    session_id: str
    node_id: str
    gateway_received_at: datetime
    device_timestamp: datetime
    payload_hash: str
    validation_profile_version: str
    prev_hash: str | None
    curr_hash: str


class RejectionLogItem(BaseModel):
    id: int
    session_id: str
    node_id: str
    gateway_received_at: datetime
    rejection_code: str
    rejection_reason: str
    rule_version: str


class MerkleBatchItem(BaseModel):
    id: int
    batch_uuid: str
    session_id: str
    from_verification_id: int
    to_verification_id: int
    leaf_count: int
    merkle_root: str
    status: str
    created_at: datetime


class BlockchainAnchorItem(BaseModel):
    id: int
    merkle_batch_id: int
    chain: str
    tx_signature: str | None
    slot: int | None
    anchored_at: datetime | None
    confirm_status: str
    error_message: str | None


class VerificationDetailResponse(VerificationLogItem):
    payload_canonical_json: str


class DashboardSummaryResponse(BaseModel):
    total_verified: int
    total_rejected: int
    active_nodes: int
    latest_merkle_root: str | None
    latest_anchor_status: str | None
