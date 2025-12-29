import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

from backend.main import app
from backend.models import LearningCandidate, ManualRule


@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        # Dependency override to force API to use this test session
        from backend.database import get_session

        # Override must be set here so it applies to client created later
        app.dependency_overrides[get_session] = lambda: session

        yield session

    app.dependency_overrides.clear()


@pytest.fixture(name="client")
def client_fixture(session):
    """Create a test client that uses the session fixture's app overrides"""
    # The session fixture sets up the overrides on the global app object
    with TestClient(app) as client:
        yield client


def test_approve_candidate_api(session: Session, client: TestClient, monkeypatch):
    # Set dashboard password for auth
    monkeypatch.setenv("DASHBOARD_PASSWORD", "testpass")

    # Create a candidate
    candidate = LearningCandidate(
        sender="xbox@microsoft.com",
        subject_pattern="*Game Pass*",
        confidence=0.9,
        type="Receipt",
    )
    session.add(candidate)
    session.commit()
    session.refresh(candidate)

    # Authenticate via login
    client.post("/api/auth/login", json={"password": "testpass"})

    # Call Approve endpoint
    response = client.post(f"/api/learning/approve/{candidate.id}")
    assert response.status_code == 200

    # Verify Rule Created
    rule = session.exec(
        select(ManualRule).where(ManualRule.email_pattern == "*xbox@microsoft.com*")
    ).first()
    assert rule is not None
    assert rule.subject_pattern == "*Game Pass*"
    assert rule.is_shadow_mode is False

    # Verify Candidate Deleted
    deleted_candidate = session.get(LearningCandidate, candidate.id)
    assert deleted_candidate is None


def test_ignore_candidate_api(session: Session, client: TestClient, monkeypatch):
    monkeypatch.setenv("DASHBOARD_PASSWORD", "testpass")

    candidate = LearningCandidate(
        sender="spam@spam.com", subject_pattern="*Spam*", confidence=0.1
    )
    session.add(candidate)
    session.commit()

    # Authenticate via login
    client.post("/api/auth/login", json={"password": "testpass"})

    response = client.delete(f"/api/learning/ignore/{candidate.id}")
    assert response.status_code == 200

    assert session.get(LearningCandidate, candidate.id) is None
