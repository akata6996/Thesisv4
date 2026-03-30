"""Merkle batch and blockchain anchor models."""

from __future__ import annotations

import enum

from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.common import utcnow, uuid4_str


class BatchStatus(str, enum.Enum):
    pending = "pending"
    anchored = "anchored"
    failed = "failed"


class AnchorStatus(str, enum.Enum):
    pending = "pending"
    confirmed = "confirmed"
    failed = "failed"


class MerkleBatch(Base):
    __tablename__ = "merkle_batches"
    __table_args__ = (
        CheckConstraint("leaf_count > 0", name="ck_merkle_leaf_count_positive"),
        CheckConstraint("to_verification_id >= from_verification_id", name="ck_merkle_id_range_valid"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    batch_uuid: Mapped[str] = mapped_column(String(36), unique=True, default=uuid4_str, nullable=False)
    session_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    from_verification_id: Mapped[int] = mapped_column(Integer, nullable=False)
    to_verification_id: Mapped[int] = mapped_column(Integer, nullable=False)
    leaf_count: Mapped[int] = mapped_column(Integer, nullable=False)
    merkle_root: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    status: Mapped[BatchStatus] = mapped_column(Enum(BatchStatus, name="batch_status"), default=BatchStatus.pending, index=True)


class BlockchainAnchor(Base):
    __tablename__ = "blockchain_anchors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    merkle_batch_id: Mapped[int] = mapped_column(ForeignKey("merkle_batches.id"), unique=True, nullable=False)
    chain: Mapped[str] = mapped_column(String(32), default="solana-devnet", nullable=False)
    tx_signature: Mapped[str | None] = mapped_column(String(128), index=True, nullable=True)
    slot: Mapped[int | None] = mapped_column(Integer, nullable=True)
    anchored_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    confirm_status: Mapped[AnchorStatus] = mapped_column(
        Enum(AnchorStatus, name="anchor_status"), default=AnchorStatus.pending, index=True, nullable=False
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
