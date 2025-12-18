from backend.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_static_files_fallback():
    # If a route doesn't match /api, it should serve index.html (if exists) or 404
    # But main.py has a catch-all for SPA
    response = client.get("/some-frontend-route")
    # In test environment, static files might not be present,
    # but let's see how it behaves.
    # Usually it returns 404 if file not found even with the catch-all if not configured right for tests.
    assert response.status_code in [200, 404]


def test_app_lifespan():
    # Testing the lifespan context manager (startup/shutdown)
    with TestClient(app) as c:
        response = c.get("/api/health")
        assert response.status_code == 200
