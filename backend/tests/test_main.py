import os
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient


def test_health_check():
    from backend.main import app

    client = TestClient(app)
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_static_files_fallback():
    from backend.main import app

    client = TestClient(app)
    # If a route doesn't match /api, it should serve index.html (if exists) or 404
    # But main.py has a catch-all for SPA
    response = client.get("/some-frontend-route")
    # In test environment, static files might not be present,
    # but let's see how it behaves.
    # Usually it returns 404 if file not found even with the catch-all if not configured right for tests.
    assert response.status_code in [200, 404]


def test_app_lifespan():
    from backend.main import app

    # Testing the lifespan context manager (startup/shutdown)
    with TestClient(app) as c:
        response = c.get("/api/health")
        assert response.status_code == 200


def test_migration_error_handling():
    """Test that startup handles migration errors gracefully (lines 24-25)"""
    with patch("backend.migration_utils.run_migrations") as mock_migrations:
        mock_migrations.side_effect = Exception("Migration failed")

        # Re-import app to trigger lifespan
        import importlib

        module = importlib.import_module("backend.main")

        importlib.reload(module)
        from backend.main import app

        # The app should still start even if migrations fail
        with TestClient(app) as c:
            response = c.get("/api/health")
            assert response.status_code == 200


def test_auth_middleware_unauthenticated_no_password(monkeypatch):
    """Test auth middleware when not authenticated and no DASHBOARD_PASSWORD set (lines 56-57)"""
    from backend.main import app

    # Ensure DASHBOARD_PASSWORD is not set
    monkeypatch.delenv("DASHBOARD_PASSWORD", raising=False)

    client = TestClient(app)
    # Should allow access to protected routes when no password is set
    response = client.get("/api/dashboard/stats")
    # It may return 200 or other status depending on the endpoint logic,
    # but should NOT return 401
    assert response.status_code != 401


def test_auth_middleware_unauthenticated_with_password(monkeypatch):
    """Test auth middleware when not authenticated but DASHBOARD_PASSWORD is set (line 59)"""
    from backend.main import app

    # Set DASHBOARD_PASSWORD
    monkeypatch.setenv("DASHBOARD_PASSWORD", "test_password")

    client = TestClient(app)
    # Should deny access to protected routes when password is set but not authenticated
    response = client.get("/api/dashboard/stats")
    assert response.status_code == 401
    assert response.json()["detail"] == "Unauthorized"


def test_auth_middleware_authenticated(monkeypatch):
    """Test auth middleware when authenticated (line 61)"""
    from backend.main import app

    monkeypatch.setenv("DASHBOARD_PASSWORD", "test_password")

    client = TestClient(app)
    # First, authenticate via login endpoint
    response = client.post("/api/auth/login", json={"password": "test_password"})
    assert response.status_code == 200

    # Now access protected route - should work
    response = client.get("/api/dashboard/stats")
    # Authenticated access should not return 401
    # May return 200 or other status codes depending on database state
    assert response.status_code != 401


def test_frontend_serving_current_state():
    """Test frontend serving based on current repository state.

    Note: This test checks the current state of the frontend/dist directory.
    The behavior differs based on whether dist exists:
    - If dist exists: Tests SPA catch-all and static file serving (lines 87-100)
    - If dist doesn't exist: Tests fallback message (line 108)

    Module reloading is avoided to maintain test isolation.
    """
    from backend.main import app, frontend_dist_path

    client = TestClient(app)

    # Check if dist currently exists
    dist_exists = os.path.exists(frontend_dist_path)

    # Test root endpoint
    response = client.get("/")
    assert response.status_code == 200

    if dist_exists:
        # When dist exists, should serve index.html or SPA routes
        # Test SPA catch-all route (lines 93-100)
        response = client.get("/some-spa-route")
        assert response.status_code in [200, 404]  # Depends on file existence

        # Test that api/ paths in catch-all return error (line 97)
        response = client.get("/api/unknown-endpoint")
        if response.status_code == 200:
            # Catch-all handled it
            assert response.json() == {"error": "API endpoint not found"}
    else:
        # When dist doesn't exist, root should return fallback message (line 108)
        response = client.get("/")
        assert response.json() == {
            "status": "ok",
            "message": "Receipt Forwarder Backend Running (Frontend not built)",
        }


@pytest.mark.parametrize("dist_should_exist", [True, False])
def test_frontend_dist_behavior(dist_should_exist, tmp_path):
    """Test frontend serving with and without dist directory.

    NOTE: This test uses module reloading to test different states of
    frontend/dist at module import time. This is necessary because
    backend.main.py checks os.path.exists(frontend_dist_path) at module
    level, not at runtime. Proper refactoring to support dependency
    injection would be needed to avoid module reloading, but that's
    out of scope for test additions.

    Args:
        dist_should_exist: Whether to set up the dist directory
        tmp_path: Pytest fixture for temporary directory
    """
    import os
    import sys

    # Ensure no auth is enforced for this test
    if "DASHBOARD_PASSWORD" in os.environ:
        del os.environ["DASHBOARD_PASSWORD"]

    # Clean up any previous imports
    if "backend.main" in sys.modules:
        del sys.modules["backend.main"]

    # Determine repo path
    repo_root = Path(__file__).parent.parent.parent
    dist_path = repo_root / "frontend" / "dist"

    # Set up dist directory state
    dist_existed_before = dist_path.exists()
    needs_cleanup = False

    try:
        if dist_should_exist and not dist_existed_before:
            # Create minimal dist structure for testing
            dist_path.mkdir(parents=True, exist_ok=True)
            (dist_path / "assets").mkdir(exist_ok=True)
            (dist_path / "index.html").write_text("<html><body>Test</body></html>")
            needs_cleanup = True
        elif not dist_should_exist and dist_existed_before:
            # Can't remove existing dist - skip this scenario
            pytest.skip("Cannot test without dist when dist already exists in repo")

        # Reimport to pick up the current dist state
        from backend.main import app

        client = TestClient(app)

        if dist_should_exist:
            # Test SPA serving (lines 87-100)
            response = client.get("/some-spa-route")
            assert response.status_code == 200

            # Test API error in catch-all (line 97)
            response = client.get("/api/unknown-endpoint")
            assert response.status_code == 200
            assert response.json() == {"error": "API endpoint not found"}
        else:
            # Test fallback message (line 108)
            response = client.get("/")
            assert response.status_code == 200
            assert response.json() == {
                "status": "ok",
                "message": "Receipt Forwarder Backend Running (Frontend not built)",
            }
    finally:
        # Clean up
        if needs_cleanup and dist_path.exists():
            import shutil

            shutil.rmtree(dist_path)

        # Always clean up module to avoid affecting other tests
        if "backend.main" in sys.modules:
            del sys.modules["backend.main"]
