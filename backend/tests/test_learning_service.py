from unittest.mock import MagicMock, patch

import pytest
from sqlmodel import Session, SQLModel, create_engine, select

from backend.models import LearningCandidate, ManualRule, ProcessedEmail
from backend.services.learning_service import LearningService


@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def test_generate_rule_from_email():
    email = ProcessedEmail(
        sender="orders@amazon.com",
        subject="Your Amazon Order confirmation",
        email_id="msg1",
    )
    suggestion = LearningService.generate_rule_from_email(email)

    assert suggestion["email_pattern"] == "*@amazon.com"
    assert "amazon" in suggestion["purpose"]
    assert suggestion["confidence"] >= 0.7


def test_run_shadow_mode(session):
    # Setup a shadow rule
    rule = ManualRule(
        email_pattern="*@store.com", is_shadow_mode=True, confidence=0.5, match_count=0
    )
    session.add(rule)
    session.commit()

    # Simulate an email matching the shadow rule
    email_data = {"from": "support@store.com", "subject": "Thank you for visiting"}

    LearningService.run_shadow_mode(session, email_data)

    # Reload rule
    session.refresh(rule)
    assert rule.match_count == 1
    assert rule.confidence > 0.5


def test_auto_promotion(session):
    # Setup a rule ready for promotion
    rule = ManualRule(
        email_pattern="*@high-confidence.com",
        is_shadow_mode=True,
        confidence=0.95,
        match_count=5,
        purpose="Testing",
    )
    session.add(rule)
    session.commit()

    LearningService.auto_promote_rules(session)

    # Reload and check promotion
    session.refresh(rule)
    assert not rule.is_shadow_mode
    assert "(AUTO)" in rule.purpose


def test_run_shadow_mode_email_pattern_no_match(session):
    """Test that shadow rule doesn't match when email pattern doesn't match sender (line 83)."""
    # Setup a shadow rule with specific email pattern
    rule = ManualRule(
        email_pattern="*@store.com", is_shadow_mode=True, confidence=0.5, match_count=0
    )
    session.add(rule)
    session.commit()

    # Simulate an email that doesn't match the email pattern
    email_data = {"from": "support@different-store.com", "subject": "Thank you"}

    LearningService.run_shadow_mode(session, email_data)

    # Reload rule and verify it wasn't matched
    session.refresh(rule)
    assert rule.match_count == 0  # Should not increment
    assert rule.confidence == 0.5  # Should not change


def test_run_shadow_mode_subject_pattern_no_match(session):
    """Test that shadow rule doesn't match when subject pattern doesn't match (line 89)."""
    # Setup a shadow rule with both email and subject patterns
    rule = ManualRule(
        email_pattern="*@store.com",
        subject_pattern="*order*",
        is_shadow_mode=True,
        confidence=0.5,
        match_count=0,
    )
    session.add(rule)
    session.commit()

    # Simulate an email where email pattern matches but subject pattern doesn't
    email_data = {"from": "support@store.com", "subject": "Just a greeting"}

    LearningService.run_shadow_mode(session, email_data)

    # Reload rule and verify it wasn't matched
    session.refresh(rule)
    assert rule.match_count == 0  # Should not increment
    assert rule.confidence == 0.5  # Should not change


@patch("backend.services.email_service.EmailService")
def test_scan_history_no_email_accounts(mock_email_service, session):
    """Test scan_history when no email accounts are configured (lines 145-147)."""
    # Mock get_all_accounts to return empty list
    mock_email_service.get_all_accounts.return_value = []

    result = LearningService.scan_history(session, days=30)

    assert result == 0
    mock_email_service.get_all_accounts.assert_called_once()


@patch("backend.services.detector.ReceiptDetector")
@patch("backend.services.email_service.EmailService")
def test_scan_history_with_emails_already_processed(
    mock_email_service, mock_detector, session
):
    """Test scan_history when emails are already in database (lines 202-208)."""
    # Setup email accounts
    mock_email_service.get_all_accounts.return_value = [
        {"email": "test@example.com", "password": "pass123", "imap_server": "imap.gmail.com"}
    ]

    # Setup fetched emails
    email_data = {
        "message_id": "existing-msg-123",
        "subject": "Test Subject",
        "body": "Test body",
        "from": "sender@example.com",
    }
    mock_email_service.fetch_recent_emails.return_value = [email_data]

    # Add email to database (already processed)
    existing_email = ProcessedEmail(
        email_id="existing-msg-123",
        sender="sender@example.com",
        subject="Test Subject",
    )
    session.add(existing_email)
    session.commit()

    result = LearningService.scan_history(session, days=30)

    # Should return 0 since email was already processed
    assert result == 0
    mock_email_service.get_all_accounts.assert_called_once()
    mock_email_service.fetch_recent_emails.assert_called_once()


@patch("backend.services.detector.ReceiptDetector")
@patch("backend.services.email_service.EmailService")
def test_scan_history_with_receipt_detected_new_candidate(
    mock_email_service, mock_detector, session
):
    """Test scan_history when a receipt is detected and creates new candidate (lines 211-259)."""
    # Setup email accounts
    mock_email_service.get_all_accounts.return_value = [
        {"email": "test@example.com", "password": "pass123", "imap_server": "imap.gmail.com"}
    ]

    # Setup fetched emails
    email_data = {
        "message_id": "new-receipt-123",
        "subject": "Amazon Order Confirmation",
        "body": "Your order has been shipped",
        "from": "orders@amazon.com",
    }
    mock_email_service.fetch_recent_emails.return_value = [email_data]

    # Mock receipt detector to return True
    mock_detector.is_receipt.return_value = True

    result = LearningService.scan_history(session, days=30)

    # Should return 1 new candidate
    assert result == 1

    # Verify a LearningCandidate was created
    candidates = session.exec(select(LearningCandidate)).all()
    assert len(candidates) == 1
    assert candidates[0].sender == "orders@amazon.com"
    assert candidates[0].type == "Receipt"
    assert candidates[0].matches == 1


@patch("backend.services.detector.ReceiptDetector")
@patch("backend.services.email_service.EmailService")
def test_scan_history_with_receipt_detected_existing_candidate(
    mock_email_service, mock_detector, session
):
    """Test scan_history when a receipt matches existing candidate (lines 245-249)."""
    # Setup email accounts
    mock_email_service.get_all_accounts.return_value = [
        {"email": "test@example.com", "password": "pass123", "imap_server": "imap.gmail.com"}
    ]

    # Create existing candidate
    existing_candidate = LearningCandidate(
        sender="orders@amazon.com",
        subject_pattern="*amazon*",
        confidence=0.8,
        example_subject="Amazon Order",
        type="Receipt",
        matches=1,
    )
    session.add(existing_candidate)
    session.commit()

    # Setup fetched emails with same pattern
    email_data = {
        "message_id": "new-receipt-456",
        "subject": "Amazon Order Confirmation #2",
        "body": "Your order has been shipped",
        "from": "orders@amazon.com",
    }
    mock_email_service.fetch_recent_emails.return_value = [email_data]

    # Mock receipt detector to return True
    mock_detector.is_receipt.return_value = True

    result = LearningService.scan_history(session, days=30)

    # Should return 0 new candidates (existing one was updated)
    assert result == 0

    # Verify the existing candidate was updated
    session.refresh(existing_candidate)
    assert existing_candidate.matches == 2


@patch("backend.services.detector.ReceiptDetector")
@patch("backend.services.email_service.EmailService")
def test_scan_history_with_non_receipt_email(
    mock_email_service, mock_detector, session
):
    """Test scan_history when fetched email is not a receipt (lines 217-219)."""
    # Setup email accounts
    mock_email_service.get_all_accounts.return_value = [
        {"email": "test@example.com", "password": "pass123", "imap_server": "imap.gmail.com"}
    ]

    # Setup fetched emails
    email_data = {
        "message_id": "not-receipt-123",
        "subject": "Regular Email",
        "body": "Just a regular message",
        "from": "friend@example.com",
    }
    mock_email_service.fetch_recent_emails.return_value = [email_data]

    # Mock receipt detector to return False
    mock_detector.is_receipt.return_value = False

    result = LearningService.scan_history(session, days=30)

    # Should return 0 candidates (not a receipt)
    assert result == 0

    # Verify no candidates were created
    candidates = session.exec(select(LearningCandidate)).all()
    assert len(candidates) == 0


@patch("backend.services.email_service.EmailService")
def test_scan_history_with_exception_handling(mock_email_service, session):
    """Test scan_history exception handling (lines 260-263)."""
    # Setup email accounts
    mock_email_service.get_all_accounts.return_value = [
        {"email": "test@example.com", "password": "pass123", "imap_server": "imap.gmail.com"}
    ]

    # Make fetch_recent_emails raise an exception
    mock_email_service.fetch_recent_emails.side_effect = Exception("Connection error")

    # Should not raise exception, should handle it gracefully
    result = LearningService.scan_history(session, days=30)

    # Should return 0 due to exception
    assert result == 0


@patch("backend.services.detector.ReceiptDetector")
@patch("backend.services.email_service.EmailService")
def test_scan_history_multiple_accounts(
    mock_email_service, mock_detector, session
):
    """Test scan_history with multiple email accounts (lines 154-158)."""
    # Setup multiple email accounts
    mock_email_service.get_all_accounts.return_value = [
        {"email": "account1@example.com", "password": "pass1", "imap_server": "imap.gmail.com"},
        {"email": "account2@example.com", "password": "pass2", "imap_server": "imap.outlook.com"},
    ]

    # Setup fetched emails for each account
    def fetch_side_effect(*args, **kwargs):
        username = kwargs.get("username")
        if username == "account1@example.com":
            return [
                {
                    "message_id": "msg1",
                    "subject": "Amazon Receipt",
                    "body": "Order confirmed",
                    "from": "orders@amazon.com",
                }
            ]
        elif username == "account2@example.com":
            return [
                {
                    "message_id": "msg2",
                    "subject": "Uber Receipt",
                    "body": "Trip completed",
                    "from": "receipts@uber.com",
                }
            ]
        return []

    mock_email_service.fetch_recent_emails.side_effect = fetch_side_effect

    # Mock receipt detector to return True for both
    mock_detector.is_receipt.return_value = True

    result = LearningService.scan_history(session, days=30)

    # Should return 2 new candidates (one from each account)
    assert result == 2

    # Verify candidates were created
    candidates = session.exec(select(LearningCandidate)).all()
    assert len(candidates) == 2
    senders = {c.sender for c in candidates}
    assert "orders@amazon.com" in senders
    assert "receipts@uber.com" in senders
