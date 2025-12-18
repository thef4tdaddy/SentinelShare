from datetime import datetime, timezone

import pytest
from backend.main import app
from backend.models import ProcessedEmail
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

client = TestClient(app)


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


def test_get_dashboard_stats(session: Session):
    # Mock dependencies to use our test session
    from backend.database import get_session

    app.dependency_overrides[get_session] = lambda: session

    # Add dummy data
    now = datetime.now(timezone.utc)
    email = ProcessedEmail(
        email_id="dash1",
        subject="Test",
        sender="s@t.com",
        received_at=now,
        status="forwarded",
        amount=10.0,
    )
    session.add(email)
    session.commit()

    response = client.get("/api/dashboard/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["total_forwarded"] == 1
    assert data["total_processed"] == 1

    app.dependency_overrides.clear()


def test_get_dashboard_activity(session: Session):
    from backend.database import get_session

    app.dependency_overrides[get_session] = lambda: session

    now = datetime.now(timezone.utc)
    email = ProcessedEmail(
        email_id="dash2",
        subject="Activity",
        sender="s@t.com",
        received_at=now,
        status="forwarded",
    )
    session.add(email)
    session.commit()

    response = client.get("/api/dashboard/activity")
    assert response.status_code == 200
    assert len(response.json()) == 1

    app.dependency_overrides.clear()
