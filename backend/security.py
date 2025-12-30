import hashlib
import hmac
import os
from datetime import datetime, timezone
from typing import Optional

import bleach
from cryptography.fernet import Fernet


def get_fernet() -> Fernet:
    """Initialize Fernet with the SECRET_KEY from environment."""
    key = os.getenv("SECRET_KEY")
    if not key:
        raise ValueError(
            "SECRET_KEY environment variable is not set. Required for email encryption."
        )

    return Fernet(key.encode())


def encrypt_content(content: str) -> str:
    """Encrypt content using Fernet."""
    if not content:
        return ""
    f = get_fernet()
    return f.encrypt(content.encode()).decode()


def decrypt_content(encrypted_content: str) -> str:
    """Decrypt content using Fernet."""
    if not encrypted_content:
        return ""
    f = get_fernet()
    try:
        from cryptography.fernet import InvalidToken

        return f.decrypt(encrypted_content.encode()).decode()
    except (InvalidToken, ValueError) as e:
        print(f"Error decrypting content: {e}")
        return ""
    except Exception as e:
        # Fallback for unexpected errors but log them
        print(f"Unexpected error decrypting content: {e}")
        return ""


def get_email_content_hash(email_data):
    """
    Generates a hash of the email content to detect duplicates when Message-ID is missing.
    Uses Sender + Subject + Normalized Body.
    """
    sender = (email_data.get("from") or "").lower().strip()
    subject = (email_data.get("subject") or "").lower().strip()

    # Normalize body by removing HTML tags and excessive whitespace
    raw_body = email_data.get("body") or email_data.get("html_body") or ""
    clean_body = bleach.clean(raw_body, tags=[], strip=True)
    normalized_body = " ".join(clean_body.split()).lower()

    content = f"{sender}|{subject}|{normalized_body}"
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def generate_hmac_signature(msg: str) -> str:
    """Generate an HMAC-SHA256 signature for a message."""
    secret = os.getenv("SECRET_KEY", "default-insecure-secret-please-change")
    return hmac.new(secret.encode(), msg.encode(), hashlib.sha256).hexdigest()


def generate_dashboard_token(email: str) -> str:
    """Generate a secure token for the sendee dashboard."""
    ts = str(int(datetime.now(timezone.utc).timestamp()))
    msg = f"dashboard:{email}:{ts}"
    sig = generate_hmac_signature(msg)
    return f"{email}:{ts}:{sig}"


def verify_dashboard_token(token: str) -> Optional[str]:
    """Verify a dashboard token and return the email if valid."""
    try:
        email, ts, sig = token.split(":")
        msg = f"dashboard:{email}:{ts}"
        expected = generate_hmac_signature(msg)

        if not hmac.compare_digest(expected, sig):
            return None

        # Check expiration (e.g., 30 days for dashboard access)
        link_ts = float(ts)
        now_ts = datetime.now(timezone.utc).timestamp()
        if now_ts - link_ts > 30 * 24 * 3600:
            return None

        return email
    except Exception:
        return None


def sanitize_csv_field(field: str) -> str:
    """Sanitize field to prevent CSV injection attacks.

    Fields starting with =, +, -, @ or tab could be interpreted as formulas.
    Prefix them with a single quote to treat them as text.
    """
    if not field:
        return field

    dangerous_chars = ("=", "+", "-", "@", "\t", "\r")
    if field.startswith(dangerous_chars):
        return "'" + field
    return field
