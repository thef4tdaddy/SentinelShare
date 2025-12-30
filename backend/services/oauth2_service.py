"""
OAuth2 service for managing OAuth2 authentication flows and token management.
Supports Google and Microsoft OAuth2 providers.
"""

import base64
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Optional
from urllib.parse import urlencode

import httpx
from sqlmodel import Session, select

from backend.models import EmailAccount
from backend.services.encryption_service import EncryptionService

logger = logging.getLogger(__name__)


class OAuth2Config:
    """Configuration for OAuth2 providers"""

    GOOGLE = {
        "authorization_endpoint": "https://accounts.google.com/o/oauth2/v2/auth",
        "token_endpoint": "https://oauth2.googleapis.com/token",
        "scopes": ["https://mail.google.com/"],
        "client_id_env": "GOOGLE_CLIENT_ID",
        "client_secret_env": "GOOGLE_CLIENT_SECRET",
    }

    MICROSOFT = {
        "authorization_endpoint": "https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
        "token_endpoint": "https://login.microsoftonline.com/common/oauth2/v2.0/token",
        "scopes": [
            "https://outlook.office.com/IMAP.AccessAsUser.All",
            "offline_access",
        ],
        "client_id_env": "MICROSOFT_CLIENT_ID",
        "client_secret_env": "MICROSOFT_CLIENT_SECRET",
    }

    @classmethod
    def get_config(cls, provider: str) -> Optional[dict]:
        """Get OAuth2 configuration for a provider"""
        provider = provider.lower()
        if provider == "google":
            return cls.GOOGLE
        elif provider == "microsoft":
            return cls.MICROSOFT
        return None


class OAuth2Service:
    """Service for managing OAuth2 authentication flows"""

    @staticmethod
    def get_authorization_url(provider: str, redirect_uri: str, state: str) -> str:
        """
        Generate the OAuth2 authorization URL for a provider.

        Args:
            provider: OAuth2 provider name ("google" or "microsoft")
            redirect_uri: The callback URI to redirect to after authorization
            state: A random state string for CSRF protection

        Returns:
            The authorization URL to redirect the user to

        Raises:
            ValueError: If provider is not supported or credentials are not configured
        """
        config = OAuth2Config.get_config(provider)
        if not config:
            raise ValueError(f"Unsupported OAuth2 provider: {provider}")

        client_id = os.environ.get(config["client_id_env"])
        if not client_id:
            raise ValueError(
                f"OAuth2 client ID not configured for {provider}. "
                f"Set {config['client_id_env']} environment variable."
            )

        params = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": " ".join(config["scopes"]),
            "state": state,
            "access_type": "offline",  # Request refresh token
            "prompt": "consent",  # Force consent screen to get refresh token
        }

        return f"{config['authorization_endpoint']}?{urlencode(params)}"

    @staticmethod
    async def exchange_code_for_tokens(
        provider: str, code: str, redirect_uri: str
    ) -> dict:
        """
        Exchange authorization code for access and refresh tokens.

        Args:
            provider: OAuth2 provider name
            code: Authorization code from OAuth callback
            redirect_uri: The redirect URI used in the authorization request

        Returns:
            Dictionary containing access_token, refresh_token, expires_in, etc.

        Raises:
            ValueError: If provider is not supported or exchange fails
        """
        config = OAuth2Config.get_config(provider)
        if not config:
            raise ValueError(f"Unsupported OAuth2 provider: {provider}")

        client_id = os.environ.get(config["client_id_env"])
        client_secret = os.environ.get(config["client_secret_env"])

        if not client_id or not client_secret:
            raise ValueError(f"OAuth2 credentials not configured for {provider}")

        data = {
            "client_id": client_id,
            "client_secret": client_secret,
            "code": code,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(config["token_endpoint"], data=data)
            response.raise_for_status()
            return response.json()

    @staticmethod
    async def refresh_access_token(provider: str, refresh_token: str) -> dict:
        """
        Refresh an expired access token using a refresh token.

        Args:
            provider: OAuth2 provider name
            refresh_token: The refresh token

        Returns:
            Dictionary containing new access_token and expires_in

        Raises:
            ValueError: If provider is not supported or refresh fails
        """
        config = OAuth2Config.get_config(provider)
        if not config:
            raise ValueError(f"Unsupported OAuth2 provider: {provider}")

        client_id = os.environ.get(config["client_id_env"])
        client_secret = os.environ.get(config["client_secret_env"])

        if not client_id or not client_secret:
            raise ValueError(f"OAuth2 credentials not configured for {provider}")

        data = {
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(config["token_endpoint"], data=data)
            response.raise_for_status()
            return response.json()

    @staticmethod
    def store_oauth2_tokens(
        session: Session,
        email: str,
        provider: str,
        access_token: str,
        refresh_token: str,
        expires_in: int,
        username: Optional[str] = None,
        host: Optional[str] = None,
        port: Optional[int] = None,
    ) -> EmailAccount:
        """
        Store OAuth2 tokens in the database for an email account.

        Args:
            session: Database session
            email: Email address
            provider: OAuth2 provider name
            access_token: OAuth2 access token
            refresh_token: OAuth2 refresh token
            expires_in: Token expiry time in seconds
            username: IMAP username (defaults to email)
            host: IMAP host (defaults based on provider)
            port: IMAP port (defaults to 993)

        Returns:
            The created or updated EmailAccount

        Raises:
            Exception: If encryption fails
        """
        # Normalize email to lowercase
        normalized_email = email.lower()

        # Set defaults based on provider
        if not host:
            if provider == "google":
                host = "imap.gmail.com"
            elif provider == "microsoft":
                host = "outlook.office365.com"
            else:
                host = "imap.gmail.com"  # Default fallback

        if not port:
            port = 993

        if not username:
            username = normalized_email

        # Calculate token expiry
        token_expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)

        # Encrypt tokens
        encrypted_access_token = EncryptionService.encrypt(access_token)
        encrypted_refresh_token = EncryptionService.encrypt(refresh_token)

        # Check if account exists
        existing = session.exec(
            select(EmailAccount).where(EmailAccount.email == normalized_email)
        ).first()

        if existing:
            # Update existing account
            existing.auth_method = "oauth2"
            existing.provider = provider
            existing.encrypted_access_token = encrypted_access_token
            existing.encrypted_refresh_token = encrypted_refresh_token
            existing.token_expires_at = token_expires_at
            existing.host = host
            existing.port = port
            existing.username = username
            existing.is_active = True
            existing.updated_at = datetime.now(timezone.utc)
            session.add(existing)
            session.commit()
            session.refresh(existing)
            return existing
        else:
            # Create new account
            new_account = EmailAccount(
                email=normalized_email,
                host=host,
                port=port,
                username=username,
                encrypted_password=None,  # No password for OAuth2
                auth_method="oauth2",
                provider=provider,
                encrypted_access_token=encrypted_access_token,
                encrypted_refresh_token=encrypted_refresh_token,
                token_expires_at=token_expires_at,
                is_active=True,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            session.add(new_account)
            session.commit()
            session.refresh(new_account)
            return new_account

    @staticmethod
    async def ensure_valid_token(
        session: Session, account: EmailAccount
    ) -> Optional[str]:
        """
        Ensure the account has a valid access token, refreshing if necessary.

        Args:
            session: Database session
            account: EmailAccount to check

        Returns:
            Valid access token, or None if refresh fails

        Raises:
            ValueError: If account doesn't use OAuth2 or tokens are missing
        """
        if account.auth_method != "oauth2":
            raise ValueError("Account does not use OAuth2 authentication")

        if not account.encrypted_refresh_token:
            raise ValueError("No refresh token available for account")

        # Check if token is expired or will expire in the next 5 minutes
        now = datetime.now(timezone.utc)
        buffer = timedelta(minutes=5)

        # Make token_expires_at timezone-aware if it isn't
        token_expiry = account.token_expires_at
        if token_expiry and token_expiry.tzinfo is None:
            token_expiry = token_expiry.replace(tzinfo=timezone.utc)

        if token_expiry and token_expiry > (now + buffer):
            # Token is still valid
            if account.encrypted_access_token:
                return EncryptionService.decrypt(account.encrypted_access_token)
            return None

        # Token is expired or about to expire, refresh it
        logger.info(f"Refreshing OAuth2 token for account {account.email}")

        try:
            refresh_token = EncryptionService.decrypt(account.encrypted_refresh_token)
            if not refresh_token:
                raise ValueError("Failed to decrypt refresh token")

            if not account.provider:
                raise ValueError("Account provider not set")

            token_data = await OAuth2Service.refresh_access_token(
                account.provider, refresh_token
            )

            # Update account with new tokens
            new_access_token = token_data.get("access_token")
            if not new_access_token:
                raise ValueError("No access token in refresh response")

            new_refresh_token = token_data.get(
                "refresh_token", refresh_token
            )  # Some providers don't return new refresh token
            expires_in = token_data.get("expires_in", 3600)

            account.encrypted_access_token = EncryptionService.encrypt(new_access_token)
            if new_refresh_token != refresh_token:
                account.encrypted_refresh_token = EncryptionService.encrypt(
                    new_refresh_token
                )
            account.token_expires_at = now + timedelta(seconds=expires_in)
            account.updated_at = now

            session.add(account)
            session.commit()
            session.refresh(account)

            logger.info(f"Successfully refreshed token for {account.email}")
            return new_access_token

        except Exception as e:
            logger.error(f"Failed to refresh token for {account.email}: {e}")
            raise

    @staticmethod
    def generate_xoauth2_string(email: str, access_token: str) -> str:
        """
        Generate XOAUTH2 authentication string for IMAP.

        Args:
            email: User's email address
            access_token: OAuth2 access token

        Returns:
            Base64-encoded XOAUTH2 authentication string
        """
        auth_string = f"user={email}\x01auth=Bearer {access_token}\x01\x01"
        return base64.b64encode(auth_string.encode()).decode()
