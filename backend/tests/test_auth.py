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


def test_login_no_password_configured(monkeypatch):
    monkeypatch.delenv("DASHBOARD_PASSWORD", raising=False)
    fresh_client = TestClient(app)
    response = fresh_client.post("/api/auth/login", json={"password": "anypass"})
    assert response.status_code == 500
    assert response.json()["error"] == "Auth not configured"


def test_logout(monkeypatch):
    monkeypatch.setenv("DASHBOARD_PASSWORD", "testpass")
    fresh_client = TestClient(app)

    # Login first
    fresh_client.post("/api/auth/login", json={"password": "testpass"})

    # Verify authenticated
    response = fresh_client.get("/api/auth/me")
    assert response.status_code == 200

    # Logout
    response = fresh_client.post("/api/auth/logout")
    assert response.status_code == 200
    assert response.json()["status"] == "logged_out"

    # Verify no longer authenticated
    response = fresh_client.get("/api/auth/me")
    assert response.status_code == 401
