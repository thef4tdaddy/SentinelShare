from backend.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_login_success(monkeypatch):
    monkeypatch.setenv("DASHBOARD_PASSWORD", "testpass")
    response = client.post("/api/auth/login", json={"password": "testpass"})
    assert response.status_code == 200
    assert response.json()["status"] == "success"


def test_login_failure(monkeypatch):
    monkeypatch.setenv("DASHBOARD_PASSWORD", "testpass")
    response = client.post("/api/auth/login", json={"password": "wrong"})
    assert response.status_code == 401


def test_check_auth(monkeypatch):
    monkeypatch.setenv("DASHBOARD_PASSWORD", "testpass")
    # Login first
    client.post("/api/auth/login", json={"password": "testpass"})

    response = client.get("/api/auth/me")
    assert response.status_code == 200
    assert response.json()["authenticated"] is True


def test_check_auth_failure():
    # Ensure fresh client or clear session
    fresh_client = TestClient(app)
    response = fresh_client.get("/api/auth/me")
    assert response.status_code == 401
