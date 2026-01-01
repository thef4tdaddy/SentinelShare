"""Unit tests for WorkflowService."""

import os
from datetime import datetime, timezone
from unittest.mock import patch

import pytest
from sqlmodel import Session, SQLModel, select

from backend.database import engine
from backend.models import ManualRule, Preference, ProcessedEmail
from backend.services.workflow_service import WorkflowService


@pytest.fixture(name="session")
def session_fixture():
    """Create an in-memory database session for testing."""
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    SQLModel.metadata.drop_all(engine)


class TestWorkflowServiceToggleToIgnored:
    """Test toggling emails to ignored status."""

    def test_toggle_forwarded_to_ignored(self, session):
        """Test toggling forwarded email to ignored."""
        email = ProcessedEmail(
            email_id="test@example.com",
            subject="Receipt",
            sender="store@example.com",
            received_at=datetime.now(timezone.utc),
            processed_at=datetime.now(timezone.utc),
            status="forwarded",
            account_email="user@example.com",
        )
        session.add(email)
        session.commit()

        result = WorkflowService.toggle_to_ignored(email.id, session)

        assert result["success"] is True
        assert "forwarded" in result["message"]
        assert "ignored" in result["message"]

        session.refresh(email)
        assert email.status == "ignored"
        assert "Manually changed from forwarded to ignored" in email.reason

    def test_toggle_blocked_to_ignored(self, session):
        """Test toggling blocked email to ignored."""
        email = ProcessedEmail(
            email_id="test@example.com",
            subject="Newsletter",
            sender="newsletter@example.com",
            received_at=datetime.now(timezone.utc),
            processed_at=datetime.now(timezone.utc),
            status="blocked",
            account_email="user@example.com",
        )
        session.add(email)
        session.commit()

        result = WorkflowService.toggle_to_ignored(email.id, session)

        assert result["success"] is True
        session.refresh(email)
        assert email.status == "ignored"

    def test_toggle_to_ignored_invalid_status(self, session):
        """Test toggling email with invalid status raises error."""
        email = ProcessedEmail(
            email_id="test@example.com",
            subject="Receipt",
            sender="store@example.com",
            received_at=datetime.now(timezone.utc),
            processed_at=datetime.now(timezone.utc),
            status="ignored",
            account_email="user@example.com",
        )
        session.add(email)
        session.commit()

        with pytest.raises(ValueError, match="Only 'forwarded' or 'blocked'"):
            WorkflowService.toggle_to_ignored(email.id, session)

    def test_toggle_to_ignored_not_found(self, session):
        """Test toggling non-existent email raises error."""
        with pytest.raises(ValueError, match="Email not found"):
            WorkflowService.toggle_to_ignored(999, session)


class TestWorkflowServiceToggleIgnoredToForwarded:
    """Test toggling ignored emails to forwarded."""

    @patch.dict(os.environ, {"WIFE_EMAIL": "wife@example.com"})
    @patch("backend.services.workflow_service.EmailForwarder.forward_email")
    @patch("backend.services.workflow_service.WorkflowService._fetch_email_content")
    def test_toggle_ignored_to_forwarded_new_rule(
        self, mock_fetch, mock_forward, session
    ):
        """Test toggling ignored email creates new rule and forwards."""
        email = ProcessedEmail(
            email_id="test@example.com",
            subject="Receipt from Store",
            sender="receipts@store.com",
            received_at=datetime.now(timezone.utc),
            processed_at=datetime.now(timezone.utc),
            status="ignored",
            account_email="user@example.com",
        )
        session.add(email)
        session.commit()

        mock_fetch.return_value = "email body content"
        mock_forward.return_value = True

        result = WorkflowService.toggle_ignored_to_forwarded(email.id, session)

        assert result["success"] is True
        assert (
            result["message"]
            == "Email forwarded and rule created for receipts@store.com"
        )

        # Verify email status updated
        session.refresh(email)
        assert email.status == "forwarded"
        assert "Manually toggled from ignored" in email.reason

        # Verify rule was created
        rule = session.exec(select(ManualRule)).first()
        assert rule is not None
        assert rule.email_pattern == "receipts@store.com"

    @patch.dict(os.environ, {"WIFE_EMAIL": "wife@example.com"})
    @patch("backend.services.workflow_service.EmailForwarder.forward_email")
    @patch("backend.services.workflow_service.WorkflowService._fetch_email_content")
    def test_toggle_ignored_to_forwarded_existing_rule(
        self, mock_fetch, mock_forward, session
    ):
        """Test toggling ignored email with existing rule."""
        # Create existing rule
        existing_rule = ManualRule(
            email_pattern="receipts@store.com",
            subject_pattern=None,
            priority=10,
            purpose="Existing rule",
        )
        session.add(existing_rule)

        email = ProcessedEmail(
            email_id="test@example.com",
            subject="Receipt",
            sender="receipts@store.com",
            received_at=datetime.now(timezone.utc),
            processed_at=datetime.now(timezone.utc),
            status="ignored",
            account_email="user@example.com",
        )
        session.add(email)
        session.commit()

        mock_fetch.return_value = "email body"
        mock_forward.return_value = True

        result = WorkflowService.toggle_ignored_to_forwarded(email.id, session)

        assert result["success"] is True

        # Verify only one rule exists (no duplicate)
        rules = session.exec(select(ManualRule)).all()
        assert len(rules) == 1

    @patch.dict(os.environ, {"WIFE_EMAIL": "wife@example.com"})
    @patch("backend.services.workflow_service.EmailForwarder.forward_email")
    @patch("backend.services.workflow_service.WorkflowService._fetch_email_content")
    def test_toggle_ignored_forward_failure(self, mock_fetch, mock_forward, session):
        """Test handling of forward failure."""
        email = ProcessedEmail(
            email_id="test@example.com",
            subject="Receipt",
            sender="store@example.com",
            received_at=datetime.now(timezone.utc),
            processed_at=datetime.now(timezone.utc),
            status="ignored",
            account_email="user@example.com",
        )
        session.add(email)
        session.commit()

        mock_fetch.return_value = "email body"
        mock_forward.return_value = False  # Forward fails

        with pytest.raises(ValueError, match="Failed to forward email"):
            WorkflowService.toggle_ignored_to_forwarded(email.id, session)

        # Verify email status not changed
        session.refresh(email)
        assert email.status == "ignored"

    def test_toggle_ignored_missing_wife_email(self, session):
        """Test error when WIFE_EMAIL not configured."""
        email = ProcessedEmail(
            email_id="test@example.com",
            subject="Receipt",
            sender="store@example.com",
            received_at=datetime.now(timezone.utc),
            processed_at=datetime.now(timezone.utc),
            status="ignored",
            account_email="user@example.com",
        )
        session.add(email)
        session.commit()

        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="WIFE_EMAIL not configured"):
                WorkflowService.toggle_ignored_to_forwarded(email.id, session)

    def test_toggle_ignored_invalid_sender(self, session):
        """Test error when sender has no valid email pattern."""
        email = ProcessedEmail(
            email_id="test@example.com",
            subject="Receipt",
            sender="invalid-sender",
            received_at=datetime.now(timezone.utc),
            processed_at=datetime.now(timezone.utc),
            status="ignored",
            account_email="user@example.com",
        )
        session.add(email)
        session.commit()

        with pytest.raises(ValueError, match="Could not extract email pattern"):
            WorkflowService.toggle_ignored_to_forwarded(email.id, session)


class TestWorkflowServiceUploadReceipt:
    """Test receipt upload functionality."""

    def test_upload_receipt_success(self, session):
        """Test successful receipt upload."""
        file_content = b"PDF content here"
        filename = "receipt.pdf"
        content_type = "application/pdf"

        with patch(
            "backend.services.workflow_service.ReceiptDetector.categorize_receipt"
        ) as mock_categorize:
            mock_categorize.return_value = "Shopping"

            result = WorkflowService.upload_receipt(
                file_content, filename, content_type, session
            )

            assert result["success"] is True
            assert "receipt.pdf" in result["message"]
            assert "file_path" in result
            assert "record_id" in result

            # Verify database record created
            email = session.exec(
                select(ProcessedEmail).where(ProcessedEmail.sender == "manual_upload")
            ).first()
            assert email is not None
            assert email.status == "manual_upload"
            assert email.category == "Shopping"

    def test_upload_receipt_file_save_failure(self, session):
        """Test handling of file save failure."""
        file_content = b"content"
        filename = "receipt.pdf"
        content_type = "application/pdf"

        with patch("builtins.open", side_effect=IOError("Disk full")):
            with pytest.raises(ValueError, match="Failed to save file"):
                WorkflowService.upload_receipt(
                    file_content, filename, content_type, session
                )


class TestWorkflowServiceUpdatePreferences:
    """Test preference update functionality."""

    def test_update_preferences_bulk_replace(self, session):
        """Test bulk preference update."""
        # Create existing preferences
        session.add(Preference(item="old1@example.com", type="Blocked Sender"))
        session.add(Preference(item="old2@example.com", type="Always Forward"))
        session.commit()

        blocked = ["new1@example.com", "new2@example.com"]
        allowed = ["new3@example.com"]

        result = WorkflowService.update_preferences(blocked, allowed, session)

        assert result["success"] is True

        # Verify old preferences removed
        old_prefs = session.exec(
            select(Preference).where(Preference.item.in_(["old1@example.com", "old2@example.com"]))  # type: ignore
        ).all()
        assert len(old_prefs) == 0

        # Verify new preferences added
        blocked_prefs = session.exec(
            select(Preference).where(Preference.type == "Blocked Sender")
        ).all()
        assert len(blocked_prefs) == 2

        allowed_prefs = session.exec(
            select(Preference).where(Preference.type == "Always Forward")
        ).all()
        assert len(allowed_prefs) == 1

    def test_update_preferences_empty_lists(self, session):
        """Test updating with empty lists."""
        # Create existing preferences
        session.add(Preference(item="old@example.com", type="Blocked Sender"))
        session.commit()

        result = WorkflowService.update_preferences([], [], session)

        assert result["success"] is True

        # Verify all preferences removed
        prefs = session.exec(select(Preference)).all()
        assert len(prefs) == 0


class TestWorkflowServiceFetchEmailContent:
    """Test email content fetching functionality."""

    @patch("backend.services.workflow_service.EmailService.get_credentials_for_account")
    @patch("backend.services.workflow_service.EmailService.fetch_email_by_id")
    def test_fetch_email_content_success(self, mock_fetch, mock_get_creds, session):
        """Test successful email content fetch."""
        email = ProcessedEmail(
            email_id="test@example.com",
            subject="Receipt",
            sender="store@example.com",
            received_at=datetime.now(timezone.utc),
            processed_at=datetime.now(timezone.utc),
            status="ignored",
            account_email="user@example.com",
        )

        mock_get_creds.return_value = {
            "email": "user@example.com",
            "password": "password",
            "imap_server": "imap.gmail.com",
        }
        mock_fetch.return_value = {
            "body": "Plain text body",
            "html_body": "<p>HTML body</p>",
        }

        result = WorkflowService._fetch_email_content(email, session)

        assert "HTML body" in result
        assert "SentinelShare Notification" in result

    @patch("backend.services.workflow_service.EmailService.get_credentials_for_account")
    def test_fetch_email_content_not_found(self, mock_get_creds, session):
        """Test email content fetch when email not found."""
        email = ProcessedEmail(
            email_id="test@example.com",
            subject="Receipt",
            sender="store@example.com",
            received_at=datetime.now(timezone.utc),
            processed_at=datetime.now(timezone.utc),
            status="ignored",
            account_email="user@example.com",
        )

        mock_get_creds.return_value = None

        with patch.dict(os.environ, {}, clear=True):
            result = WorkflowService._fetch_email_content(email, session)

            # Should return fallback message
            assert "Original email body is not available" in result
