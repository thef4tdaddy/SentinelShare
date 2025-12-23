import os
from unittest.mock import patch

import backend.services.scheduler as scheduler_module
import pytest
from backend.models import ProcessedEmail, ProcessingRun
from backend.services.scheduler import process_emails, start_scheduler
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
