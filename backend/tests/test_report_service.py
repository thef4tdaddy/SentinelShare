"""Unit tests for ReportService."""

import os
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest
from sqlmodel import Session, SQLModel, select

from backend.database import engine
from backend.models import CategoryRule, ManualRule, ProcessedEmail
from backend.services.report_service import ReportService


@pytest.fixture(name="session")
def session_fixture():
    """Create an in-memory database session for testing."""
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    SQLModel.metadata.drop_all(engine)


@pytest.fixture(name="sample_emails")
def sample_emails_fixture(session):
    """Create sample emails for testing."""
    now = datetime.now(timezone.utc)
    emails = [
        ProcessedEmail(
            email_id="email1@test.com",
            subject="Receipt from Amazon",
            sender="receipts@amazon.com",
            received_at=now - timedelta(days=1),
            processed_at=now - timedelta(days=1),
            status="forwarded",
            account_email="user@example.com",
            category="Shopping",
            amount=29.99,
        ),
        ProcessedEmail(
            email_id="email2@test.com",
            subject="Newsletter",
            sender="newsletter@company.com",
            received_at=now - timedelta(days=2),
            processed_at=now - timedelta(days=2),
            status="blocked",
            account_email="user@example.com",
            category=None,
        ),
        ProcessedEmail(
            email_id="email3@test.com",
            subject="Receipt from Target",
            sender="receipts@target.com",
            received_at=now - timedelta(days=3),
            processed_at=now - timedelta(days=3),
            status="forwarded",
            account_email="user@example.com",
            category="Shopping",
            amount=15.50,
        ),
    ]
    for email in emails:
        session.add(email)
    session.commit()
    return emails


class TestReportServicePagination:
    """Test pagination functionality."""

    def test_get_paginated_emails_default(self, session, sample_emails):
        """Test getting emails with default pagination."""
        result = ReportService.get_paginated_emails(session)

        assert len(result["emails"]) == 3
        assert result["pagination"]["page"] == 1
        assert result["pagination"]["per_page"] == 50
        assert result["pagination"]["total"] == 3

    def test_get_paginated_emails_custom_page_size(self, session, sample_emails):
        """Test custom page size."""
        result = ReportService.get_paginated_emails(session, per_page=2)

        assert len(result["emails"]) == 2
        assert result["pagination"]["per_page"] == 2
        assert result["pagination"]["total_pages"] == 2

    def test_get_paginated_emails_ordering(self, session, sample_emails):
        """Test emails are ordered by processed_at descending."""
        result = ReportService.get_paginated_emails(session)

        emails = result["emails"]
        # Most recent first
        assert emails[0].email_id == "email1@test.com"
        assert emails[1].email_id == "email2@test.com"
        assert emails[2].email_id == "email3@test.com"


class TestReportServiceFiltering:
    """Test filtering functionality."""

    def test_filter_by_status(self, session, sample_emails):
        """Test filtering by status."""
        result = ReportService.get_paginated_emails(session, status="forwarded")

        assert len(result["emails"]) == 2
        for email in result["emails"]:
            assert email.status == "forwarded"

    def test_filter_by_sender(self, session, sample_emails):
        """Test filtering by sender."""
        result = ReportService.get_paginated_emails(session, sender="amazon")

        assert len(result["emails"]) == 1
        assert result["emails"][0].sender == "receipts@amazon.com"

    def test_filter_by_date_range(self, session, sample_emails):
        """Test filtering by date range."""
        now = datetime.now(timezone.utc)
        date_from = now - timedelta(days=2, hours=12)

        result = ReportService.get_paginated_emails(session, date_from=date_from)

        assert len(result["emails"]) == 2

    def test_filter_by_amount_range(self, session, sample_emails):
        """Test filtering by amount range."""
        result = ReportService.get_paginated_emails(
            session, min_amount=20.0, max_amount=30.0
        )

        assert len(result["emails"]) == 1
        assert result["emails"][0].amount == 29.99


class TestReportServiceReprocessing:
    """Test email reprocessing functionality."""

    @patch("backend.services.report_service.decrypt_content")
    @patch("backend.services.report_service.ReceiptDetector")
    def test_reprocess_email_success(self, mock_detector, mock_decrypt, session):
        """Test successful email reprocessing."""
        # Create a test email
        email = ProcessedEmail(
            email_id="test@example.com",
            subject="Test Receipt",
            sender="store@example.com",
            received_at=datetime.now(timezone.utc),
            processed_at=datetime.now(timezone.utc),
            status="blocked",
            account_email="user@example.com",
            encrypted_body="encrypted_content",
        )
        session.add(email)
        session.commit()

        # Mock decryption and detection
        mock_decrypt.return_value = "decrypted body"
        mock_detector.debug_is_receipt.return_value = {
            "final_decision": True,
            "reason": "test",
        }
        mock_detector.categorize_receipt.return_value = "Shopping"

        result = ReportService.reprocess_email(email.id, session)

        assert result["current_status"] == "blocked"
        assert result["suggested_status"] == "forwarded"
        assert result["category"] == "Shopping"

    def test_reprocess_email_not_found(self, session):
        """Test reprocessing non-existent email."""
        with pytest.raises(ValueError, match="Email not found"):
            ReportService.reprocess_email(999, session)


class TestReportServiceFeedback:
    """Test feedback functionality."""

    def test_submit_feedback_creates_rule(self, session):
        """Test submitting feedback creates a suggested rule."""
        email = ProcessedEmail(
            email_id="test@example.com",
            subject="Receipt from Store",
            sender="receipts@store.com",
            received_at=datetime.now(timezone.utc),
            processed_at=datetime.now(timezone.utc),
            status="blocked",
            account_email="user@example.com",
        )
        session.add(email)
        session.commit()

        with patch(
            "backend.services.learning_service.LearningService.generate_rule_from_email"
        ) as mock_generate:
            mock_generate.return_value = {
                "email_pattern": "*@store.com",
                "subject_pattern": None,
                "purpose": "Test rule",
                "confidence": 0.8,
            }

            result = ReportService.submit_feedback(email.id, True, session)

            assert result["status"] == "success"
            # Check that a rule was created
            rule = session.exec(select(ManualRule)).first()
            assert rule is not None
            assert rule.email_pattern == "*@store.com"

    def test_submit_feedback_email_not_found(self, session):
        """Test feedback on non-existent email."""
        with pytest.raises(ValueError, match="Email not found"):
            ReportService.submit_feedback(999, True, session)


class TestReportServiceCategoryUpdate:
    """Test category update functionality."""

    def test_update_email_category_success(self, session):
        """Test successful category update."""
        email = ProcessedEmail(
            email_id="test@example.com",
            subject="Receipt",
            sender="store@example.com",
            received_at=datetime.now(timezone.utc),
            processed_at=datetime.now(timezone.utc),
            status="forwarded",
            account_email="user@example.com",
            category="Old Category",
        )
        session.add(email)
        session.commit()

        result = ReportService.update_email_category(
            email.id, "New Category", False, "sender", session
        )

        assert result["status"] == "success"
        assert "Old Category" in result["message"]
        assert "New Category" in result["message"]
        assert result["rule_created"] is False

        # Verify email was updated
        session.refresh(email)
        assert email.category == "New Category"

    def test_update_email_category_with_rule_creation(self, session):
        """Test category update with rule creation."""
        email = ProcessedEmail(
            email_id="test@example.com",
            subject="Receipt from Store",
            sender="receipts@store.com",
            received_at=datetime.now(timezone.utc),
            processed_at=datetime.now(timezone.utc),
            status="forwarded",
            account_email="user@example.com",
            category="Shopping",
        )
        session.add(email)
        session.commit()

        result = ReportService.update_email_category(
            email.id, "Retail", True, "sender", session
        )

        assert result["rule_created"] is True
        assert "rule created" in result["message"]

        # Verify rule was created
        rule = session.exec(select(CategoryRule)).first()
        assert rule is not None
        assert rule.pattern == "*@store.com"
        assert rule.assigned_category == "Retail"

    def test_update_email_category_invalid(self, session):
        """Test category update with invalid data."""
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

        # Empty category
        with pytest.raises(ValueError, match="cannot be empty"):
            ReportService.update_email_category(email.id, "  ", False, "sender", session)

        # Invalid match_type
        with pytest.raises(ValueError, match="must be either"):
            ReportService.update_email_category(
                email.id, "Category", False, "invalid", session
            )


class TestReportServiceStats:
    """Test statistics functionality."""

    def test_get_history_stats(self, session, sample_emails):
        """Test getting history statistics."""
        result = ReportService.get_history_stats(session)

        assert result["total"] == 3
        assert result["forwarded"] == 2
        assert result["blocked"] == 1
        assert result["errors"] == 0
        assert abs(result["total_amount"] - 45.49) < 0.01  # 29.99 + 15.50 with float tolerance
        assert result["status_breakdown"]["forwarded"] == 2
        assert result["status_breakdown"]["blocked"] == 1


class TestReportServiceCSVExport:
    """Test CSV export functionality."""

    def test_generate_csv_export(self, session, sample_emails):
        """Test CSV export generation."""
        generator = ReportService.generate_csv_export(session)

        # Collect all chunks
        chunks = list(generator)

        # Should have header + 3 data rows
        csv_content = "".join(chunks)
        lines = csv_content.strip().split("\n")

        assert len(lines) == 4  # Header + 3 emails
        assert "Date" in lines[0]
        assert "Vendor" in lines[0]
        assert "Amount" in lines[0]

    def test_generate_csv_export_with_filters(self, session, sample_emails):
        """Test CSV export with filters."""
        generator = ReportService.generate_csv_export(session, status="forwarded")

        csv_content = "".join(list(generator))
        lines = csv_content.strip().split("\n")

        # Header + 2 forwarded emails
        assert len(lines) == 3


class TestReportServiceReprocessAllIgnored:
    """Test reprocessing all ignored emails."""

    @patch.dict(os.environ, {"WIFE_EMAIL": "wife@example.com"})
    @patch("backend.services.report_service.ReceiptDetector")
    @patch("backend.services.report_service.EmailForwarder")
    @patch("backend.services.report_service.decrypt_content")
    def test_reprocess_all_ignored(
        self, mock_decrypt, mock_forwarder, mock_detector, session
    ):
        """Test reprocessing all ignored emails."""
        now = datetime.now(timezone.utc)
        email = ProcessedEmail(
            email_id="ignored@test.com",
            subject="Receipt",
            sender="store@example.com",
            received_at=now - timedelta(hours=1),
            processed_at=now - timedelta(hours=1),
            status="ignored",
            account_email="user@example.com",
            encrypted_body="encrypted",
        )
        session.add(email)
        session.commit()

        mock_decrypt.return_value = "body"
        mock_detector.is_receipt.return_value = True
        mock_detector.categorize_receipt.return_value = "Shopping"
        mock_forwarder.forward_email.return_value = True

        result = ReportService.reprocess_all_ignored(session)

        assert result["status"] == "success"
        assert result["reprocessed"] == 1
        assert result["newly_forwarded"] == 1

        # Verify email status updated
        session.refresh(email)
        assert email.status == "forwarded"
