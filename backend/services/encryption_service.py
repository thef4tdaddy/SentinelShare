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
        Consistently uses SHA256-based key derivation to ensure compatibility.
        """
        secret_key = os.environ.get("SECRET_KEY")
        if not secret_key:
            raise ValueError(
                "SECRET_KEY environment variable is required for encryption"
            )

        # Always use hash-based derivation for consistency
        # This ensures the same plaintext encrypts the same way regardless of SECRET_KEY format
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
            
        Raises:
            ValueError: If the encrypted text is invalid or key has changed
        """
        if not encrypted_text:
            return None

        try:
            fernet = EncryptionService._get_fernet()
            decrypted_bytes = fernet.decrypt(encrypted_text.encode())
            return decrypted_bytes.decode()
        except Exception as e:
            # Log the error with details for debugging
            import logging

            logging.error(f"Failed to decrypt data: {type(e).__name__}")
            # Raise a more specific error for callers to handle
            raise ValueError("Decryption failed - key may have changed or data is corrupted")
