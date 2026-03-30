from collections.abc import Generator
from datetime import datetime, timezone
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.api.deps import get_db
from app.core.security import hash_password
from app.db.base import Base
from app.main import app
from app.models.enrollment import EnrollmentRegistry, EnrollmentStatus
from app.models.merkle import AnchorStatus, BatchStatus, BlockchainAnchor, MerkleBatch
from app.models.user import User, UserRole
from app.models.verification import RejectionLog, VerificationLog


def _build_test_client(tmp_db_path: Path) -> tuple[TestClient, sessionmaker[Session]]:
    engine = create_engine(f"sqlite:///{tmp_db_path}", connect_args={"check_same_thread": False})
    testing_session = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    Base.metadata.create_all(bind=engine)

    def override_get_db() -> Generator[Session, None, None]:
        db = testing_session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app), testing_session


def _login(client: TestClient, username: str, password: str) -> str:
    response = client.post("/api/v1/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


def test_observability_endpoints_for_authenticated_user(tmp_path: Path) -> None:
    client, db_session = _build_test_client(tmp_path / "obs_test.db")

    with db_session() as db:
        operator = User(username="operator", password_hash=hash_password("password123"), role=UserRole.operator, is_active=True)
        viewer = User(username="viewer", password_hash=hash_password("password123"), role=UserRole.viewer, is_active=True)
        db.add_all([operator, viewer])
        db.flush()

        registry = EnrollmentRegistry(
            node_id="esp32-01",
            display_name="Node 1",
            enrolled_by_user_id=operator.id,
            enrollment_status=EnrollmentStatus.active,
        )
        db.add(registry)

        v1 = VerificationLog(
            session_id="session-a",
            node_id="esp32-01",
            gateway_received_at=datetime.now(timezone.utc),
            device_timestamp=datetime.now(timezone.utc),
            payload_canonical_json='{"temp":25}',
            payload_hash="hash1",
            validation_profile_version="v1",
            prev_hash=None,
            curr_hash="curr1",
        )
        db.add(v1)

        r1 = RejectionLog(
            session_id="session-a",
            node_id="esp32-01",
            gateway_received_at=datetime.now(timezone.utc),
            device_timestamp=datetime.now(timezone.utc),
            payload_canonical_json='{"temp":999}',
            rejection_code="OUT_OF_WINDOW",
            rejection_reason="timestamp too old",
            rule_version="v1",
        )
        db.add(r1)
        db.flush()

        mb = MerkleBatch(
            session_id="session-a",
            from_verification_id=v1.id,
            to_verification_id=v1.id,
            leaf_count=1,
            merkle_root="root1",
            status=BatchStatus.pending,
        )
        db.add(mb)
        db.flush()

        anchor = BlockchainAnchor(
            merkle_batch_id=mb.id,
            chain="solana-devnet",
            tx_signature="tx1",
            confirm_status=AnchorStatus.pending,
        )
        db.add(anchor)
        db.commit()

    token = _login(client, "viewer", "password123")
    headers = {"Authorization": f"Bearer {token}"}

    verifications = client.get("/api/v1/observability/verification-log", headers=headers)
    assert verifications.status_code == 200
    assert len(verifications.json()) == 1

    verification_detail = client.get("/api/v1/observability/verification-log/1", headers=headers)
    assert verification_detail.status_code == 200
    assert verification_detail.json()["payload_hash"] == "hash1"

    rejections = client.get("/api/v1/observability/rejection-log?rejection_code=OUT_OF_WINDOW", headers=headers)
    assert rejections.status_code == 200
    assert len(rejections.json()) == 1

    merkle = client.get("/api/v1/observability/merkle-batches", headers=headers)
    assert merkle.status_code == 200
    assert len(merkle.json()) == 1

    anchors = client.get("/api/v1/observability/anchors", headers=headers)
    assert anchors.status_code == 200
    assert len(anchors.json()) == 1

    dashboard = client.get("/api/v1/observability/dashboard-summary", headers=headers)
    assert dashboard.status_code == 200
    assert dashboard.json()["total_verified"] == 1
    assert dashboard.json()["total_rejected"] == 1
    assert dashboard.json()["active_nodes"] == 1

    app.dependency_overrides.clear()
