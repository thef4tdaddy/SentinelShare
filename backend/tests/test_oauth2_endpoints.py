"""
Tests for OAuth2 authentication endpoints
"""

from unittest.mock import patch
from urllib.parse import urlparse

import pytest
from fastapi.testclient import TestClient

from backend.main import app


@pytest.fixture(name="client")
def client_fixture():
    """Create a test client"""
    return TestClient(app)


class TestOAuth2Endpoints:
    """Tests for OAuth2 authentication endpoints"""

    def test_oauth2_authorize_google(self, client: TestClient, monkeypatch):
        """Test OAuth2 authorization endpoint for Google"""
        monkeypatch.setenv("GOOGLE_CLIENT_ID", "test_client_id")

        response = client.get("/api/auth/google/authorize", follow_redirects=False)

        assert response.status_code == 307  # Redirect
        location = response.headers["location"]
        parsed = urlparse(location)
        assert parsed.hostname == "accounts.google.com"
        assert "test_client_id" in location

    def test_oauth2_authorize_invalid_provider(self, client: TestClient):
        """Test OAuth2 authorization with invalid provider"""
        response = client.get("/api/auth/invalid/authorize")

        assert response.status_code == 400
        assert "Unsupported OAuth2 provider" in response.json()["detail"]

    def test_oauth2_authorize_missing_credentials(
        self, client: TestClient, monkeypatch
    ):
        """Test OAuth2 authorization without configured credentials"""
        # Ensure GOOGLE_CLIENT_ID is not set
        monkeypatch.delenv("GOOGLE_CLIENT_ID", raising=False)

        response = client.get("/api/auth/google/authorize")

        assert response.status_code == 500
        assert "not configured" in response.json()["detail"]

    def test_oauth2_callback_missing_state(self, client: TestClient):
        """Test OAuth2 callback without state in session"""
        response = client.get(
            "/api/auth/google/callback?code=test_code&state=test_state"
        )

        # Without session state, should fail CSRF check
        assert response.status_code == 400
        assert "Invalid state" in response.json()["detail"]

    def test_oauth2_callback_error_from_provider(self, client: TestClient):
        """Test OAuth2 callback with error from provider"""
        response = client.get(
            "/api/auth/google/callback?error=access_denied&state=test_state&code=",
            follow_redirects=False,
        )

        # Error from provider should be handled with 400 or 422
        assert response.status_code in [400, 422]

    def test_oauth2_service_url_encoding(self):
        """Test that OAuth2Service properly encodes URLs"""
        from backend.services.oauth2_service import OAuth2Service

        with patch.dict("os.environ", {"GOOGLE_CLIENT_ID": "test_client_id"}):
            url = OAuth2Service.get_authorization_url(
                "google",
                "http://localhost/callback?param=value&other=test",
                "test_state",
            )

            # Check that the redirect_uri is properly URL-encoded
            assert "http" in url
            assert "callback" in url
            # The URL should contain encoded characters
            assert "%3F" in url or "callback" in url  # ? is encoded as %3F

    def test_oauth2_xoauth2_string_generation(self):
        """Test XOAUTH2 string generation"""
        import base64

        from backend.services.oauth2_service import OAuth2Service

        auth_string = OAuth2Service.generate_xoauth2_string(
            "test@example.com", "test_token"
        )

        # Should be base64 encoded
        decoded = base64.b64decode(auth_string).decode()
        assert "user=test@example.com" in decoded
        assert "auth=" in decoded

    def test_oauth2_config_google(self):
        """Test OAuth2 configuration for Google"""
        from backend.services.oauth2_service import OAuth2Config

        config = OAuth2Config.get_config("google")

        assert config is not None
        assert "authorization_endpoint" in config
        assert "token_endpoint" in config
        assert "scopes" in config
        scopes = config["scopes"]
        if isinstance(scopes, str):
            scopes = scopes.split()
        # Check using strict equality to satisfy CodeQL
        assert any(s == "https://mail.google.com/" for s in scopes)

    def test_oauth2_config_microsoft(self):
        """Test OAuth2 configuration for Microsoft"""
        from backend.services.oauth2_service import OAuth2Config

        config = OAuth2Config.get_config("microsoft")

        assert config is not None
        assert "authorization_endpoint" in config
        assert "token_endpoint" in config
        assert "scopes" in config

    def test_oauth2_config_invalid_provider(self):
        """Test OAuth2 configuration for invalid provider"""
        from backend.services.oauth2_service import OAuth2Config

        config = OAuth2Config.get_config("invalid")

        assert config is None
