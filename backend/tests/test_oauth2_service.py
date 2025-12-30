"""
Tests for OAuth2 service
"""

import base64
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, Mock, patch
from urllib.parse import urlparse

import pytest
from sqlmodel import Session, create_engine
from sqlmodel.pool import StaticPool

from backend.models import EmailAccount
from backend.services.oauth2_service import OAuth2Config, OAuth2Service


@pytest.fixture(name="session")
def session_fixture():
    """Create a test database session"""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    from backend.models import SQLModel

    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


class TestOAuth2Config:
    """Tests for OAuth2Config class"""

    def test_get_google_config(self):
        """Test getting Google OAuth2 configuration"""
        config = OAuth2Config.get_config("google")
        assert config is not None
        assert config["authorization_endpoint"]
        assert config["token_endpoint"]
        assert config["scopes"]
        assert "https://mail.google.com/" in config["scopes"]

    def test_get_microsoft_config(self):
        """Test getting Microsoft OAuth2 configuration"""
        config = OAuth2Config.get_config("microsoft")
        assert config is not None
        assert config["authorization_endpoint"]
        assert config["token_endpoint"]
        assert config["scopes"]

    def test_get_invalid_provider(self):
        """Test getting configuration for invalid provider"""
        config = OAuth2Config.get_config("invalid")
        assert config is None


class TestOAuth2Service:
    """Tests for OAuth2Service class"""

    def test_get_authorization_url_google(self, monkeypatch):
        """Test generating Google authorization URL"""
        monkeypatch.setenv("GOOGLE_CLIENT_ID", "test_client_id")

        url = OAuth2Service.get_authorization_url(
            "google", "http://localhost/callback", "test_state"
        )

        parsed = urlparse(url)
        assert parsed.hostname == "accounts.google.com"
        assert "test_client_id" in url
        assert "test_state" in url
        # URL-encoded callback
        assert "localhost%2Fcallback" in url or "localhost/callback" in url

    def test_get_authorization_url_no_client_id(self):
        """Test generating authorization URL without client ID"""
        with pytest.raises(ValueError, match="not configured"):
            OAuth2Service.get_authorization_url(
                "google", "http://localhost/callback", "test_state"
            )

    def test_get_authorization_url_invalid_provider(self):
        """Test generating authorization URL for invalid provider"""
        with pytest.raises(ValueError, match="Unsupported"):
            OAuth2Service.get_authorization_url(
                "invalid", "http://localhost/callback", "test_state"
            )

    def test_exchange_code_for_tokens(self, monkeypatch):
        """Test exchanging authorization code for tokens"""
        import asyncio

        monkeypatch.setenv("GOOGLE_CLIENT_ID", "test_client_id")
        monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "test_client_secret")

        mock_response = Mock()
        mock_response.json.return_value = {
            "access_token": "test_access_token",
            "refresh_token": "test_refresh_token",
            "expires_in": 3600,
        }
        mock_response.raise_for_status = Mock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            result = asyncio.run(
                OAuth2Service.exchange_code_for_tokens(
                    "google", "test_code", "http://localhost/callback"
                )
            )

            assert result["access_token"] == "test_access_token"
            assert result["refresh_token"] == "test_refresh_token"
            assert result["expires_in"] == 3600

    def test_refresh_access_token(self, monkeypatch):
        """Test refreshing an access token"""
        import asyncio

        monkeypatch.setenv("GOOGLE_CLIENT_ID", "test_client_id")
        monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "test_client_secret")

        mock_response = Mock()
        mock_response.json.return_value = {
            "access_token": "new_access_token",
            "expires_in": 3600,
        }
        mock_response.raise_for_status = Mock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            result = asyncio.run(
                OAuth2Service.refresh_access_token("google", "test_refresh_token")
            )

            assert result["access_token"] == "new_access_token"
            assert result["expires_in"] == 3600

    def test_store_oauth2_tokens_new_account(self, session: Session, monkeypatch):
        """Test storing OAuth2 tokens for a new account"""
        monkeypatch.setenv("SECRET_KEY", "test_secret_key_12345")

        account = OAuth2Service.store_oauth2_tokens(
            session=session,
            email="test@gmail.com",
            provider="google",
            access_token="test_access_token",
            refresh_token="test_refresh_token",
            expires_in=3600,
        )

        assert account.email == "test@gmail.com"
        assert account.auth_method == "oauth2"
        assert account.provider == "google"
        assert account.encrypted_access_token is not None
        assert account.encrypted_refresh_token is not None
        assert account.token_expires_at is not None
        assert account.host == "imap.gmail.com"
        assert account.port == 993

    def test_store_oauth2_tokens_existing_account(self, session: Session, monkeypatch):
        """Test storing OAuth2 tokens for an existing account"""
        monkeypatch.setenv("SECRET_KEY", "test_secret_key_12345")

        # Create initial account
        OAuth2Service.store_oauth2_tokens(
            session=session,
            email="test@gmail.com",
            provider="google",
            access_token="old_token",
            refresh_token="old_refresh",
            expires_in=3600,
        )

        # Update with new tokens
        account = OAuth2Service.store_oauth2_tokens(
            session=session,
            email="test@gmail.com",
            provider="google",
            access_token="new_token",
            refresh_token="new_refresh",
            expires_in=7200,
        )

        assert account.email == "test@gmail.com"
        assert account.auth_method == "oauth2"

    def test_ensure_valid_token_not_expired(self, session: Session, monkeypatch):
        """Test ensuring valid token when token is not expired"""
        import asyncio

        monkeypatch.setenv("SECRET_KEY", "test_secret_key_12345")

        # Create account with valid token
        account = OAuth2Service.store_oauth2_tokens(
            session=session,
            email="test@gmail.com",
            provider="google",
            access_token="valid_token",
            refresh_token="refresh_token",
            expires_in=3600,
        )

        # Token should not be refreshed
        token = asyncio.run(OAuth2Service.ensure_valid_token(session, account))
        assert token == "valid_token"

    def test_ensure_valid_token_expired(self, session: Session, monkeypatch):
        """Test ensuring valid token when token is expired"""
        import asyncio

        monkeypatch.setenv("SECRET_KEY", "test_secret_key_12345")
        monkeypatch.setenv("GOOGLE_CLIENT_ID", "test_client_id")
        monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "test_client_secret")

        # Create account with expired token
        account = OAuth2Service.store_oauth2_tokens(
            session=session,
            email="test@gmail.com",
            provider="google",
            access_token="old_token",
            refresh_token="refresh_token",
            expires_in=1,  # Expires in 1 second
        )

        # Manually set token to expired
        account.token_expires_at = datetime.now(timezone.utc) - timedelta(minutes=5)
        session.add(account)
        session.commit()

        # Mock refresh response
        mock_response = Mock()
        mock_response.json.return_value = {
            "access_token": "new_token",
            "expires_in": 3600,
        }
        mock_response.raise_for_status = Mock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            # Token should be refreshed
            token = asyncio.run(OAuth2Service.ensure_valid_token(session, account))
            assert token == "new_token"

    def test_ensure_valid_token_not_oauth2(self, session: Session, monkeypatch):
        """Test ensuring valid token for non-OAuth2 account"""
        monkeypatch.setenv("SECRET_KEY", "test_secret_key_12345")

        from backend.services.encryption_service import EncryptionService

        # Create password-based account
        account = EmailAccount(
            email="test@example.com",
            host="imap.gmail.com",
            port=993,
            username="test@example.com",
            encrypted_password=EncryptionService.encrypt("password"),
            auth_method="password",
        )
        session.add(account)
        session.commit()

        # Should raise ValueError
        import asyncio

        with pytest.raises(ValueError, match="does not use OAuth2"):
            asyncio.run(OAuth2Service.ensure_valid_token(session, account))

    def test_generate_xoauth2_string(self):
        """Test generating XOAUTH2 authentication string"""
        auth_string = OAuth2Service.generate_xoauth2_string(
            "test@example.com", "test_token"
        )

        # Decode and verify
        decoded = base64.b64decode(auth_string).decode()
        assert "user=test@example.com" in decoded
        assert "auth=Bearer test_token" in decoded
