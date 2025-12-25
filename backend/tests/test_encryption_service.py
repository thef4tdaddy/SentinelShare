import pytest
from backend.services.encryption_service import EncryptionService


class TestEncryptionService:
    """Tests for the EncryptionService"""

    def test_encrypt_decrypt(self, monkeypatch):
        """Test basic encrypt and decrypt"""
        monkeypatch.setenv("SECRET_KEY", "test-secret-key-for-testing")

        plaintext = "my-password-123"
        encrypted = EncryptionService.encrypt(plaintext)

        # Encrypted text should be different from plaintext
        assert encrypted != plaintext
        assert len(encrypted) > 0

        # Decrypt should return original text
        decrypted = EncryptionService.decrypt(encrypted)
        assert decrypted == plaintext

    def test_encrypt_empty_string_raises_error(self, monkeypatch):
        """Test that encrypting empty string raises ValueError"""
        monkeypatch.setenv("SECRET_KEY", "test-secret-key-for-testing")

        with pytest.raises(ValueError):
            EncryptionService.encrypt("")

    def test_decrypt_invalid_text_raises_error(self, monkeypatch):
        """Test that decrypting invalid text raises ValueError"""
        monkeypatch.setenv("SECRET_KEY", "test-secret-key-for-testing")

        with pytest.raises(ValueError):
            EncryptionService.decrypt("invalid-encrypted-text")

    def test_decrypt_empty_string_returns_none(self, monkeypatch):
        """Test that decrypting empty string returns None"""
        monkeypatch.setenv("SECRET_KEY", "test-secret-key-for-testing")

        result = EncryptionService.decrypt("")
        assert result is None

    def test_encryption_with_different_keys(self, monkeypatch):
        """Test that different keys produce different encrypted values"""
        plaintext = "my-password"

        monkeypatch.setenv("SECRET_KEY", "key1")
        encrypted1 = EncryptionService.encrypt(plaintext)

        monkeypatch.setenv("SECRET_KEY", "key2")
        encrypted2 = EncryptionService.encrypt(plaintext)

        # Different keys should produce different encrypted values
        assert encrypted1 != encrypted2

    def test_missing_secret_key_raises_error(self, monkeypatch):
        """Test that missing SECRET_KEY raises ValueError"""
        monkeypatch.delenv("SECRET_KEY", raising=False)

        with pytest.raises(ValueError, match="SECRET_KEY environment variable is required"):
            EncryptionService.encrypt("test")

    def test_encrypt_special_characters(self, monkeypatch):
        """Test encrypting passwords with special characters"""
        monkeypatch.setenv("SECRET_KEY", "test-secret-key-for-testing")

        plaintext = "P@ssw0rd!#$%^&*()_+-=[]{}|;:',.<>?/"
        encrypted = EncryptionService.encrypt(plaintext)
        decrypted = EncryptionService.decrypt(encrypted)

        assert decrypted == plaintext

    def test_encrypt_unicode_characters(self, monkeypatch):
        """Test encrypting passwords with unicode characters"""
        monkeypatch.setenv("SECRET_KEY", "test-secret-key-for-testing")

        plaintext = "пароль密码🔒"
        encrypted = EncryptionService.encrypt(plaintext)
        decrypted = EncryptionService.decrypt(encrypted)

        assert decrypted == plaintext
