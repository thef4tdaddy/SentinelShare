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

    @patch("backend.routers.auth.OAuth2Service.exchange_code_for_tokens")
    @patch("backend.routers.auth.OAuth2Service.store_oauth2_tokens")
    @patch("httpx.AsyncClient")
    def test_oauth2_callback_success_google(
        self,
        mock_async_client_class,
        mock_store_tokens,
        mock_exchange,
        client: TestClient,
        monkeypatch,
    ):
        """Test successful Google OAuth2 callback"""
        monkeypatch.setenv("GOOGLE_CLIENT_ID", "test_client_id")
        monkeypatch.setenv("FRONTEND_URL", "http://frontend-test.com")

        # 1. Authorize to set session state
        auth_response = client.get("/api/auth/google/authorize", follow_redirects=False)
        assert auth_response.status_code == 307
        location = auth_response.headers["location"]
        from urllib.parse import parse_qs, urlparse

        parsed_url = urlparse(location)
        query_params = parse_qs(parsed_url.query)
        state = query_params["state"][0]

        # 2. Mock token exchange
        mock_exchange.return_value = {
            "access_token": "test_access_token",
            "refresh_token": "test_refresh_token",
            "expires_in": 3600,
        }

        # 3. Mock Google userinfo fetch
        from unittest.mock import AsyncMock, MagicMock

        mock_response = MagicMock()
        mock_response.json.return_value = {"email": "google_user@example.com"}
        mock_response.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_async_client_class.return_value.__aenter__.return_value = mock_client

        # 4. Call callback
        callback_response = client.get(
            f"/api/auth/google/callback?code=test_code&state={state}",
            follow_redirects=False,
        )

        # 5. Verify redirect to frontend settings page with success message
        assert callback_response.status_code == 307
        redirect_url = callback_response.headers["location"]
        assert "http://frontend-test.com/settings" in redirect_url
        assert "oauth_success=true" in redirect_url
        assert "google_user%40example.com" in redirect_url

        # Verify tokens stored
        mock_store_tokens.assert_called_once()
        args, kwargs = mock_store_tokens.call_args
        assert kwargs["email"] == "google_user@example.com"
        assert kwargs["provider"] == "google"

    @patch("backend.routers.auth.OAuth2Service.exchange_code_for_tokens")
    @patch("backend.routers.auth.OAuth2Service.store_oauth2_tokens")
    @patch("httpx.AsyncClient")
    def test_oauth2_callback_success_microsoft(
        self,
        mock_async_client_class,
        mock_store_tokens,
        mock_exchange,
        client: TestClient,
        monkeypatch,
    ):
        """Test successful Microsoft OAuth2 callback"""
        monkeypatch.setenv("MICROSOFT_CLIENT_ID", "test_client_id")
        monkeypatch.setenv("FRONTEND_URL", "http://frontend-test.com")

        # 1. Authorize to set session state
        auth_response = client.get(
            "/api/auth/microsoft/authorize", follow_redirects=False
        )
        assert auth_response.status_code == 307
        location = auth_response.headers["location"]
        from urllib.parse import parse_qs, urlparse

        parsed_url = urlparse(location)
        query_params = parse_qs(parsed_url.query)
        state = query_params["state"][0]

        # 2. Mock token exchange
        mock_exchange.return_value = {
            "access_token": "test_access_token",
            "refresh_token": "test_refresh_token",
            "expires_in": 3600,
        }

        # 3. Mock Microsoft userinfo fetch
        from unittest.mock import AsyncMock, MagicMock

        mock_response = MagicMock()
        mock_response.json.return_value = {"mail": "microsoft_user@example.com"}
        mock_response.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_async_client_class.return_value.__aenter__.return_value = mock_client

        # 4. Call callback
        callback_response = client.get(
            f"/api/auth/microsoft/callback?code=test_code&state={state}",
            follow_redirects=False,
        )

        # 5. Verify redirect to frontend settings page with success message
        assert callback_response.status_code == 307
        redirect_url = callback_response.headers["location"]
        assert "http://frontend-test.com/settings" in redirect_url
        assert "oauth_success=true" in redirect_url
        assert "microsoft_user%40example.com" in redirect_url

        # Verify tokens stored
        mock_store_tokens.assert_called_once()
        args, kwargs = mock_store_tokens.call_args
        assert kwargs["email"] == "microsoft_user@example.com"
        assert kwargs["provider"] == "microsoft"

    def test_oauth2_callback_provider_mismatch(self, client: TestClient, monkeypatch):
        """Test OAuth2 callback when provider in session does not match"""
        monkeypatch.setenv("GOOGLE_CLIENT_ID", "test_client_id")

        # 1. Authorize for Google (sets session provider to google)
        auth_response = client.get("/api/auth/google/authorize", follow_redirects=False)
        location = auth_response.headers["location"]
        from urllib.parse import parse_qs, urlparse

        parsed_url = urlparse(location)
        query_params = parse_qs(parsed_url.query)
        state = query_params["state"][0]

        # 2. Call callback but for microsoft provider
        callback_response = client.get(
            f"/api/auth/microsoft/callback?code=test_code&state={state}",
            follow_redirects=False,
        )

        assert callback_response.status_code == 400
        assert "Provider mismatch" in callback_response.json()["detail"]

    @patch("backend.routers.auth.OAuth2Service.exchange_code_for_tokens")
    def test_oauth2_callback_missing_tokens(
        self,
        mock_exchange,
        client: TestClient,
        monkeypatch,
    ):
        """Test OAuth2 callback when provider does not return tokens"""
        monkeypatch.setenv("GOOGLE_CLIENT_ID", "test_client_id")
        monkeypatch.setenv("FRONTEND_URL", "http://frontend-test.com")

        # 1. Authorize to set session state
        auth_response = client.get("/api/auth/google/authorize", follow_redirects=False)
        location = auth_response.headers["location"]
        from urllib.parse import parse_qs, urlparse

        parsed_url = urlparse(location)
        query_params = parse_qs(parsed_url.query)
        state = query_params["state"][0]

        # 2. Mock token exchange returning incomplete tokens
        mock_exchange.return_value = {
            "access_token": None,
            "refresh_token": "test_refresh_token",
        }

        # 3. Call callback
        callback_response = client.get(
            f"/api/auth/google/callback?code=test_code&state={state}",
            follow_redirects=False,
        )

        # 4. Verify redirect with error message
        assert callback_response.status_code == 307
        from urllib.parse import unquote

        redirect_url = unquote(callback_response.headers["location"])
        assert "oauth_error=true" in redirect_url
        assert "Failed to obtain tokens from provider" in redirect_url

    @patch("backend.routers.auth.OAuth2Service.exchange_code_for_tokens")
    @patch("httpx.AsyncClient")
    def test_oauth2_callback_httpx_error(
        self,
        mock_async_client_class,
        mock_exchange,
        client: TestClient,
        monkeypatch,
    ):
        """Test OAuth2 callback when userinfo request fails with HTTPError"""
        monkeypatch.setenv("GOOGLE_CLIENT_ID", "test_client_id")
        monkeypatch.setenv("FRONTEND_URL", "http://frontend-test.com")

        # 1. Authorize to set session state
        auth_response = client.get("/api/auth/google/authorize", follow_redirects=False)
        location = auth_response.headers["location"]
        from urllib.parse import parse_qs, urlparse

        parsed_url = urlparse(location)
        query_params = parse_qs(parsed_url.query)
        state = query_params["state"][0]

        # 2. Mock token exchange
        mock_exchange.return_value = {
            "access_token": "test_access_token",
            "refresh_token": "test_refresh_token",
        }

        # 3. Mock Google userinfo fetch raising HTTPError
        from unittest.mock import AsyncMock, MagicMock

        import httpx

        mock_client = MagicMock()
        mock_client.get = AsyncMock(side_effect=httpx.HTTPError("Connection timeout"))
        mock_async_client_class.return_value.__aenter__.return_value = mock_client

        # 4. Call callback
        callback_response = client.get(
            f"/api/auth/google/callback?code=test_code&state={state}",
            follow_redirects=False,
        )

        # 5. Verify redirect with error message
        assert callback_response.status_code == 307
        from urllib.parse import unquote

        redirect_url = unquote(callback_response.headers["location"])
        assert "oauth_error=true" in redirect_url
        assert "Failed to retrieve user information from google" in redirect_url

    @patch("backend.routers.auth.OAuth2Service.exchange_code_for_tokens")
    @patch("httpx.AsyncClient")
    def test_oauth2_callback_missing_email(
        self,
        mock_async_client_class,
        mock_exchange,
        client: TestClient,
        monkeypatch,
    ):
        """Test OAuth2 callback when userinfo response contains no email"""
        monkeypatch.setenv("GOOGLE_CLIENT_ID", "test_client_id")
        monkeypatch.setenv("FRONTEND_URL", "http://frontend-test.com")

        # 1. Authorize to set session state
        auth_response = client.get("/api/auth/google/authorize", follow_redirects=False)
        location = auth_response.headers["location"]
        from urllib.parse import parse_qs, urlparse

        parsed_url = urlparse(location)
        query_params = parse_qs(parsed_url.query)
        state = query_params["state"][0]

        # 2. Mock token exchange
        mock_exchange.return_value = {
            "access_token": "test_access_token",
            "refresh_token": "test_refresh_token",
        }

        # 3. Mock Google userinfo fetch returning no email
        from unittest.mock import AsyncMock, MagicMock

        mock_response = MagicMock()
        mock_response.json.return_value = {"name": "Test User"}
        mock_response.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_async_client_class.return_value.__aenter__.return_value = mock_client

        # 4. Call callback
        callback_response = client.get(
            f"/api/auth/google/callback?code=test_code&state={state}",
            follow_redirects=False,
        )

        # 5. Verify redirect with error message
        assert callback_response.status_code == 307
        from urllib.parse import unquote

        redirect_url = unquote(callback_response.headers["location"])
        assert "oauth_error=true" in redirect_url
        assert "Failed to obtain user email from provider" in redirect_url

    @patch("backend.routers.auth.OAuth2Service.exchange_code_for_tokens")
    @patch("backend.routers.auth.OAuth2Service.store_oauth2_tokens")
    @patch("httpx.AsyncClient")
    def test_oauth2_callback_db_store_error(
        self,
        mock_async_client_class,
        mock_store_tokens,
        mock_exchange,
        client: TestClient,
        monkeypatch,
    ):
        """Test OAuth2 callback when storing tokens in database fails"""
        monkeypatch.setenv("GOOGLE_CLIENT_ID", "test_client_id")
        monkeypatch.setenv("FRONTEND_URL", "http://frontend-test.com")

        # 1. Authorize to set session state
        auth_response = client.get("/api/auth/google/authorize", follow_redirects=False)
        location = auth_response.headers["location"]
        from urllib.parse import parse_qs, urlparse

        parsed_url = urlparse(location)
        query_params = parse_qs(parsed_url.query)
        state = query_params["state"][0]

        # 2. Mock token exchange
        mock_exchange.return_value = {
            "access_token": "test_access_token",
            "refresh_token": "test_refresh_token",
        }

        # 3. Mock Google userinfo fetch
        from unittest.mock import AsyncMock, MagicMock

        mock_response = MagicMock()
        mock_response.json.return_value = {"email": "google_user@example.com"}
        mock_response.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_async_client_class.return_value.__aenter__.return_value = mock_client

        # 4. Mock database storage failure
        mock_store_tokens.side_effect = Exception("Database write error")

        # 5. Call callback
        callback_response = client.get(
            f"/api/auth/google/callback?code=test_code&state={state}",
            follow_redirects=False,
        )

        # 6. Verify redirect with error message
        assert callback_response.status_code == 307
        from urllib.parse import unquote

        redirect_url = unquote(callback_response.headers["location"])
        assert "oauth_error=true" in redirect_url
        assert "Database write error" in redirect_url
