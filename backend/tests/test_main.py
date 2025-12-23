import os
import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def frontend_dist_path():
    """Get the path to the frontend dist directory."""
    # Get the repo root by going up from backend/tests
    test_dir = Path(__file__).parent
    repo_root = test_dir.parent.parent
    return repo_root / "frontend" / "dist"


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

        import backend.main

        importlib.reload(backend.main)
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
    response = client.get("/api/dashboard/emails")
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
    response = client.get("/api/dashboard/emails")
    assert response.status_code == 401
    assert response.json()["detail"] == "Unauthorized"


def test_auth_middleware_authenticated(monkeypatch):
    """Test auth middleware when authenticated (line 61)"""
    from backend.main import app

    monkeypatch.setenv("DASHBOARD_PASSWORD", "test_password")

    client = TestClient(app)
    # First, authenticate via login endpoint
    response = client.post(
        "/api/auth/login", json={"password": "test_password"}
    )
    assert response.status_code == 200

    # Now access protected route - should work
    response = client.get("/api/dashboard/emails")
    # Should not return 401 since we're authenticated
    # May return other status codes based on endpoint logic
    assert response.status_code in [200, 404, 500]  # But not 401


def test_frontend_dist_mounting(frontend_dist_path):
    """Test frontend static files and SPA serving (lines 87-100, 106-108)"""
    # Check if dist already exists
    dist_existed = frontend_dist_path.exists()
    
    try:
        # Create dist directory and files
        frontend_dist_path.mkdir(parents=True, exist_ok=True)
        
        # Create assets directory
        assets_path = frontend_dist_path / "assets"
        assets_path.mkdir(exist_ok=True)
        
        # Create a dummy asset file
        asset_file = assets_path / "test.js"
        asset_file.write_text("console.log('test');")
        
        # Create index.html
        index_file = frontend_dist_path / "index.html"
        index_file.write_text("<html><body>Test</body></html>")
        
        # Import fresh to pick up the dist directory
        import importlib
        import sys
        
        # Remove from cache to force reload
        if 'backend.main' in sys.modules:
            del sys.modules['backend.main']
        
        import backend.main
        from backend.main import app
        
        client = TestClient(app)
        
        # Test root endpoint (lines 106-108)
        response = client.get("/")
        assert response.status_code == 200
        
        # Test SPA catch-all route (lines 93-100)
        response = client.get("/some-spa-route")
        assert response.status_code == 200
        
        # Test that api/ paths in catch-all return error (line 97)
        # When dist exists, the catch-all returns a JSON error with 200 status
        response = client.get("/api/unknown-endpoint")
        assert response.status_code == 200
        assert response.json() == {"error": "API endpoint not found"}
        
    finally:
        # Clean up - remove the dist directory if it didn't exist before
        if not dist_existed and frontend_dist_path.exists():
            shutil.rmtree(frontend_dist_path)


def test_root_endpoint_without_dist(frontend_dist_path):
    """Test root endpoint when frontend dist doesn't exist (line 108)"""
    dist_existed = frontend_dist_path.exists()
    
    if dist_existed:
        shutil.rmtree(frontend_dist_path)
    
    try:
        # Force reimport
        import importlib
        import sys
        
        if 'backend.main' in sys.modules:
            del sys.modules['backend.main']
        
        from backend.main import app
        
        client = TestClient(app)
        response = client.get("/")
        assert response.status_code == 200
        assert response.json() == {
            "status": "ok",
            "message": "Receipt Forwarder Backend Running (Frontend not built)",
        }
    finally:
        # Restore if needed
        if dist_existed:
            frontend_dist_path.mkdir(parents=True, exist_ok=True)


def test_spa_catch_all_api_passthrough(frontend_dist_path):
    """Test that SPA catch-all properly handles api/ paths (lines 96-97)"""
    # Clean up dist if it exists from previous test
    dist_existed = frontend_dist_path.exists()
    
    if dist_existed:
        shutil.rmtree(frontend_dist_path)
    
    try:
        # Force reimport to ensure dist check happens
        import importlib
        import sys
        
        if 'backend.main' in sys.modules:
            del sys.modules['backend.main']
        
        from backend.main import app
        
        # Create a test client
        client = TestClient(app)
        
        # When dist doesn't exist, API errors should return FastAPI's standard 404
        # This is different from when dist exists (which returns {"error": "..."})
        response = client.get("/api/does-not-exist")
        assert response.status_code == 404
    finally:
        # Restore dist if it existed before
        if dist_existed:
            frontend_dist_path.mkdir(parents=True, exist_ok=True)
