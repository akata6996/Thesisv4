"""append-only guards and composite indexes

Revision ID: 20260330_0002
Revises: 20260330_0001
Create Date: 2026-03-30 00:30:00
"""

from __future__ import annotations

from alembic import op


revision = "20260330_0002"
down_revision = "20260330_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "ix_verification_log_session_id_id",
        "verification_log",
        ["session_id", "id"],
    )
    op.create_index(
        "ix_rejection_log_session_code_id",
        "rejection_log",
        ["session_id", "rejection_code", "id"],
    )
    op.create_index(
        "ix_admin_action_log_type_occurred",
        "admin_action_log",
        ["action_type", "occurred_at"],
    )

    op.execute(
        """
        CREATE TRIGGER trg_verification_log_no_update
        BEFORE UPDATE ON verification_log
        BEGIN
            SELECT RAISE(ABORT, 'verification_log is append-only');
        END;
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_verification_log_no_delete
        BEFORE DELETE ON verification_log
        BEGIN
            SELECT RAISE(ABORT, 'verification_log is append-only');
        END;
        """
    )

    op.execute(
        """
        CREATE TRIGGER trg_rejection_log_no_update
        BEFORE UPDATE ON rejection_log
        BEGIN
            SELECT RAISE(ABORT, 'rejection_log is append-only');
        END;
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_rejection_log_no_delete
        BEFORE DELETE ON rejection_log
        BEGIN
            SELECT RAISE(ABORT, 'rejection_log is append-only');
        END;
        """
    )

    op.execute(
        """
        CREATE TRIGGER trg_admin_action_log_no_update
        BEFORE UPDATE ON admin_action_log
        BEGIN
            SELECT RAISE(ABORT, 'admin_action_log is append-only');
        END;
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_admin_action_log_no_delete
        BEFORE DELETE ON admin_action_log
        BEGIN
            SELECT RAISE(ABORT, 'admin_action_log is append-only');
        END;
        """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_admin_action_log_no_delete")
    op.execute("DROP TRIGGER IF EXISTS trg_admin_action_log_no_update")
    op.execute("DROP TRIGGER IF EXISTS trg_rejection_log_no_delete")
    op.execute("DROP TRIGGER IF EXISTS trg_rejection_log_no_update")
    op.execute("DROP TRIGGER IF EXISTS trg_verification_log_no_delete")
    op.execute("DROP TRIGGER IF EXISTS trg_verification_log_no_update")

    op.drop_index("ix_admin_action_log_type_occurred", table_name="admin_action_log")
    op.drop_index("ix_rejection_log_session_code_id", table_name="rejection_log")
    op.drop_index("ix_verification_log_session_id_id", table_name="verification_log")
