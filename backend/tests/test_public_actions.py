import hashlib
import hmac
import time

from backend.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_quick_action_public_access(monkeypatch):
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

    # 3. Request without Auth
    # No cookies, no 'token' query param
    url = f"/api/actions/quick?cmd={cmd}&arg={arg}&ts={ts}&sig={sig}"
    response = client.get(url)

    # 4. Verify Success (Not 401)
    # It should return 200 OK because the signature is valid
    assert (
        response.status_code == 200
    ), f"Expected 200, got {response.status_code}. Middleware might be blocking."
    assert "Successfully Blocked" in response.text


def test_preferences_update_public_access(monkeypatch):
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
