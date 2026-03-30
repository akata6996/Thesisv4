from collections.abc import Generator
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from app.api.deps import get_db
from app.db.base import Base
from app.main import app
import app.models as models  # noqa: F401
from app.models.admin import AdminActionLog


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


def test_bootstrap_login_and_me(tmp_path: Path) -> None:
    client, test_session = _build_test_client(tmp_path / "auth_test.db")

    bootstrap = client.post("/api/v1/auth/bootstrap", json={"username": "operator", "password": "password123"})
    assert bootstrap.status_code == 201

    second_bootstrap = client.post("/api/v1/auth/bootstrap", json={"username": "operator2", "password": "password123"})
    assert second_bootstrap.status_code == 400

    login = client.post("/api/v1/auth/login", json={"username": "operator", "password": "password123"})
    assert login.status_code == 200
    token = login.json()["access_token"]

    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["username"] == "operator"
    assert me.json()["role"] == "operator"

    check = client.get("/api/v1/auth/operator-check", headers={"Authorization": f"Bearer {token}"})
    assert check.status_code == 200

    with test_session() as db:
        rows = db.execute(select(AdminActionLog).order_by(AdminActionLog.id.asc())).scalars().all()
        assert len(rows) == 1
        assert rows[0].action_type.value == "user_login"
        assert rows[0].curr_hash

    app.dependency_overrides.clear()
