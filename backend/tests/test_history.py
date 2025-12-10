import pytest
from datetime import datetime
from sqlmodel import Session, create_engine, SQLModel, select
from sqlmodel.pool import StaticPool
from backend.models import ProcessingRun
from backend.routers import history


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
    # Create multiple runs
    for i in range(5):
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

    # Get runs using the router function
    runs = history.get_processing_runs(limit=10, skip=0, session=session)
    
    assert len(runs) == 5
    # Runs should be in descending order by started_at
    assert runs[0].id >= runs[-1].id


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
    from fastapi import HTTPException
    import pytest
    
    # Try to get a run that doesn't exist
    with pytest.raises(HTTPException) as exc_info:
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
