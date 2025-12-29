from backend.security import (generate_dashboard_token, generate_hmac_signature,
                              get_email_content_hash, verify_dashboard_token)


def test_get_email_content_hash_consistency():
    """Test that hashing the same content results in the same hash."""
    email_data = {
        "from": "sender@example.com",
        "subject": "Test Receipt",
        "body": "Hello world",
    }
    hash1 = get_email_content_hash(email_data)
    hash2 = get_email_content_hash(email_data)
    assert hash1 == hash2
    assert len(hash1) == 64  # SHA-256


def test_get_email_content_hash_normalization():
    """Test that hashing is resilient to whitespace and case in sender/subject."""
    email_data1 = {
        "from": " SENDER@example.com ",
        "subject": " TEST Receipt  ",
        "body": "Hello world",
    }
    email_data2 = {
        "from": "sender@example.com",
        "subject": "test receipt",
        "body": "Hello world",
    }
    assert get_email_content_hash(email_data1) == get_email_content_hash(email_data2)


def test_dashboard_token_verification_success():
    """Test that a generated token is verified correctly."""
    email = "test@example.com"
    token = generate_dashboard_token(email)
    verified_email = verify_dashboard_token(token)
    assert verified_email == email


def test_dashboard_token_verification_failure():
    """Test that tampered tokens or invalid formats fail verification."""
    email = "test@example.com"
    token = generate_dashboard_token(email)

    # Tamper with the email part
    parts = token.split(":")
    tampered_token = f"other@example.com:{parts[1]}:{parts[2]}"
    assert verify_dashboard_token(tampered_token) is None

    # Invalid format
    assert verify_dashboard_token("invalid-token") is None


def test_dashboard_token_case_sensitivity():
    """Test that tokens are verified with exact match (usually emails are normalized)."""
    email = "User@Example.Com"
    token = generate_dashboard_token(email)
    # verify_dashboard_token should return the original string if sig matches
    assert verify_dashboard_token(token) == email


def test_dashboard_token_expiration():
    """Test that tokens older than 30 days are rejected."""
    email = "test@example.com"
    # Create a token with a timestamp from 31 days ago (30 days * 24 hours * 3600 seconds + 1 second)
    old_timestamp = str(int(1234567890))  # This is an old timestamp from 2009
    msg = f"dashboard:{email}:{old_timestamp}"
    sig = generate_hmac_signature(msg)
    expired_token = f"{email}:{old_timestamp}:{sig}"
    # Verify that the expired token is rejected
    assert verify_dashboard_token(expired_token) is None
