import os
import sqlite3
import subprocess
from pathlib import Path


def test_append_only_triggers_from_migration(tmp_path: Path) -> None:
    db_path = tmp_path / "migration_test.db"
    env = os.environ.copy()
    env["DATABASE_URL"] = f"sqlite:///{db_path}"

    subprocess.run(["alembic", "upgrade", "head"], cwd=Path(__file__).resolve().parents[1], check=True, env=env)

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO verification_log
        (session_id, node_id, gateway_received_at, device_timestamp, payload_canonical_json, payload_hash, validation_profile_version, prev_hash, curr_hash)
        VALUES (?, ?, datetime('now'), datetime('now'), ?, ?, ?, ?, ?)
        """,
        ("s-1", "n-1", '{"temp": 1}', "h1", "v1", None, "c1"),
    )
    conn.commit()

    failed = False
    try:
        cur.execute("UPDATE verification_log SET payload_hash = ? WHERE id = 1", ("h2",))
        conn.commit()
    except sqlite3.DatabaseError:
        failed = True

    conn.close()
    assert failed
