"""initial phase2 schema

Revision ID: 20260330_0001
Revises: 
Create Date: 2026-03-30 00:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260330_0001"
down_revision = None
branch_labels = None
depends_on = None


user_role = sa.Enum("viewer", "operator", name="user_role")
enrollment_status = sa.Enum("active", "revoked", name="enrollment_status")
batch_status = sa.Enum("pending", "anchored", "failed", name="batch_status")
anchor_status = sa.Enum("pending", "confirmed", "failed", name="anchor_status")
admin_action_type = sa.Enum(
    "node_enroll", "node_revoke", "session_reset", "export_request", "user_login", name="admin_action_type"
)
export_status = sa.Enum("queued", "completed", "failed", name="export_status")


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("username", sa.String(length=64), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", user_role, nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("username"),
    )
    op.create_index("ix_users_username", "users", ["username"])
    op.create_index("ix_users_role", "users", ["role"])

    op.create_table(
        "session_state",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("current_session_id", sa.String(length=36), nullable=False),
        sa.Column("session_started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reset_counter", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("id = 1", name="ck_session_state_singleton"),
    )
    op.create_index("ix_session_state_current_session_id", "session_state", ["current_session_id"])

    op.create_table(
        "enrollment_registry",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("node_id", sa.String(length=128), nullable=False),
        sa.Column("display_name", sa.String(length=128), nullable=False),
        sa.Column("pubkey_fingerprint", sa.String(length=128), nullable=True),
        sa.Column("enrolled_by_user_id", sa.String(length=36), nullable=False),
        sa.Column("enrollment_status", enrollment_status, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["enrolled_by_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("node_id"),
    )
    op.create_index("ix_enrollment_registry_node_id", "enrollment_registry", ["node_id"])
    op.create_index("ix_enrollment_registry_enrolled_by_user_id", "enrollment_registry", ["enrolled_by_user_id"])
    op.create_index("ix_enrollment_registry_enrollment_status", "enrollment_registry", ["enrollment_status"])

    op.create_table(
        "verification_log",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("session_id", sa.String(length=36), nullable=False),
        sa.Column("node_id", sa.String(length=128), nullable=False),
        sa.Column("gateway_received_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("device_timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("payload_canonical_json", sa.Text(), nullable=False),
        sa.Column("payload_hash", sa.String(length=64), nullable=False),
        sa.Column("validation_profile_version", sa.String(length=32), nullable=False),
        sa.Column("prev_hash", sa.String(length=64), nullable=True),
        sa.Column("curr_hash", sa.String(length=64), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("curr_hash"),
    )
    op.create_index("ix_verification_log_session_id", "verification_log", ["session_id"])
    op.create_index("ix_verification_log_node_id", "verification_log", ["node_id"])
    op.create_index("ix_verification_log_gateway_received_at", "verification_log", ["gateway_received_at"])
    op.create_index("ix_verification_log_curr_hash", "verification_log", ["curr_hash"])

    op.create_table(
        "rejection_log",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("session_id", sa.String(length=36), nullable=False),
        sa.Column("node_id", sa.String(length=128), nullable=False),
        sa.Column("gateway_received_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("device_timestamp", sa.DateTime(timezone=True), nullable=True),
        sa.Column("payload_canonical_json", sa.Text(), nullable=False),
        sa.Column("rejection_code", sa.String(length=64), nullable=False),
        sa.Column("rejection_reason", sa.Text(), nullable=False),
        sa.Column("rule_version", sa.String(length=32), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("rejection_code <> ''", name="ck_rejection_code_non_empty"),
    )
    op.create_index("ix_rejection_log_session_id", "rejection_log", ["session_id"])
    op.create_index("ix_rejection_log_node_id", "rejection_log", ["node_id"])
    op.create_index("ix_rejection_log_gateway_received_at", "rejection_log", ["gateway_received_at"])
    op.create_index("ix_rejection_log_rejection_code", "rejection_log", ["rejection_code"])

    op.create_table(
        "merkle_batches",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("batch_uuid", sa.String(length=36), nullable=False),
        sa.Column("session_id", sa.String(length=36), nullable=False),
        sa.Column("from_verification_id", sa.Integer(), nullable=False),
        sa.Column("to_verification_id", sa.Integer(), nullable=False),
        sa.Column("leaf_count", sa.Integer(), nullable=False),
        sa.Column("merkle_root", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", batch_status, nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("batch_uuid"),
        sa.CheckConstraint("leaf_count > 0", name="ck_merkle_leaf_count_positive"),
        sa.CheckConstraint("to_verification_id >= from_verification_id", name="ck_merkle_id_range_valid"),
    )
    op.create_index("ix_merkle_batches_session_id", "merkle_batches", ["session_id"])
    op.create_index("ix_merkle_batches_merkle_root", "merkle_batches", ["merkle_root"])
    op.create_index("ix_merkle_batches_status", "merkle_batches", ["status"])

    op.create_table(
        "blockchain_anchors",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("merkle_batch_id", sa.Integer(), nullable=False),
        sa.Column("chain", sa.String(length=32), nullable=False),
        sa.Column("tx_signature", sa.String(length=128), nullable=True),
        sa.Column("slot", sa.Integer(), nullable=True),
        sa.Column("anchored_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("confirm_status", anchor_status, nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["merkle_batch_id"], ["merkle_batches.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("merkle_batch_id"),
    )
    op.create_index("ix_blockchain_anchors_tx_signature", "blockchain_anchors", ["tx_signature"])
    op.create_index("ix_blockchain_anchors_confirm_status", "blockchain_anchors", ["confirm_status"])

    op.create_table(
        "admin_action_log",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("actor_user_id", sa.String(length=36), nullable=False),
        sa.Column("action_type", admin_action_type, nullable=False),
        sa.Column("target_type", sa.String(length=64), nullable=False),
        sa.Column("target_id", sa.String(length=64), nullable=False),
        sa.Column("request_id", sa.String(length=64), nullable=True),
        sa.Column("action_payload_json", sa.Text(), nullable=False),
        sa.Column("prev_hash", sa.String(length=64), nullable=True),
        sa.Column("curr_hash", sa.String(length=64), nullable=False),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("curr_hash"),
    )
    op.create_index("ix_admin_action_log_occurred_at", "admin_action_log", ["occurred_at"])
    op.create_index("ix_admin_action_log_actor_user_id", "admin_action_log", ["actor_user_id"])
    op.create_index("ix_admin_action_log_action_type", "admin_action_log", ["action_type"])
    op.create_index("ix_admin_action_log_curr_hash", "admin_action_log", ["curr_hash"])

    op.create_table(
        "audit_exports",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("requested_by_user_id", sa.String(length=36), nullable=False),
        sa.Column("export_type", sa.String(length=64), nullable=False),
        sa.Column("filter_json", sa.Text(), nullable=False),
        sa.Column("status", export_status, nullable=False),
        sa.Column("artifact_path", sa.String(length=255), nullable=True),
        sa.Column("artifact_hash", sa.String(length=64), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["requested_by_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audit_exports_requested_at", "audit_exports", ["requested_at"])
    op.create_index("ix_audit_exports_requested_by_user_id", "audit_exports", ["requested_by_user_id"])
    op.create_index("ix_audit_exports_status", "audit_exports", ["status"])


def downgrade() -> None:
    op.drop_index("ix_audit_exports_status", table_name="audit_exports")
    op.drop_index("ix_audit_exports_requested_by_user_id", table_name="audit_exports")
    op.drop_index("ix_audit_exports_requested_at", table_name="audit_exports")
    op.drop_table("audit_exports")

    op.drop_index("ix_admin_action_log_curr_hash", table_name="admin_action_log")
    op.drop_index("ix_admin_action_log_action_type", table_name="admin_action_log")
    op.drop_index("ix_admin_action_log_actor_user_id", table_name="admin_action_log")
    op.drop_index("ix_admin_action_log_occurred_at", table_name="admin_action_log")
    op.drop_table("admin_action_log")

    op.drop_index("ix_blockchain_anchors_confirm_status", table_name="blockchain_anchors")
    op.drop_index("ix_blockchain_anchors_tx_signature", table_name="blockchain_anchors")
    op.drop_table("blockchain_anchors")

    op.drop_index("ix_merkle_batches_status", table_name="merkle_batches")
    op.drop_index("ix_merkle_batches_merkle_root", table_name="merkle_batches")
    op.drop_index("ix_merkle_batches_session_id", table_name="merkle_batches")
    op.drop_table("merkle_batches")

    op.drop_index("ix_rejection_log_rejection_code", table_name="rejection_log")
    op.drop_index("ix_rejection_log_gateway_received_at", table_name="rejection_log")
    op.drop_index("ix_rejection_log_node_id", table_name="rejection_log")
    op.drop_index("ix_rejection_log_session_id", table_name="rejection_log")
    op.drop_table("rejection_log")

    op.drop_index("ix_verification_log_curr_hash", table_name="verification_log")
    op.drop_index("ix_verification_log_gateway_received_at", table_name="verification_log")
    op.drop_index("ix_verification_log_node_id", table_name="verification_log")
    op.drop_index("ix_verification_log_session_id", table_name="verification_log")
    op.drop_table("verification_log")

    op.drop_index("ix_enrollment_registry_enrollment_status", table_name="enrollment_registry")
    op.drop_index("ix_enrollment_registry_enrolled_by_user_id", table_name="enrollment_registry")
    op.drop_index("ix_enrollment_registry_node_id", table_name="enrollment_registry")
    op.drop_table("enrollment_registry")

    op.drop_index("ix_session_state_current_session_id", table_name="session_state")
    op.drop_table("session_state")

    op.drop_index("ix_users_role", table_name="users")
    op.drop_index("ix_users_username", table_name="users")
    op.drop_table("users")

    export_status.drop(op.get_bind(), checkfirst=True)
    admin_action_type.drop(op.get_bind(), checkfirst=True)
    anchor_status.drop(op.get_bind(), checkfirst=True)
    batch_status.drop(op.get_bind(), checkfirst=True)
    enrollment_status.drop(op.get_bind(), checkfirst=True)
    user_role.drop(op.get_bind(), checkfirst=True)
