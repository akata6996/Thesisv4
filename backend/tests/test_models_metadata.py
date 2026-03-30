from sqlalchemy import create_engine, inspect

from app.db.base import Base
import app.models  # noqa: F401


def test_all_phase2_tables_present() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    tables = set(inspect(engine).get_table_names())
    expected = {
        "users",
        "enrollment_registry",
        "session_state",
        "verification_log",
        "rejection_log",
        "merkle_batches",
        "blockchain_anchors",
        "admin_action_log",
        "audit_exports",
    }
    assert expected.issubset(tables)
