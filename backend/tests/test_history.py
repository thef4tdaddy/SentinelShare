from datetime import datetime, timedelta

import pytest
from backend.models import ProcessedEmail, ProcessingRun
from backend.routers import history
from backend.routers.history import router
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool


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
    now = datetime.utcnow()

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

        result = get_recent_runs(session=session)

        assert "runs" in result
        assert len(result["runs"]) == 0

    def test_get_recent_runs_with_emails(self, session: Session, sample_emails):
        """Test getting recent runs with sample emails"""
        from backend.routers.history import get_recent_runs

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
        assert total_blocked == 2
        assert total_errors == 1


class TestHistoryDateFiltering:
    """Test date filtering functionality"""

    def test_filter_emails_by_date_from(self, session: Session, sample_emails):
        """Test filtering emails by date_from parameter"""
        from backend.routers.history import get_email_history

        now = datetime.utcnow()
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

        now = datetime.utcnow()
        date_to = (now - timedelta(minutes=35)).isoformat()

        result = get_email_history(
            page=1, per_page=50, date_to=date_to, session=session
        )

        # Should only include email4 and email5 (older than 35 minutes)
        assert len(result["emails"]) == 2

    def test_filter_emails_by_date_range(self, session: Session, sample_emails):
        """Test filtering emails by both date_from and date_to"""
        from backend.routers.history import get_email_history

        now = datetime.utcnow()
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

        now = datetime.utcnow()
        date_from = (now - timedelta(minutes=25)).isoformat()

        result = get_history_stats(date_from=date_from, session=session)

        # Should only count email1 and email2
        assert result["total"] == 2
        assert result["forwarded"] == 1
        assert result["blocked"] == 1

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
        started_at=datetime.utcnow(),
        completed_at=datetime.utcnow(),
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
        started_at=datetime.utcnow(),
        completed_at=datetime.utcnow(),
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
        started_at=datetime.utcnow(),
        completed_at=datetime.utcnow(),
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

    base_time = datetime.utcnow()

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
        started_at=datetime.utcnow(),
        completed_at=datetime.utcnow(),
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
    retrieved_run = history.get_processing_run(run.id, session=session)

    assert retrieved_run.id == run.id
    assert retrieved_run.emails_checked == 10
    assert retrieved_run.emails_processed == 5
    assert retrieved_run.emails_forwarded == 3
    assert retrieved_run.check_interval_minutes == 45


def test_get_nonexistent_processing_run(session: Session):
    """Test retrieving a processing run that doesn't exist"""
    # Try to get a run that doesn't exist
    with pytest.raises(Exception) as exc_info:
        history.get_processing_run(999, session=session)

    assert exc_info.value.status_code == 404
    assert "not found" in exc_info.value.detail.lower()


def test_processing_run_pagination(session: Session):
    """Test pagination of processing runs"""
    # Create 10 runs
    for i in range(10):
        run = ProcessingRun(
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
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
