import os
from typing import Optional

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
        return f.decrypt(encrypted_content.encode()).decode()
    except Exception as e:
        print(f"Error decrypting content: {e}")
        return ""
