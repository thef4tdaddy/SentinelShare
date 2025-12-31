import hashlib
import hmac
import time

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from backend.main import app


@pytest.fixture(name="engine")
def engine_fixture():
    """Create an in-memory database engine for testing"""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture(name="session")
def session_fixture(engine):
    """Create an in-memory database session for testing"""
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session):
    """Create a test client with mocked dependencies"""

    def get_session_override():
        return session

    from backend.database import get_session

    app.dependency_overrides[get_session] = get_session_override

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def test_quick_action_public_access(monkeypatch, client, engine):
    """
    Regression test for Public Action Links (STOP, MORE, SETTINGS).
    Ensures that these endpoints can be accessed WITHOUT authentication
    (i.e., NO dashboard token, NO session cookie), relying only on 'sig'.
    """
    # 1. Setup Secret
    secret = "test-secret"
    # We must patch os.environ for the app to see it if it reads per request,
    # or ensure backend.security reads it properly.
    # The generates_hmac_signature uses os.getenv("SECRET_KEY"), so patching os.environ works.
    monkeypatch.setenv("SECRET_KEY", secret)

    # Also force DASHBOARD_PASSWORD to ensure auth middleware is active
    monkeypatch.setenv("DASHBOARD_PASSWORD", "supersecret")

    # 2. Generate Valid Link
    ts = str(time.time())
    cmd = "STOP"
    arg = "spam.com"
    msg = f"{cmd}:{arg}:{ts}"
    sig = hmac.new(secret.encode(), msg.encode(), hashlib.sha256).hexdigest()

    # 3. Patch the engine used by CommandService to use the test engine
    # Using monkeypatch for cleaner test setup
    import backend.services.command_service as cmd_service

    monkeypatch.setattr(cmd_service, "engine", engine)

    # 4. Request without Auth
    # No cookies, no 'token' query param
    url = f"/api/actions/quick?cmd={cmd}&arg={arg}&ts={ts}&sig={sig}"
    response = client.get(url)

    # 5. Verify Success (Not 401)
    # It should return 200 OK because the signature is valid
    assert (
        response.status_code == 200
    ), f"Expected 200, got {response.status_code}. Middleware might be blocking."
    assert "Successfully Blocked" in response.text


def test_preferences_update_public_access(monkeypatch, client):
    """
    Ensure /api/actions/update-preferences is also whitelisted.
    This uses a token in the BODY, not query param, so middleware needs to let it through.
    """
    monkeypatch.setenv("DASHBOARD_PASSWORD", "supersecret")

    # Does this endpoint require a token in the body to be valid?
    # Yes, verify_dashboard_token check. But middleware should pass it to the router.
    # If we send garbage token, router returns 403. Middleware returns 401.

    response = client.post(
        "/api/actions/update-preferences",
        json={"token": "invalid-token", "blocked_senders": [], "allowed_senders": []},
    )

    # Expect 403 (Invalid Token from Router), NOT 401 (Middleware Block)
    assert (
        response.status_code == 403
    ), f"Expected 403 from Router, got {response.status_code}"
