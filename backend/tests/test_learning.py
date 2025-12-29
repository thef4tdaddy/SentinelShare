import logging
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

from backend.main import app
from backend.models import LearningCandidate, ManualRule
from backend.routers.learning import run_scan_wrapper


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


def test_get_candidates_api(session: Session, client: TestClient, monkeypatch):
    """Test the GET /api/learning/candidates endpoint"""
    monkeypatch.setenv("DASHBOARD_PASSWORD", "testpass")

    # Create multiple candidates
    candidate1 = LearningCandidate(
        sender="store1@example.com",
        subject_pattern="*Order*",
        confidence=0.8,
        type="Receipt",
    )
    session.add(candidate1)
    session.commit()
    session.refresh(candidate1)

    # Create second candidate slightly later to ensure different created_at
    candidate2 = LearningCandidate(
        sender="store2@example.com",
        subject_pattern="*Invoice*",
        confidence=0.9,
        type="Receipt",
    )
    session.add(candidate2)
    session.commit()
    session.refresh(candidate2)

    # Authenticate via login
    client.post("/api/auth/login", json={"password": "testpass"})

    # Call GET candidates endpoint
    response = client.get("/api/learning/candidates")
    assert response.status_code == 200

    candidates = response.json()
    assert len(candidates) == 2
    # Verify they are ordered by created_at desc (most recent first)
    # candidate2 was created after candidate1, so it should be first
    assert candidates[0]["sender"] == "store2@example.com"
    assert candidates[1]["sender"] == "store1@example.com"


def test_approve_candidate_not_found(session: Session, client: TestClient, monkeypatch):
    """Test approve endpoint with non-existent candidate_id (covers line 55)"""
    monkeypatch.setenv("DASHBOARD_PASSWORD", "testpass")

    # Authenticate via login
    client.post("/api/auth/login", json={"password": "testpass"})

    # Try to approve a non-existent candidate
    response = client.post("/api/learning/approve/99999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Candidate not found"


def test_ignore_candidate_not_found(session: Session, client: TestClient, monkeypatch):
    """Test ignore endpoint with non-existent candidate_id (covers line 86)"""
    monkeypatch.setenv("DASHBOARD_PASSWORD", "testpass")

    # Authenticate via login
    client.post("/api/auth/login", json={"password": "testpass"})

    # Try to ignore a non-existent candidate
    response = client.delete("/api/learning/ignore/99999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Candidate not found"


def test_scan_history_api(session: Session, client: TestClient, monkeypatch):
    """Test the POST /api/learning/scan endpoint (covers lines 34-35)"""
    monkeypatch.setenv("DASHBOARD_PASSWORD", "testpass")

    # Authenticate via login
    client.post("/api/auth/login", json={"password": "testpass"})

    # Mock the background_tasks.add_task to verify it's called
    with patch("fastapi.BackgroundTasks.add_task") as mock_add_task:
        # Call scan endpoint
        response = client.post("/api/learning/scan?days=7")
        assert response.status_code == 200

        data = response.json()
        assert data["message"] == "Scan started in background"
        assert data["days"] == 7

        # Verify the background task was added with correct parameters
        mock_add_task.assert_called_once()
        # Check that run_scan_wrapper was passed as the task
        call_args = mock_add_task.call_args
        assert call_args[0][0].__name__ == "run_scan_wrapper"
        assert call_args[0][1] == 7  # days parameter


def test_run_scan_wrapper_success(caplog):
    """Test run_scan_wrapper with successful scan (covers lines 17-20)"""
    # Mock LearningService.scan_history to return a count
    with patch("backend.routers.learning.LearningService.scan_history") as mock_scan:
        mock_scan.return_value = 5

        with caplog.at_level(logging.INFO):
            run_scan_wrapper(days=7)

        # Verify the success log message
        assert "Background Scan Complete" in caplog.text
        assert "Found 5 new candidates" in caplog.text
        mock_scan.assert_called_once()


def test_run_scan_wrapper_error(caplog):
    """Test run_scan_wrapper with exception (covers lines 21-22)"""
    # Mock LearningService.scan_history to raise an exception
    with patch("backend.routers.learning.LearningService.scan_history") as mock_scan:
        mock_scan.side_effect = Exception("Test error")

        with caplog.at_level(logging.ERROR):
            run_scan_wrapper(days=7)

        # Verify the error log message
        assert "Background Scan Failed" in caplog.text
        assert "Test error" in caplog.text
        mock_scan.assert_called_once()
