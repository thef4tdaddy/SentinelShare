import os

import pytest


# Set common environment variables for all backend tests
@pytest.fixture(autouse=True)
def test_env_setup():
    os.environ["SECRET_KEY"] = "cpUbNMiXWufM3gAPx1arHE1h7Y72s9sBri-MDiWtwb4="
    os.environ["POLL_INTERVAL"] = "30"
    os.environ["WIFE_EMAIL"] = "wife@example.com"
    os.environ["GMAIL_EMAIL"] = "test@example.com"
    os.environ["GMAIL_PASSWORD"] = "password"
    yield
