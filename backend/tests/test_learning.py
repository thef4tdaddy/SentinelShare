from unittest.mock import patch

import pytest
from backend.main import app
from backend.models import LearningCandidate, ManualRule
from backend.services.learning_service import LearningService
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select


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


# Mock Email Data
MOCK_EMAILS = [
    {
        "message_id": "msg_1",
        "subject": "Payment Receipt for Game Pass",
        "body": "Thank you for your payment of $15.00",
        "from": "xbox@microsoft.com",
    },
    {
        "message_id": "msg_2",
        "subject": "Unknown Email",
        "body": "Just saying hi",
        "from": "friend@gmail.com",
    },
    {
        "message_id": "msg_3",
        "subject": "Your receipt for order #123456",
        "body": "Order #123456 confirmed.",
        "from": "store@shop.com",
    },
]


def test_scan_history_logic(session: Session):
    # Mock EmailService and ReceiptDetector
    with patch(
        "backend.services.email_service.EmailService.fetch_recent_emails"
    ) as mock_fetch:
        with patch(
            "backend.services.email_service.EmailService.get_all_accounts"
        ) as mock_accounts:
            # Setup mocks
            mock_accounts.return_value = [
                {"email": "test@test.com", "password": "pw", "provider": "gmail"}
            ]
            mock_fetch.return_value = MOCK_EMAILS

            # Run Scan
            count = LearningService.scan_history(session, days=30)

            # Verify results
            assert count == 2  # Should find Xbox and Shop (friend is ignored)

            candidates = session.exec(select(LearningCandidate)).all()
            assert len(candidates) == 2

            xbox = next(c for c in candidates if "microsoft" in c.sender)
            assert xbox.confidence > 0.5
            assert xbox.type == "Receipt"


def test_scan_deduplication(session: Session):
    with patch(
        "backend.services.email_service.EmailService.fetch_recent_emails"
    ) as mock_fetch:
        with patch(
            "backend.services.email_service.EmailService.get_all_accounts"
        ) as mock_accounts:
            mock_accounts.return_value = [
                {"email": "test@test.com", "password": "pw", "provider": "gmail"}
            ]
            # Return same email twice (simulating multiple similar receipts)
            mock_fetch.return_value = [MOCK_EMAILS[0], MOCK_EMAILS[0]]

            LearningService.scan_history(session, days=30)

            # Should create 1 candidate with 2 matches
            candidates = session.exec(select(LearningCandidate)).all()
            assert len(candidates) == 1
            assert candidates[0].matches == 2


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
