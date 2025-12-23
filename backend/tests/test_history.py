from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest
from backend.models import ProcessedEmail, ProcessingRun
from backend.routers import history
from sqlmodel import Session, SQLModel, create_engine, select
from sqlmodel.pool import StaticPool

# Test constants
MOCK_IMAP_CREDENTIALS = {
    "password": "test_password",
    "imap_server": "imap.example.com",
}


@pytest.fixture(name="session")
def session_fixture():
    """Create an in-memory database for testing"""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="sample_emails")
def sample_emails_fixture(session: Session):
    """Create sample emails for testing"""
    now = datetime.now(timezone.utc)

    emails = [
        ProcessedEmail(
            email_id="email1@test.com",
            subject="Amazon Receipt",
            sender="order@amazon.com",
            received_at=now - timedelta(minutes=10),
            processed_at=now - timedelta(minutes=10),
            status="forwarded",
            account_email="user1@example.com",
            category="shopping",
            amount=49.99,
            reason="Detected as receipt",
        ),
        ProcessedEmail(
            email_id="email2@test.com",
            subject="Spam Email",
            sender="spam@example.com",
            received_at=now - timedelta(minutes=20),
            processed_at=now - timedelta(minutes=20),
            status="blocked",
            account_email="user1@example.com",
            category="spam",
            reason="Not a receipt",
        ),
        ProcessedEmail(
            email_id="email3@test.com",
            subject="Uber Receipt",
            sender="receipts@uber.com",
            received_at=now - timedelta(minutes=30),
            processed_at=now - timedelta(minutes=30),
            status="forwarded",
            account_email="user2@example.com",
            category="transportation",
            amount=25.50,
            reason="Detected as receipt",
        ),
        ProcessedEmail(
            email_id="email4@test.com",
            subject="Newsletter",
            sender="news@example.com",
            received_at=now - timedelta(minutes=40),
            processed_at=now - timedelta(minutes=40),
            status="ignored",
            account_email="user1@example.com",
            category=None,
            reason="Not a receipt",
        ),
        ProcessedEmail(
            email_id="email5@test.com",
            subject="Error Processing Email",
            sender="test@example.com",
            received_at=now - timedelta(minutes=50),
            processed_at=now - timedelta(minutes=50),
            status="error",
            account_email="user1@example.com",
            category=None,
            reason="SMTP Error",
        ),
    ]

    for email in emails:
        session.add(email)
    session.commit()

    return emails


class TestHistoryEmails:

    def test_get_emails_default_pagination(self, session: Session, sample_emails):
        """Test getting email history with default pagination"""
        from backend.routers.history import get_email_history

        result = get_email_history(page=1, per_page=50, session=session)

        assert "emails" in result
        assert "pagination" in result
        assert len(result["emails"]) == 5
        assert result["pagination"]["page"] == 1
        assert result["pagination"]["total"] == 5

    def test_get_emails_custom_pagination(self, session: Session, sample_emails):
        """Test getting email history with custom pagination"""
        from backend.routers.history import get_email_history

        result = get_email_history(page=1, per_page=2, session=session)

        assert len(result["emails"]) == 2
        assert result["pagination"]["per_page"] == 2
        assert result["pagination"]["total_pages"] == 3

    def test_get_emails_filter_by_status(self, session: Session, sample_emails):
        """Test filtering emails by status"""
        from backend.routers.history import EmailStatus, get_email_history

        result = get_email_history(
            page=1, per_page=50, status=EmailStatus.FORWARDED, session=session
        )

        assert len(result["emails"]) == 2
        for email in result["emails"]:
            assert email.status == "forwarded"

    def test_get_emails_filter_by_blocked_status(self, session: Session, sample_emails):
        """Test filtering emails by blocked status"""
        from backend.routers.history import EmailStatus, get_email_history

        result = get_email_history(
            page=1, per_page=50, status=EmailStatus.BLOCKED, session=session
        )

        assert len(result["emails"]) == 1
        assert result["emails"][0].status == "blocked"

    def test_get_emails_ordered_by_processed_at_desc(
        self, session: Session, sample_emails
    ):
        """Test that emails are ordered by processed_at descending"""
        from backend.routers.history import get_email_history

        result = get_email_history(page=1, per_page=50, session=session)

        emails = result["emails"]
        # First email should be the most recent (email1)
        assert emails[0].email_id == "email1@test.com"
        # Last email should be the oldest (email5)
        assert emails[-1].email_id == "email5@test.com"


class TestHistoryStats:

    def test_get_stats_all_emails(self, session: Session, sample_emails):
        """Test getting statistics for all emails"""
        from backend.routers.history import get_history_stats

        result = get_history_stats(session=session)

        assert result["total"] == 5
        assert result["forwarded"] == 2
        assert result["blocked"] == 2  # blocked + ignored
        assert result["errors"] == 1
        assert (
            abs(result["total_amount"] - 75.49) < 0.01
        )  # 49.99 + 25.50 with floating point tolerance

    def test_get_stats_status_breakdown(self, session: Session, sample_emails):
        """Test status breakdown in statistics"""
        from backend.routers.history import get_history_stats

        result = get_history_stats(session=session)

        assert "status_breakdown" in result
        assert result["status_breakdown"]["forwarded"] == 2
        assert result["status_breakdown"]["blocked"] == 1
        assert result["status_breakdown"]["ignored"] == 1
        assert result["status_breakdown"]["error"] == 1


class TestHistoryRuns:

    def test_get_recent_runs_empty(self, session: Session):
        """Test getting recent runs when no emails exist"""
        from backend.routers.history import get_recent_runs

        result = get_recent_runs(limit=20, session=session)

        assert "runs" in result
        assert len(result["runs"]) == 0

    def test_get_recent_runs_with_emails(self, session: Session, sample_emails):
        """Test getting recent runs with sample emails"""
        from backend.routers.history import get_recent_runs

        # Create dummy runs to match the expectation of "recent runs"
        run1 = ProcessingRun(
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
            emails_checked=3,
            emails_processed=3,
            emails_forwarded=1,
            status="completed",
            check_interval_minutes=60,
        )
        session.add(run1)
        session.commit()

        result = get_recent_runs(limit=20, session=session)

        assert "runs" in result
        runs = result["runs"]

        # Should group emails into runs (emails spaced 10 minutes apart will be in different runs)
        assert len(runs) > 0

        # Each run should have required fields
        for run in runs:
            assert "run_time" in run
            assert "total_emails" in run
            assert "forwarded" in run
            assert "blocked" in run
            assert "errors" in run

    def test_get_recent_runs_limit(self, session: Session, sample_emails):
        """Test limiting the number of runs returned"""
        from backend.routers.history import get_recent_runs

        result = get_recent_runs(limit=2, session=session)

        assert len(result["runs"]) <= 2

    def test_get_recent_runs_aggregation(self, session: Session, sample_emails):
        """Test that runs correctly aggregate email statistics"""
        from backend.routers.history import get_recent_runs

        # Create dummy runs to match the expectation
        # We need total 5 emails, 2 forwarded, 2 blocked, 1 error
        # Run 1: 3 emails (1 fwd, 1 blocked, 1 error)
        run1 = ProcessingRun(
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
            emails_checked=3,
            emails_processed=3,
            emails_forwarded=1,
            status="error",  # One error in this batch
            check_interval_minutes=60,
        )
        # Run 2: 2 emails (1 fwd, 1 blocked)
        run2 = ProcessingRun(
            started_at=datetime.now(timezone.utc) - timedelta(minutes=10),
            completed_at=datetime.now(timezone.utc) - timedelta(minutes=9),
            emails_checked=2,
            emails_processed=2,
            emails_forwarded=1,
            status="completed",
            check_interval_minutes=60,
        )
        session.add(run1)
        session.add(run2)
        session.commit()

        result = get_recent_runs(limit=20, session=session)

        runs = result["runs"]

        # Sum up all emails across runs should equal total sample emails
        total_emails = sum(run["total_emails"] for run in runs)
        assert total_emails == 5

        # Verify counts
        total_forwarded = sum(run["forwarded"] for run in runs)
        total_blocked = sum(run["blocked"] for run in runs)
        total_errors = sum(run["errors"] for run in runs)

        assert total_forwarded == 2
        assert total_blocked == 3
        assert total_errors == 1


class TestHistoryDateFiltering:
    """Test date filtering functionality"""

    def test_filter_emails_by_date_from(self, session: Session, sample_emails):
        """Test filtering emails by date_from parameter"""
        from backend.routers.history import get_email_history

        now = datetime.now(timezone.utc)
        date_from = (now - timedelta(minutes=25)).isoformat()

        result = get_email_history(
            page=1, per_page=50, date_from=date_from, session=session
        )

        # Should only include email1 and email2 (within last 25 minutes)
        assert len(result["emails"]) == 2
        assert result["emails"][0].email_id == "email1@test.com"
        assert result["emails"][1].email_id == "email2@test.com"

    def test_filter_emails_by_date_to(self, session: Session, sample_emails):
        """Test filtering emails by date_to parameter"""
        from backend.routers.history import get_email_history

        now = datetime.now(timezone.utc)
        date_to = (now - timedelta(minutes=35)).isoformat()

        result = get_email_history(
            page=1, per_page=50, date_to=date_to, session=session
        )

        # Should only include email4 and email5 (older than 35 minutes)
        assert len(result["emails"]) == 2

    def test_filter_emails_by_date_range(self, session: Session, sample_emails):
        """Test filtering emails by both date_from and date_to"""
        from backend.routers.history import get_email_history

        now = datetime.now(timezone.utc)
        date_from = (now - timedelta(minutes=45)).isoformat()
        date_to = (now - timedelta(minutes=15)).isoformat()

        result = get_email_history(
            page=1, per_page=50, date_from=date_from, date_to=date_to, session=session
        )

        # Should include email2, email3, email4 (between 15-45 minutes ago)
        assert len(result["emails"]) == 3

    def test_invalid_date_from_format(self, session: Session, sample_emails):
        """Test that invalid date_from format returns 400 error"""
        from backend.routers.history import get_email_history
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            get_email_history(
                page=1, per_page=50, date_from="invalid-date", session=session
            )

        assert exc_info.value.status_code == 400
        assert "Invalid date format" in exc_info.value.detail

    def test_invalid_date_to_format(self, session: Session, sample_emails):
        """Test that invalid date_to format returns 400 error"""
        from backend.routers.history import get_email_history
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            get_email_history(
                page=1, per_page=50, date_to="not-a-date", session=session
            )

        assert exc_info.value.status_code == 400
        assert "Invalid date format" in exc_info.value.detail

    def test_stats_with_date_from_filter(self, session: Session, sample_emails):
        """Test statistics with date_from filter"""
        from backend.routers.history import get_history_stats

        now = datetime.now(timezone.utc)
        date_from = (now - timedelta(minutes=25)).isoformat()

        result = get_history_stats(date_from=date_from, session=session)

        # Should only count email1 and email2
        assert result["total"] == 2
        assert result["forwarded"] == 1
        assert result["blocked"] == 1

    def test_stats_with_date_to_filter(self, session: Session, sample_emails):
        """Test statistics with date_to filter"""
        from backend.routers.history import get_history_stats

        now = datetime.now(timezone.utc)
        date_to = (now - timedelta(minutes=35)).isoformat()

        result = get_history_stats(date_to=date_to, session=session)

        # Should only count email4 and email5 (older than 35 minutes)
        assert result["total"] == 2

    def test_stats_with_invalid_date(self, session: Session, sample_emails):
        """Test that stats endpoint returns 400 for invalid dates"""
        from backend.routers.history import get_history_stats
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            get_history_stats(date_from="bad-date", session=session)

        assert exc_info.value.status_code == 400

    def test_empty_date_strings_ignored(self, session: Session, sample_emails):
        """Test that empty date strings are handled gracefully"""
        from backend.routers.history import get_email_history

        # Empty strings should be treated as None (no filter)
        result = get_email_history(
            page=1, per_page=50, date_from="", date_to="", session=session
        )

        # Should return all emails when dates are empty
        assert len(result["emails"]) == 5


class TestHistoryStatusValidation:
    """Test status parameter validation"""

    def test_valid_status_forwarded(self, session: Session, sample_emails):
        """Test filtering with valid 'forwarded' status"""
        from backend.routers.history import EmailStatus, get_email_history

        result = get_email_history(
            page=1, per_page=50, status=EmailStatus.FORWARDED, session=session
        )

        assert len(result["emails"]) == 2
        for email in result["emails"]:
            assert email.status == "forwarded"

    def test_valid_status_blocked(self, session: Session, sample_emails):
        """Test filtering with valid 'blocked' status"""
        from backend.routers.history import EmailStatus, get_email_history

        result = get_email_history(
            page=1, per_page=50, status=EmailStatus.BLOCKED, session=session
        )

        assert len(result["emails"]) == 1
        assert result["emails"][0].status == "blocked"


def test_create_processing_run(session: Session):
    """Test creating a processing run record"""
    run = ProcessingRun(
        started_at=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc),
        emails_checked=10,
        emails_processed=3,
        emails_forwarded=2,
        status="completed",
        check_interval_minutes=60,
    )
    session.add(run)
    session.commit()
    session.refresh(run)

    assert run.id is not None
    assert run.emails_checked == 10
    assert run.emails_processed == 3
    assert run.emails_forwarded == 2
    assert run.status == "completed"
    assert run.check_interval_minutes == 60


def test_processing_run_with_no_emails(session: Session):
    """Test processing run when no emails are found"""
    run = ProcessingRun(
        started_at=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc),
        emails_checked=0,
        emails_processed=0,
        emails_forwarded=0,
        status="completed",
        check_interval_minutes=30,
    )
    session.add(run)
    session.commit()
    session.refresh(run)

    assert run.id is not None
    assert run.emails_checked == 0
    assert run.emails_processed == 0
    assert run.emails_forwarded == 0
    assert run.status == "completed"


def test_processing_run_with_error(session: Session):
    """Test processing run with error"""
    run = ProcessingRun(
        started_at=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc),
        emails_checked=5,
        emails_processed=0,
        emails_forwarded=0,
        status="error",
        error_message="SMTP connection failed",
        check_interval_minutes=60,
    )
    session.add(run)
    session.commit()
    session.refresh(run)

    assert run.id is not None
    assert run.status == "error"
    assert run.error_message == "SMTP connection failed"


def test_get_processing_runs(session: Session):
    """Test retrieving processing runs via API"""
    from datetime import timedelta

    base_time = datetime.now(timezone.utc)

    # Create multiple runs with explicitly different timestamps
    for i in range(5):
        run = ProcessingRun(
            started_at=base_time + timedelta(seconds=i),
            completed_at=base_time + timedelta(seconds=i, milliseconds=500),
            emails_checked=i,
            emails_processed=0,
            emails_forwarded=0,
            status="completed",
            check_interval_minutes=60,
        )
        session.add(run)
    session.commit()

    # Get runs using the router function
    runs = history.get_processing_runs(limit=10, skip=0, session=session)

    assert len(runs) == 5
    # Runs should be in descending order by started_at (most recent first)
    for i in range(len(runs) - 1):
        assert runs[i].started_at >= runs[i + 1].started_at


def test_get_specific_processing_run(session: Session):
    """Test retrieving a specific processing run by ID"""
    run = ProcessingRun(
        started_at=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc),
        emails_checked=10,
        emails_processed=5,
        emails_forwarded=3,
        status="completed",
        check_interval_minutes=45,
    )
    session.add(run)
    session.commit()
    session.refresh(run)

    # Get the run by ID
    assert run.id is not None
    retrieved_run = history.get_processing_run(run.id, session=session)

    assert retrieved_run.id == run.id
    assert retrieved_run.emails_checked == 10
    assert retrieved_run.emails_processed == 5
    assert retrieved_run.emails_forwarded == 3
    assert retrieved_run.check_interval_minutes == 45


def test_get_nonexistent_processing_run(session: Session):
    """Test retrieving a processing run that doesn't exist"""
    # Try to get a run that doesn't exist
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc_info:
        history.get_processing_run(999, session=session)

    assert exc_info.value.status_code == 404
    assert "not found" in str(exc_info.value.detail).lower()


def test_processing_run_pagination(session: Session):
    """Test pagination of processing runs"""
    # Create 10 runs
    for i in range(10):
        run = ProcessingRun(
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
            emails_checked=i,
            emails_processed=0,
            emails_forwarded=0,
            status="completed",
            check_interval_minutes=60,
        )
        session.add(run)
    session.commit()

    # Get first 5 runs
    first_page = history.get_processing_runs(limit=5, skip=0, session=session)
    assert len(first_page) == 5

    # Get next 5 runs
    second_page = history.get_processing_runs(limit=5, skip=5, session=session)
    assert len(second_page) == 5

    # Verify no overlap
    first_ids = {run.id for run in first_page}
    second_ids = {run.id for run in second_page}
    assert len(first_ids.intersection(second_ids)) == 0


class TestHistoryReprocess:
    """Test reprocessing endpoints"""

    def test_reprocess_all_ignored(self, session: Session, monkeypatch):
        # Create an ignored email within 24 hours with encrypted body
        from backend.security import encrypt_content

        now = datetime.now(timezone.utc)
        email = ProcessedEmail(
            email_id="ignored1",
            subject="Ignored Subject",
            sender="news@example.com",
            received_at=now - timedelta(hours=1),
            status="ignored",
            encrypted_body=encrypt_content("This is a receipt that was ignored"),
            account_email="test@example.com",
        )
        session.add(email)
        session.commit()

        # Mock dependencies
        monkeypatch.setenv("WIFE_EMAIL", "wife@example.com")
        with patch(
            "backend.services.detector.ReceiptDetector.is_receipt", return_value=True
        ), patch(
            "backend.services.detector.ReceiptDetector.categorize_receipt",
            return_value="Shopping",
        ), patch(
            "backend.services.forwarder.EmailForwarder.forward_email", return_value=True
        ):

            from backend.routers.history import reprocess_all_ignored

            result = reprocess_all_ignored(session=session)

            assert result["reprocessed"] == 1
            session.refresh(email)
            assert email.status == "forwarded"
            assert email.category == "Shopping"

    def test_reprocess_specific_email(self, session: Session, monkeypatch):
        from backend.security import encrypt_content

        now = datetime.now(timezone.utc)
        email = ProcessedEmail(
            email_id="spec1",
            subject="Manual Reprocess",
            sender="manual@example.com",
            received_at=now,
            status="ignored",
            encrypted_body=encrypt_content("Body content"),
            account_email="test@example.com",
        )
        session.add(email)
        session.commit()

        with patch(
            "backend.services.detector.ReceiptDetector.is_receipt", return_value=True
        ), patch(
            "backend.services.forwarder.EmailForwarder.forward_email", return_value=True
        ):

            from backend.routers.history import reprocess_email

            assert email.id is not None
            result = reprocess_email(email_id=email.id, session=session)

            assert "analysis" in result
            assert result["suggested_status"] == "forwarded"

    def test_submit_feedback(self, session: Session):
        now = datetime.now(timezone.utc)
        email = ProcessedEmail(
            email_id="feedback1",
            subject="Feedback needed",
            sender="feedback@example.com",
            received_at=now,
            status="blocked",  # Added status
            account_email="test@example.com",
        )
        session.add(email)
        session.commit()

        from backend.routers.history import submit_feedback

        assert email.id is not None
        result = submit_feedback(email_id=email.id, is_receipt=True, session=session)

        assert result["status"] == "success"

        # Check if shadow rule was created
        from backend.models import ManualRule

        rule = session.exec(select(ManualRule).where(ManualRule.is_shadow_mode)).first()
        assert rule is not None
        assert rule.email_pattern == "*@example.com"

    def test_reprocess_email_not_found(self, session: Session):
        """Test reprocessing a non-existent email"""
        from backend.routers.history import reprocess_email
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            reprocess_email(email_id=99999, session=session)

        assert exc_info.value.status_code == 404
        assert "Email not found" in exc_info.value.detail

    def test_reprocess_email_imap_fallback_no_credentials(self, session: Session):
        """Test reprocessing email when encrypted body is missing and no IMAP credentials"""
        now = datetime.now(timezone.utc)
        email = ProcessedEmail(
            email_id="no_body_email",
            subject="Email without body",
            sender="test@example.com",
            received_at=now,
            status="ignored",
            account_email="unknown@example.com",
            # No encrypted_body or encrypted_html
        )
        session.add(email)
        session.commit()

        from backend.routers.history import reprocess_email
        from fastapi import HTTPException

        assert email.id is not None
        with patch(
            "backend.services.email_service.EmailService.get_credentials_for_account",
            return_value=None,
        ):
            with pytest.raises(HTTPException) as exc_info:
                reprocess_email(email_id=email.id, session=session)

            assert exc_info.value.status_code == 400
            assert "Credentials missing" in exc_info.value.detail

    def test_reprocess_email_imap_fallback_email_not_found(self, session: Session):
        """Test reprocessing email when IMAP fetch returns None"""
        now = datetime.now(timezone.utc)
        email = ProcessedEmail(
            email_id="missing_imap_email",
            subject="Email not in IMAP",
            sender="test@example.com",
            received_at=now,
            status="ignored",
            account_email="test@example.com",
            # No encrypted_body or encrypted_html
        )
        session.add(email)
        session.commit()

        from backend.routers.history import reprocess_email
        from fastapi import HTTPException

        assert email.id is not None
        with patch(
            "backend.services.email_service.EmailService.get_credentials_for_account",
            return_value=MOCK_IMAP_CREDENTIALS,
        ), patch(
            "backend.services.email_service.EmailService.fetch_email_by_id",
            return_value=None,
        ):
            with pytest.raises(HTTPException) as exc_info:
                reprocess_email(email_id=email.id, session=session)

            assert exc_info.value.status_code == 404
            assert "Email not found in IMAP inbox" in exc_info.value.detail

    def test_reprocess_email_imap_fallback_success(self, session: Session):
        """Test successful IMAP fallback when encrypted body is missing"""
        now = datetime.now(timezone.utc)
        email = ProcessedEmail(
            email_id="imap_fallback_success",
            subject="IMAP Fallback Test",
            sender="test@example.com",
            received_at=now,
            status="ignored",
            account_email="test@example.com",
            # No encrypted_body or encrypted_html
        )
        session.add(email)
        session.commit()

        from backend.routers.history import reprocess_email

        mock_fetched = {"body": "Fetched body content", "html_body": "<p>HTML</p>"}

        assert email.id is not None
        with patch(
            "backend.services.email_service.EmailService.get_credentials_for_account",
            return_value=MOCK_IMAP_CREDENTIALS,
        ), patch(
            "backend.services.email_service.EmailService.fetch_email_by_id",
            return_value=mock_fetched,
        ), patch(
            "backend.services.detector.ReceiptDetector.debug_is_receipt",
            return_value={"final_decision": True},
        ), patch(
            "backend.services.detector.ReceiptDetector.categorize_receipt",
            return_value="shopping",
        ):
            result = reprocess_email(email_id=email.id, session=session)

            assert result["suggested_status"] == "forwarded"
            assert result["category"] == "shopping"

    def test_submit_feedback_email_not_found(self, session: Session):
        """Test submitting feedback for a non-existent email"""
        from backend.routers.history import submit_feedback
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            submit_feedback(email_id=99999, is_receipt=True, session=session)

        assert exc_info.value.status_code == 404
        assert "Email not found" in exc_info.value.detail
