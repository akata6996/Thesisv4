from collections.abc import Generator
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from app.api.deps import get_db
from app.core.security import hash_password
from app.db.base import Base
from app.main import app
import app.models as models  # noqa: F401
from app.models.admin import AdminActionLog
from app.models.user import User, UserRole


def _build_test_client(tmp_db_path: Path) -> tuple[TestClient, sessionmaker[Session]]:
    engine = create_engine(f"sqlite:///{tmp_db_path}", connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    Base.metadata.create_all(bind=engine)

    def override_get_db() -> Generator[Session, None, None]:
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app), TestingSessionLocal


def _login(client: TestClient, username: str, password: str) -> str:
    response = client.post("/api/v1/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


def test_enroll_and_reset_requires_operator(tmp_path: Path) -> None:
    client, test_session = _build_test_client(tmp_path / "admin_test.db")

    bootstrap = client.post("/api/v1/auth/bootstrap", json={"username": "operator", "password": "password123"})
    assert bootstrap.status_code == 201

    with test_session() as db:
        viewer = User(
            username="viewer",
            password_hash=hash_password("password123"),
            role=UserRole.viewer,
            is_active=True,
        )
        db.add(viewer)
        db.commit()

    operator_token = _login(client, "operator", "password123")
    viewer_token = _login(client, "viewer", "password123")

    forbidden = client.post(
        "/api/v1/admin/nodes/enroll",
        json={"node_id": "esp32-01", "display_name": "Lab Node 01"},
        headers={"Authorization": f"Bearer {viewer_token}"},
    )
    assert forbidden.status_code == 403

    enroll = client.post(
        "/api/v1/admin/nodes/enroll",
        json={"node_id": "esp32-01", "display_name": "Lab Node 01"},
        headers={"Authorization": f"Bearer {operator_token}"},
    )
    assert enroll.status_code == 201

    duplicate = client.post(
        "/api/v1/admin/nodes/enroll",
        json={"node_id": "esp32-01", "display_name": "Lab Node 01"},
        headers={"Authorization": f"Bearer {operator_token}"},
    )
    assert duplicate.status_code == 409

    list_nodes = client.get("/api/v1/admin/nodes", headers={"Authorization": f"Bearer {viewer_token}"})
    assert list_nodes.status_code == 200
    assert len(list_nodes.json()) == 1
    assert list_nodes.json()[0]["node_id"] == "esp32-01"

    reset = client.post(
        "/api/v1/admin/session/reset",
        json={"reason": "Operator requested new acquisition run"},
        headers={"Authorization": f"Bearer {operator_token}"},
    )
    assert reset.status_code == 200
    assert reset.json()["reset_counter"] == 1

    with test_session() as db:
        actions = db.execute(select(AdminActionLog).order_by(AdminActionLog.id.asc())).scalars().all()
        action_types = [a.action_type.value for a in actions]
        assert action_types == ["user_login", "user_login", "node_enroll", "session_reset"]

    app.dependency_overrides.clear()
