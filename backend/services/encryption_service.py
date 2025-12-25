import os
from cryptography.fernet import Fernet
from typing import Optional


class EncryptionService:
    """
    Service for encrypting and decrypting sensitive data using Fernet symmetric encryption.
    Uses the SECRET_KEY from environment variables as the encryption key.
    """

    @staticmethod
    def _get_fernet() -> Fernet:
        """
        Get or create a Fernet instance using the SECRET_KEY.
        The SECRET_KEY must be a valid Fernet key (32 url-safe base64-encoded bytes).
        """
        secret_key = os.environ.get("SECRET_KEY")
        if not secret_key:
            raise ValueError(
                "SECRET_KEY environment variable is required for encryption"
            )

        # Convert the secret key to bytes and ensure it's the right format
        # Fernet keys must be 32 url-safe base64-encoded bytes
        try:
            # Try to use it directly first
            return Fernet(secret_key.encode())
        except Exception:
            # If that fails, generate a proper key from the secret
            # This ensures backward compatibility with non-Fernet keys
            import hashlib
            import base64

            # Hash the secret to get consistent 32 bytes
            key_bytes = hashlib.sha256(secret_key.encode()).digest()
            # Encode as base64 for Fernet
            fernet_key = base64.urlsafe_b64encode(key_bytes)
            return Fernet(fernet_key)

    @staticmethod
    def encrypt(plaintext: str) -> str:
        """
        Encrypt a plaintext string.

        Args:
            plaintext: The string to encrypt

        Returns:
            The encrypted string as a base64-encoded string
        """
        if not plaintext:
            raise ValueError("Cannot encrypt empty string")

        fernet = EncryptionService._get_fernet()
        encrypted_bytes = fernet.encrypt(plaintext.encode())
        return encrypted_bytes.decode()

    @staticmethod
    def decrypt(encrypted_text: str) -> Optional[str]:
        """
        Decrypt an encrypted string.

        Args:
            encrypted_text: The encrypted string (base64-encoded)

        Returns:
            The decrypted plaintext string, or None if decryption fails
        """
        if not encrypted_text:
            return None

        try:
            fernet = EncryptionService._get_fernet()
            decrypted_bytes = fernet.decrypt(encrypted_text.encode())
            return decrypted_bytes.decode()
        except Exception:
            # Log the error but don't expose details
            import logging

            logging.error("Failed to decrypt data - key may have changed")
            return None
