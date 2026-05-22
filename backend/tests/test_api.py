import uuid
import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch

from app.main import app
from app.database import Base, engine

client = TestClient(app)


def _uid() -> str:
    return uuid.uuid4().hex[:8]


def _data(resp):
    body = resp.json()
    assert "code" in body and "message" in body
    return body["data"]


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["code"] == 200
    assert body["data"]["status"] == "ok"


def test_register_duplicate_account():
    account = f"dup_{_uid()}"
    payload = {
        "account": account,
        "password": "test1234",
        "email": f"{account}@test.com",
    }
    r1 = client.post("/api/v1/auth/register", json=payload)
    assert r1.status_code == 201
    r2 = client.post("/api/v1/auth/register", json=payload)
    assert r2.status_code == 400
    assert "账号" in r2.json()["message"]


def test_register_and_login():
    account = f"testuser1_{_uid()}"
    r = client.post(
        "/api/v1/auth/register",
        json={"account": account, "password": "test1234", "email": f"{account}@test.com"},
    )
    assert r.status_code == 201
    token = _data(r)["access_token"]
    assert token

    r2 = client.post(
        "/api/v1/auth/login",
        json={"account": account, "password": "test1234"},
    )
    assert r2.status_code == 200
    assert _data(r2)["access_token"]


def test_interview_crud():
    account = f"testuser2_{_uid()}"
    r = client.post(
        "/api/v1/auth/register",
        json={"account": account, "password": "test1234", "phone": f"139{_uid()}"},
    )
    token = _data(r)["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    from datetime import datetime
    r2 = client.post(
        "/api/v1/interviews",
        headers=headers,
        json={
            "company_name": "测试公司",
            "job_title": "工程师",
            "interview_time": datetime.now().isoformat(),
            "visibility": 1,
        },
    )
    assert r2.status_code == 201
    record_id = _data(r2)["id"]

    r3 = client.get("/api/v1/interviews", headers=headers)
    assert r3.status_code == 200
    assert _data(r3)["total"] >= 1

    mock_redis = MagicMock()
    mock_redis.get.return_value = None
    mock_redis.setex.return_value = True
    with patch("app.services.task_service.get_redis", return_value=mock_redis):
        r4 = client.post(f"/api/v1/interviews/{record_id}/ai/analyze", headers=headers)
    assert r4.status_code == 200
    task_id = _data(r4)["task_id"]
    assert task_id
