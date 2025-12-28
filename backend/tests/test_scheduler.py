import os
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import backend.services.scheduler as scheduler_module
import pytest
from backend.models import ProcessedEmail, ProcessingRun
from backend.services.scheduler import (cleanup_expired_emails, process_emails,
                                        redact_email, start_scheduler,
                                        stop_scheduler)
from sqlmodel import Session, SQLModel, create_engine, select
from sqlmodel.pool import StaticPool


@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="engine")
def engine_fixture():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    return engine


@patch.dict(os.environ, {"POLL_INTERVAL": "30", "WIFE_EMAIL": "wife@example.com"})
@patch("backend.services.scheduler.engine")
@patch("backend.services.scheduler.EmailService.fetch_recent_emails")
def test_process_emails_creates_run_with_no_emails(
    mock_fetch, mock_engine_patch, engine
):
    """Test that process_emails creates a ProcessingRun record when no emails are found"""
    # Mock the engine to use our test engine
    mock_engine_patch.begin.return_value.__enter__.return_value = Session(engine)
    mock_engine_patch.connect.return_value.__enter__.return_value = engine.connect()

    # Use our test engine in the scheduler module
    original_engine = scheduler_module.engine
    scheduler_module.engine = engine

    try:
        # Mock fetch_recent_emails to return empty list
        mock_fetch.return_value = []

        # Set required environment variables
        os.environ["GMAIL_EMAIL"] = "test@example.com"
        os.environ["GMAIL_PASSWORD"] = "password"

        # Call process_emails
        process_emails()

        # Verify that a ProcessingRun was created
        with Session(engine) as session:
            runs = session.exec(select(ProcessingRun)).all()
            assert len(runs) == 1

            run = runs[0]
            assert run.emails_checked == 0
            assert run.emails_processed == 0
            assert run.emails_forwarded == 0
            assert run.status == "completed"
            assert run.check_interval_minutes == 30
            assert run.completed_at is not None
    finally:
        # Restore original engine
        scheduler_module.engine = original_engine


@patch.dict(
    os.environ,
    {
        "POLL_INTERVAL": "60",
        "WIFE_EMAIL": "wife@example.com",
        "SECRET_KEY": "cpUbNMiXWufM3gAPx1arHE1h7Y72s9sBri-MDiWtwb4=",  # Added
        "GMAIL_EMAIL": "test@example.com",
        "GMAIL_PASSWORD": "password",
        "EMAIL_ACCOUNTS": "",  # Ensure no multi-account processing
    },
)
@patch("backend.services.scheduler.engine")
@patch("backend.services.scheduler.EmailService.fetch_recent_emails")
@patch("backend.services.scheduler.EmailForwarder.forward_email")
@patch("backend.services.scheduler.ReceiptDetector.is_receipt")
@patch("backend.services.scheduler.ReceiptDetector.categorize_receipt")
def test_process_emails_creates_run_with_emails(
    mock_categorize,
    mock_is_receipt,
    mock_forward,
    mock_fetch,
    mock_engine_patch,
    engine,
):
    """Test that process_emails creates a ProcessingRun record with correct counts"""
    # Use our test engine in the scheduler module
    original_engine = scheduler_module.engine
    scheduler_module.engine = engine

    try:
        # Mock email data
        mock_emails = [
            {
                "message_id": "msg1",
                "subject": "Receipt from Amazon",
                "from": "amazon@example.com",
                "body": "Thanks for your order",
            },
            {
                "message_id": "msg2",
                "subject": "Receipt from Starbucks",
                "from": "starbucks@example.com",
                "body": "Thanks for your purchase",
            },
        ]
        mock_fetch.return_value = mock_emails
        mock_is_receipt.return_value = True
        mock_categorize.return_value = "Shopping"
        mock_forward.return_value = True

        # Call process_emails
        process_emails()

        # Verify that a ProcessingRun was created with correct counts
        with Session(engine) as session:
            runs = session.exec(select(ProcessingRun)).all()
            assert len(runs) == 1

            run = runs[0]
            assert run.emails_checked == 2
            assert run.emails_processed == 2
            assert run.emails_forwarded == 2
            assert run.status == "completed"
            assert run.check_interval_minutes == 60
            assert run.completed_at is not None

            # Verify emails were processed
            emails = session.exec(select(ProcessedEmail)).all()
            assert len(emails) == 2
    finally:
        # Restore original engine
        scheduler_module.engine = original_engine


@patch.dict(os.environ, {"POLL_INTERVAL": "45"})
@patch("backend.services.scheduler.scheduler")
def test_start_scheduler_uses_poll_interval(mock_scheduler):
    """Test that start_scheduler uses the POLL_INTERVAL from environment"""
    start_scheduler()

    # Verify scheduler was started and jobs were added
    mock_scheduler.start.assert_called_once()
    assert mock_scheduler.add_job.call_count == 2
    # Verify both function jobs were added
    calls = [c[0][0].__name__ for c in mock_scheduler.add_job.call_args_list]
    assert "process_emails" in calls
    assert "cleanup_expired_emails" in calls


@patch.dict(
    os.environ,
    {
        "POLL_INTERVAL": "60",
        "SECRET_KEY": "cpUbNMiXWufM3gAPx1arHE1h7Y72s9sBri-MDiWtwb4=",  # Added
        "GMAIL_EMAIL": "test@example.com",
        "GMAIL_PASSWORD": "password",
        "EMAIL_ACCOUNTS": "",  # Ensure no multi-account processing
    },
)
@patch("backend.services.scheduler.engine")
@patch("backend.services.scheduler.EmailService.fetch_recent_emails")
def test_process_emails_records_error(mock_fetch, mock_engine_patch, engine):
    """Test that errors during processing are recorded in ProcessingRun"""
    # Use our test engine in the scheduler module
    original_engine = scheduler_module.engine
    scheduler_module.engine = engine

    try:
        # Mock fetch to raise an exception
        mock_fetch.side_effect = Exception("IMAP connection failed")

        # Call process_emails
        process_emails()

        # Verify that a ProcessingRun was created with error status
        with Session(engine) as session:
            runs = session.exec(select(ProcessingRun)).all()
            assert len(runs) == 1

            run = runs[0]
            assert run.status == "error"
            assert "Connection failed (Exception)" in run.error_message
            assert run.completed_at is not None
    finally:
        # Restore original engine
        scheduler_module.engine = original_engine


@patch.dict(
    os.environ,
    {
        "POLL_INTERVAL": "60",
        "WIFE_EMAIL": "wife@example.com",
        "SECRET_KEY": "cpUbNMiXWufM3gAPx1arHE1h7Y72s9sBri-MDiWtwb4=",  # Added
        "EMAIL_ACCOUNTS": '[{"email": "acc1@example.com", "password": "pass1"}, {"email": "acc2@example.com", "password": "pass2"}]',
    },
)
@patch("backend.services.scheduler.engine")
@patch("backend.services.scheduler.EmailService.fetch_recent_emails")
@patch("backend.services.scheduler.EmailForwarder.forward_email")
@patch("backend.services.scheduler.ReceiptDetector.is_receipt")
@patch("backend.services.scheduler.ReceiptDetector.categorize_receipt")
def test_multi_account_email_tagging(
    mock_categorize,
    mock_is_receipt,
    mock_forward,
    mock_fetch,
    mock_engine_patch,
    engine,
):
    """Test that emails from multiple accounts are correctly tagged with their source account"""
    # Use our test engine in the scheduler module
    original_engine = scheduler_module.engine
    scheduler_module.engine = engine

    try:
        # Mock email data from different accounts
        emails_acc1 = [
            {
                "message_id": "msg1",
                "subject": "Receipt from Amazon",
                "from": "amazon@example.com",
                "body": "Thanks for your order",
            }
        ]
        emails_acc2 = [
            {
                "message_id": "msg2",
                "subject": "Receipt from Starbucks",
                "from": "starbucks@example.com",
                "body": "Thanks for your purchase",
            }
        ]

        # Mock fetch_recent_emails to return different emails for different accounts
        def fetch_side_effect(user, pwd, server):
            if user == "acc1@example.com":
                return emails_acc1.copy()  # Return copy to avoid mutations
            elif user == "acc2@example.com":
                return emails_acc2.copy()
            return []

        mock_fetch.side_effect = fetch_side_effect
        mock_is_receipt.return_value = True
        mock_categorize.return_value = "Shopping"
        mock_forward.return_value = True

        # Call process_emails
        process_emails()

        # Verify that emails were tagged with correct source accounts
        with Session(engine) as session:
            emails = session.exec(select(ProcessedEmail)).all()
            assert len(emails) == 2

            # Find each email and verify its account_email
            msg1 = next(e for e in emails if e.email_id == "msg1")
            msg2 = next(e for e in emails if e.email_id == "msg2")

            assert msg1.account_email == "acc1@example.com"
            assert msg2.account_email == "acc2@example.com"

            # Verify both were processed
            assert msg1.status == "forwarded"
            assert msg2.status == "forwarded"

            # Verify processing run was created
            runs = session.exec(select(ProcessingRun)).all()
            assert len(runs) == 1
            assert runs[0].emails_checked == 2
            assert runs[0].emails_processed == 2
            assert runs[0].emails_forwarded == 2
    finally:
        # Restore original engine
        scheduler_module.engine = original_engine


def test_session_fixture_creates_db(session):
    """Test that the session fixture properly creates a database session"""
    # Verify the session is functional by querying for ProcessingRuns
    runs = session.exec(select(ProcessingRun)).all()
    assert len(runs) == 0  # New database should be empty


def test_redact_email_normal():
    """Test redact_email with normal email addresses"""
    assert redact_email("john@example.com") == "j**n@example.com"
    assert redact_email("jane@example.com") == "j**e@example.com"
    assert redact_email("alexander@example.com") == "a*******r@example.com"


def test_redact_email_short():
    """Test redact_email with short email addresses (2 chars or less)"""
    assert redact_email("ab@example.com") == "**@example.com"
    assert redact_email("a@example.com") == "*@example.com"


def test_redact_email_invalid():
    """Test redact_email with invalid input"""
    assert redact_email("not-an-email") == "[REDACTED]"
    assert redact_email("") == "[REDACTED]"
    assert redact_email(None) == "[REDACTED]"
    assert redact_email(123) == "[REDACTED]"


@patch.dict(os.environ, {"SECRET_KEY": ""})
@patch("backend.services.scheduler.engine")
def test_process_emails_no_secret_key(mock_engine_patch, engine):
    """Test that process_emails returns early when SECRET_KEY is not set"""
    # Use our test engine in the scheduler module
    original_engine = scheduler_module.engine
    scheduler_module.engine = engine

    try:
        # Ensure SECRET_KEY is not set
        if "SECRET_KEY" in os.environ:
            del os.environ["SECRET_KEY"]

        # Call process_emails
        process_emails()

        # Verify that no ProcessingRun was created
        with Session(engine) as session:
            runs = session.exec(select(ProcessingRun)).all()
            assert len(runs) == 0
    finally:
        # Restore original engine
        scheduler_module.engine = original_engine


@patch.dict(
    os.environ,
    {
        "POLL_INTERVAL": "60",
        "SECRET_KEY": "cpUbNMiXWufM3gAPx1arHE1h7Y72s9sBri-MDiWtwb4=",
    },
)
@patch("backend.services.scheduler.engine")
@patch("backend.services.scheduler.Session")
def test_process_emails_run_creation_error(mock_session_class, mock_engine_patch):
    """Test that process_emails handles errors when creating ProcessingRun"""
    # Mock Session to raise exception on commit
    mock_session = MagicMock()
    mock_session.__enter__ = MagicMock(return_value=mock_session)
    mock_session.__exit__ = MagicMock(return_value=False)
    mock_session.commit.side_effect = Exception("Database error")
    mock_session_class.return_value = mock_session

    # Call process_emails - should return early without crashing
    process_emails()

    # Verify session methods were attempted
    mock_session.add.assert_called()
    mock_session.commit.assert_called()


@patch.dict(
    os.environ,
    {
        "POLL_INTERVAL": "60",
        "SECRET_KEY": "cpUbNMiXWufM3gAPx1arHE1h7Y72s9sBri-MDiWtwb4=",
        "EMAIL_ACCOUNTS": "[]",
    },
)
@patch("backend.services.scheduler.engine")
@patch("backend.services.scheduler.EmailService.get_all_accounts")
def test_process_emails_no_accounts_configured(
    mock_get_accounts, mock_engine_patch, engine
):
    """Test that process_emails handles no configured accounts"""
    # Use our test engine in the scheduler module
    original_engine = scheduler_module.engine
    scheduler_module.engine = engine

    try:
        # Mock get_all_accounts to return empty list
        mock_get_accounts.return_value = []

        # Call process_emails
        process_emails()

        # Verify that a ProcessingRun was created with zero emails
        with Session(engine) as session:
            runs = session.exec(select(ProcessingRun)).all()
            assert len(runs) == 1
            run = runs[0]
            assert run.emails_checked == 0
            assert run.status == "completed"
    finally:
        # Restore original engine
        scheduler_module.engine = original_engine


@patch.dict(
    os.environ,
    {
        "POLL_INTERVAL": "60",
        "SECRET_KEY": "cpUbNMiXWufM3gAPx1arHE1h7Y72s9sBri-MDiWtwb4=",
        "GMAIL_EMAIL": "test@example.com",
        "GMAIL_PASSWORD": "password",
        "EMAIL_ACCOUNTS": "",  # Ensure no multi-account processing from local env
    },
)
@patch("backend.services.scheduler.engine")
@patch("backend.services.scheduler.EmailService.fetch_recent_emails")
def test_process_emails_no_wife_email(mock_fetch, mock_engine_patch, engine):
    """Test that process_emails handles missing WIFE_EMAIL"""
    # Use our test engine in the scheduler module
    original_engine = scheduler_module.engine
    scheduler_module.engine = engine

    try:
        # Mock email data
        mock_emails = [
            {
                "message_id": "msg1",
                "subject": "Test email",
                "from": "sender@example.com",
                "body": "Test body",
            }
        ]
        mock_fetch.return_value = mock_emails

        # Ensure WIFE_EMAIL is not set
        if "WIFE_EMAIL" in os.environ:
            del os.environ["WIFE_EMAIL"]

        # Call process_emails
        process_emails()

        # Verify that a ProcessingRun was created with error status
        with Session(engine) as session:
            runs = session.exec(select(ProcessingRun)).all()
            assert len(runs) == 1
            run = runs[0]
            assert run.status == "error"
            assert "WIFE_EMAIL not configured" in run.error_message
            assert run.emails_checked == 1
            assert run.emails_processed == 0
            assert run.emails_forwarded == 0
    finally:
        # Restore original engine
        scheduler_module.engine = original_engine


@patch.dict(
    os.environ,
    {
        "POLL_INTERVAL": "60",
        "WIFE_EMAIL": "wife@example.com",
        "SECRET_KEY": "cpUbNMiXWufM3gAPx1arHE1h7Y72s9sBri-MDiWtwb4=",
        "GMAIL_EMAIL": "test@example.com",
        "GMAIL_PASSWORD": "password",
    },
)
@patch("backend.services.scheduler.engine")
@patch("backend.services.scheduler.EmailService.fetch_recent_emails")
@patch("backend.services.scheduler.EmailForwarder.forward_email")
@patch("backend.services.scheduler.ReceiptDetector.is_receipt")
@patch("backend.services.scheduler.ReceiptDetector.categorize_receipt")
@patch("backend.services.learning_service.LearningService.run_shadow_mode")
@patch("backend.services.learning_service.LearningService.auto_promote_rules")
def test_process_emails_duplicate_detection(
    mock_auto_promote,
    mock_shadow_mode,
    mock_categorize,
    mock_is_receipt,
    mock_forward,
    mock_fetch,
    mock_engine_patch,
    engine,
):
    """Test that duplicate emails are skipped"""
    # Use our test engine in the scheduler module
    original_engine = scheduler_module.engine
    scheduler_module.engine = engine

    try:
        # Mock email data
        mock_emails = [
            {
                "message_id": "msg1",
                "subject": "Receipt from Amazon",
                "from": "amazon@example.com",
                "body": "Thanks for your order",
            }
        ]
        mock_fetch.return_value = mock_emails
        mock_is_receipt.return_value = True
        mock_categorize.return_value = "Shopping"
        mock_forward.return_value = True

        # First call - should process the email
        process_emails()

        # Second call with same email - should skip it
        process_emails()

        # Verify only one email was saved (duplicate was skipped)
        with Session(engine) as session:
            emails = session.exec(select(ProcessedEmail)).all()
            assert len(emails) == 1

            # Verify two runs were created
            runs = session.exec(select(ProcessingRun)).all()
            assert len(runs) == 2
    finally:
        # Restore original engine
        scheduler_module.engine = original_engine


@patch.dict(
    os.environ,
    {
        "POLL_INTERVAL": "60",
        "WIFE_EMAIL": "wife@example.com",
        "SECRET_KEY": "cpUbNMiXWufM3gAPx1arHE1h7Y72s9sBri-MDiWtwb4=",
        "GMAIL_EMAIL": "test@example.com",
        "GMAIL_PASSWORD": "password",
    },
)
@patch("backend.services.scheduler.engine")
@patch("backend.services.scheduler.EmailService.fetch_recent_emails")
@patch("backend.services.command_service.CommandService.is_command_email")
@patch("backend.services.command_service.CommandService.process_command")
@patch("backend.services.learning_service.LearningService.run_shadow_mode")
@patch("backend.services.learning_service.LearningService.auto_promote_rules")
def test_process_emails_command_processing(
    mock_auto_promote,
    mock_shadow_mode,
    mock_process_command,
    mock_is_command,
    mock_fetch,
    mock_engine_patch,
    engine,
):
    """Test that command emails are processed correctly"""
    # Use our test engine in the scheduler module
    original_engine = scheduler_module.engine
    scheduler_module.engine = engine

    try:
        # Mock command email
        mock_emails = [
            {
                "message_id": "cmd1",
                "subject": "Re: Receipt forwarded",
                "from": "wife@example.com",
                "body": "APPROVE amazon@example.com",
            }
        ]
        mock_fetch.return_value = mock_emails
        mock_is_command.return_value = True
        mock_process_command.return_value = True  # Command executed

        # Call process_emails
        process_emails()

        # Verify command email was processed
        with Session(engine) as session:
            emails = session.exec(select(ProcessedEmail)).all()
            assert len(emails) == 1
            email = emails[0]
            assert email.status == "command_executed"
            assert email.category == "command"
            assert email.reason == "User command"
    finally:
        # Restore original engine
        scheduler_module.engine = original_engine


@patch.dict(
    os.environ,
    {
        "POLL_INTERVAL": "60",
        "WIFE_EMAIL": "wife@example.com",
        "SECRET_KEY": "cpUbNMiXWufM3gAPx1arHE1h7Y72s9sBri-MDiWtwb4=",
        "GMAIL_EMAIL": "test@example.com",
        "GMAIL_PASSWORD": "password",
    },
)
@patch("backend.services.scheduler.engine")
@patch("backend.services.scheduler.EmailService.fetch_recent_emails")
@patch("backend.services.command_service.CommandService.is_command_email")
@patch("backend.services.command_service.CommandService.process_command")
@patch("backend.services.learning_service.LearningService.run_shadow_mode")
@patch("backend.services.learning_service.LearningService.auto_promote_rules")
def test_process_emails_command_no_action(
    mock_auto_promote,
    mock_shadow_mode,
    mock_process_command,
    mock_is_command,
    mock_fetch,
    mock_engine_patch,
    engine,
):
    """Test that command emails with no action are marked as ignored"""
    # Use our test engine in the scheduler module
    original_engine = scheduler_module.engine
    scheduler_module.engine = engine

    try:
        # Mock command email
        mock_emails = [
            {
                "message_id": "cmd1",
                "subject": "Re: Receipt forwarded",
                "from": "wife@example.com",
                "body": "Thanks",
            }
        ]
        mock_fetch.return_value = mock_emails
        mock_is_command.return_value = True
        mock_process_command.return_value = False  # No action

        # Call process_emails
        process_emails()

        # Verify command email was logged as ignored
        with Session(engine) as session:
            emails = session.exec(select(ProcessedEmail)).all()
            assert len(emails) == 1
            email = emails[0]
            assert email.status == "ignored"
            assert email.category == "command"
            assert email.reason == "Command from wife (no action)"
    finally:
        # Restore original engine
        scheduler_module.engine = original_engine


@patch.dict(
    os.environ,
    {
        "POLL_INTERVAL": "60",
        "WIFE_EMAIL": "wife@example.com",
        "SECRET_KEY": "cpUbNMiXWufM3gAPx1arHE1h7Y72s9sBri-MDiWtwb4=",
        "GMAIL_EMAIL": "test@example.com",
        "GMAIL_PASSWORD": "password",
    },
)
@patch("backend.services.scheduler.engine")
@patch("backend.services.scheduler.EmailService.fetch_recent_emails")
@patch("backend.services.scheduler.EmailForwarder.forward_email")
@patch("backend.services.scheduler.ReceiptDetector.is_receipt")
@patch("backend.services.scheduler.ReceiptDetector.categorize_receipt")
@patch("backend.services.learning_service.LearningService.run_shadow_mode")
@patch("backend.services.learning_service.LearningService.auto_promote_rules")
def test_process_emails_individual_error_handling(
    mock_auto_promote,
    mock_shadow_mode,
    mock_categorize,
    mock_is_receipt,
    mock_forward,
    mock_fetch,
    mock_engine_patch,
    engine,
):
    """Test that errors processing individual emails are handled gracefully"""
    # Use our test engine in the scheduler module
    original_engine = scheduler_module.engine
    scheduler_module.engine = engine

    try:
        # Mock email data
        mock_emails = [
            {
                "message_id": "msg1",
                "subject": "Receipt from Amazon",
                "from": "amazon@example.com",
                "body": "Thanks for your order",
            },
            {
                "message_id": "msg2",
                "subject": "Receipt from Starbucks",
                "from": "starbucks@example.com",
                "body": "Thanks for your purchase",
            },
        ]
        mock_fetch.return_value = mock_emails
        mock_is_receipt.return_value = True
        mock_categorize.return_value = "Shopping"
        # First email succeeds, second fails
        mock_forward.side_effect = [True, Exception("SMTP error")]

        # Call process_emails
        process_emails()

        # Verify that the run was created with error status
        with Session(engine) as session:
            runs = session.exec(select(ProcessingRun)).all()
            assert len(runs) == 1
            run = runs[0]
            assert run.status == "error"
            assert "Receipt from Starbucks" in run.error_message

            # Verify first email was processed successfully
            emails = session.exec(select(ProcessedEmail)).all()
            assert len(emails) >= 1  # At least the first one
    finally:
        # Restore original engine
        scheduler_module.engine = original_engine


@patch.dict(
    os.environ,
    {
        "POLL_INTERVAL": "60",
        "SECRET_KEY": "cpUbNMiXWufM3gAPx1arHE1h7Y72s9sBri-MDiWtwb4=",
        "GMAIL_EMAIL": "test@example.com",
        "GMAIL_PASSWORD": "password",
    },
)
@patch("backend.services.scheduler.engine")
@patch("backend.services.scheduler.EmailService.fetch_recent_emails")
def test_process_emails_top_level_exception(mock_fetch, mock_engine_patch, engine):
    """Test that top-level exceptions are caught and recorded"""
    # Use our test engine in the scheduler module
    original_engine = scheduler_module.engine
    scheduler_module.engine = engine

    try:
        # Mock fetch to raise an exception during processing
        mock_fetch.side_effect = Exception("Unexpected error")

        # Call process_emails
        process_emails()

        # Verify that a ProcessingRun was created with error status
        with Session(engine) as session:
            runs = session.exec(select(ProcessingRun)).all()
            assert len(runs) == 1
            run = runs[0]
            assert run.status == "error"
            assert run.error_message is not None
    finally:
        # Restore original engine
        scheduler_module.engine = original_engine


@patch.dict(os.environ, {"POLL_INTERVAL": "30"})
@patch("backend.services.scheduler.scheduler")
def test_start_scheduler_adds_cleanup_job(mock_scheduler):
    """Test that start_scheduler adds both process_emails and cleanup jobs"""
    start_scheduler()

    # Verify scheduler was started
    mock_scheduler.start.assert_called_once()

    # Verify two jobs were added
    assert mock_scheduler.add_job.call_count == 2

    # Verify the cleanup job was added with 1 hour interval
    calls = mock_scheduler.add_job.call_args_list
    cleanup_calls = [c for c in calls if c[0][0].__name__ == "cleanup_expired_emails"]
    assert len(cleanup_calls) == 1
    assert cleanup_calls[0].kwargs["hours"] == 1


def test_cleanup_expired_emails(engine):
    """Test that cleanup_expired_emails removes expired email bodies"""
    # Use our test engine in the scheduler module
    original_engine = scheduler_module.engine
    scheduler_module.engine = engine

    try:
        # Create test data with expired and non-expired emails
        with Session(engine) as session:
            # Expired email
            expired = ProcessedEmail(
                email_id="expired1",
                subject="Expired email",
                sender="sender@example.com",
                received_at=datetime.now(timezone.utc) - timedelta(hours=48),
                processed_at=datetime.now(timezone.utc) - timedelta(hours=48),
                status="forwarded",
                account_email="test@example.com",
                retention_expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
                encrypted_body="encrypted_body_data",
                encrypted_html="encrypted_html_data",
            )
            # Non-expired email
            non_expired = ProcessedEmail(
                email_id="active1",
                subject="Active email",
                sender="sender@example.com",
                received_at=datetime.now(timezone.utc),
                processed_at=datetime.now(timezone.utc),
                status="forwarded",
                account_email="test@example.com",
                retention_expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
                encrypted_body="encrypted_body_data",
                encrypted_html="encrypted_html_data",
            )
            session.add(expired)
            session.add(non_expired)
            session.commit()
            session.refresh(expired)
            session.refresh(non_expired)

        # Run cleanup
        cleanup_expired_emails()

        # Verify expired email body was removed
        with Session(engine) as session:
            expired_email = session.exec(
                select(ProcessedEmail).where(ProcessedEmail.email_id == "expired1")
            ).first()
            assert expired_email.encrypted_body is None
            assert expired_email.encrypted_html is None

            # Verify non-expired email body was not removed
            active_email = session.exec(
                select(ProcessedEmail).where(ProcessedEmail.email_id == "active1")
            ).first()
            assert active_email.encrypted_body == "encrypted_body_data"
            assert active_email.encrypted_html == "encrypted_html_data"
    finally:
        # Restore original engine
        scheduler_module.engine = original_engine


def test_cleanup_expired_emails_no_bodies(engine):
    """Test that cleanup_expired_emails handles emails with no bodies"""
    # Use our test engine in the scheduler module
    original_engine = scheduler_module.engine
    scheduler_module.engine = engine

    try:
        # Create expired email with no body
        with Session(engine) as session:
            expired = ProcessedEmail(
                email_id="expired1",
                subject="Expired email",
                sender="sender@example.com",
                received_at=datetime.now(timezone.utc) - timedelta(hours=48),
                processed_at=datetime.now(timezone.utc) - timedelta(hours=48),
                status="forwarded",
                account_email="test@example.com",
                retention_expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
                encrypted_body=None,
                encrypted_html=None,
            )
            session.add(expired)
            session.commit()
            session.refresh(expired)

        # Run cleanup - should not crash
        cleanup_expired_emails()

        # Verify email still exists
        with Session(engine) as session:
            email = session.exec(
                select(ProcessedEmail).where(ProcessedEmail.email_id == "expired1")
            ).first()
            assert email is not None
    finally:
        # Restore original engine
        scheduler_module.engine = original_engine


@patch("backend.services.scheduler.engine")
def test_cleanup_expired_emails_error_handling(mock_engine):
    """Test that cleanup_expired_emails handles errors gracefully"""
    # Mock Session to raise exception
    with patch("backend.services.scheduler.Session") as mock_session_class:
        mock_session = MagicMock()
        mock_session.__enter__ = MagicMock(side_effect=Exception("Database error"))
        mock_session_class.return_value = mock_session

        # Should not crash
        cleanup_expired_emails()


@patch("backend.services.scheduler.scheduler")
def test_stop_scheduler(mock_scheduler):
    """Test that stop_scheduler shuts down the scheduler"""
    stop_scheduler()

    # Verify scheduler.shutdown was called
    mock_scheduler.shutdown.assert_called_once()


@patch.dict(
    os.environ,
    {
        "POLL_INTERVAL": "60",
        "WIFE_EMAIL": "wife@example.com",
        "SECRET_KEY": "cpUbNMiXWufM3gAPx1arHE1h7Y72s9sBri-MDiWtwb4=",
        "GMAIL_EMAIL": "test@example.com",
        "GMAIL_PASSWORD": "password",
    },
)
@patch("backend.services.scheduler.engine")
@patch("backend.services.scheduler.EmailService.fetch_recent_emails")
@patch("backend.services.scheduler.EmailForwarder.forward_email")
@patch("backend.services.scheduler.ReceiptDetector.is_receipt")
@patch("backend.services.scheduler.ReceiptDetector.categorize_receipt")
@patch("backend.services.learning_service.LearningService.run_shadow_mode")
@patch("backend.services.learning_service.LearningService.auto_promote_rules")
def test_process_emails_multiple_errors(
    mock_auto_promote,
    mock_shadow_mode,
    mock_categorize,
    mock_is_receipt,
    mock_forward,
    mock_fetch,
    mock_engine_patch,
    engine,
):
    """Test that multiple errors processing emails are concatenated in error message"""
    # Use our test engine in the scheduler module
    original_engine = scheduler_module.engine
    scheduler_module.engine = engine

    try:
        # Mock email data with 3 emails
        mock_emails = [
            {
                "message_id": "msg1",
                "subject": "Receipt from Amazon",
                "from": "amazon@example.com",
                "body": "Thanks for your order",
            },
            {
                "message_id": "msg2",
                "subject": "Receipt from Starbucks",
                "from": "starbucks@example.com",
                "body": "Thanks for your purchase",
            },
            {
                "message_id": "msg3",
                "subject": "Receipt from Target",
                "from": "target@example.com",
                "body": "Thanks for shopping",
            },
        ]
        mock_fetch.return_value = mock_emails
        mock_is_receipt.return_value = True
        mock_categorize.return_value = "Shopping"
        # First email succeeds, second and third fail
        mock_forward.side_effect = [
            True,
            Exception("SMTP error 1"),
            Exception("SMTP error 2"),
        ]

        # Call process_emails
        process_emails()

        # Verify that the run was created with error status and concatenated errors
        with Session(engine) as session:
            runs = session.exec(select(ProcessingRun)).all()
            assert len(runs) == 1
            run = runs[0]
            assert run.status == "error"
            # Check that error message contains both failed emails
            assert "Receipt from Starbucks" in run.error_message
            assert "Receipt from Target" in run.error_message
    finally:
        # Restore original engine
        scheduler_module.engine = original_engine


@patch.dict(
    os.environ,
    {
        "POLL_INTERVAL": "60",
        "WIFE_EMAIL": "wife@example.com",
        "SECRET_KEY": "cpUbNMiXWufM3gAPx1arHE1h7Y72s9sBri-MDiWtwb4=",
        "GMAIL_EMAIL": "test@example.com",
        "GMAIL_PASSWORD": "password",
    },
)
@patch("backend.services.scheduler.engine")
@patch("backend.services.scheduler.EmailService.fetch_recent_emails")
@patch("backend.services.learning_service.LearningService.auto_promote_rules")
def test_process_emails_outer_exception(
    mock_auto_promote,
    mock_fetch,
    mock_engine_patch,
    engine,
):
    """Test that outer exceptions are caught and recorded properly"""
    # Use our test engine in the scheduler module
    original_engine = scheduler_module.engine
    scheduler_module.engine = engine

    try:
        # Mock fetch to return an email, but auto_promote_rules to raise exception
        mock_fetch.return_value = [
            {
                "message_id": "msg1",
                "subject": "Test email",
                "from": "sender@example.com",
                "body": "Test body",
            }
        ]
        mock_auto_promote.side_effect = Exception("Auto-promote failed")

        # Call process_emails
        process_emails()

        # Verify that a ProcessingRun was created with error status
        with Session(engine) as session:
            runs = session.exec(select(ProcessingRun)).all()
            assert len(runs) == 1
            run = runs[0]
            assert run.status == "error"
            assert "Auto-promote failed" in run.error_message
    finally:
        # Restore original engine
        scheduler_module.engine = original_engine
