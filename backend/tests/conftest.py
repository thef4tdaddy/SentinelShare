import os

import pytest

# Force SQLite for all tests by unsetting DATABASE_URL before any backend code is imported
os.environ["DATABASE_URL"] = ""
os.environ["TESTING"] = "1"


# Set common environment variables for all backend tests
@pytest.fixture(autouse=True)
def test_env_setup():
    os.environ["SECRET_KEY"] = "cpUbNMiXWufM3gAPx1arHE1h7Y72s9sBri-MDiWtwb4="

    os.environ["POLL_INTERVAL"] = "30"
    os.environ["WIFE_EMAIL"] = "wife@example.com"
    os.environ["GMAIL_EMAIL"] = "test@example.com"
    os.environ["GMAIL_PASSWORD"] = "password"
    yield
