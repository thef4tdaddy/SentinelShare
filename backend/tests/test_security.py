import pytest
from backend.security import decrypt_content, encrypt_content, get_fernet
from cryptography.fernet import Fernet


def test_encryption_decryption():
    content = "Hello, secret world!"
    encrypted = encrypt_content(content)
    assert encrypted != content
    assert isinstance(encrypted, str)

    decrypted = decrypt_content(encrypted)
    assert decrypted == content


def test_encrypt_empty_content():
    assert encrypt_content("") == ""
    assert encrypt_content(None) == ""


def test_decrypt_empty_content():
    assert decrypt_content("") == ""
    assert decrypt_content(None) == ""


def test_decryption_failure():
    invalid_content = "not_a_valid_fernet_token"
    # Should catch exception and return empty string as per implementation
    assert decrypt_content(invalid_content) == ""


def test_get_fernet_missing_key(monkeypatch):
    monkeypatch.delenv("SECRET_KEY", raising=False)
    with pytest.raises(ValueError, match="SECRET_KEY environment variable is not set"):
        get_fernet()


def test_get_fernet_valid_key():
    f = get_fernet()
    assert isinstance(f, Fernet)
