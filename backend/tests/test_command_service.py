import os
from unittest.mock import patch

import pytest
from backend.database import engine
from backend.models import Preference
from backend.services.command_service import CommandService
from sqlmodel import Session, SQLModel, select


# Setup in-memory DB for tests
@pytest.fixture(name="session")
def session_fixture():
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    SQLModel.metadata.drop_all(engine)


class TestCommandService:

    @patch.dict(os.environ, {"WIFE_EMAIL": "sara@example.com"})
    def test_is_command_email(self):
        # Match
        assert CommandService.is_command_email({"from": "sara@example.com"}) is True
        assert (
            CommandService.is_command_email({"from": "Sara@Example.com"}) is True
        )  # Case insensitive
        assert (
            CommandService.is_command_email({"from": "Sara <sara@example.com>"}) is True
        )

        # No Match
        assert CommandService.is_command_email({"from": "sender@store.com"}) is False
        assert CommandService.is_command_email({"from": ""}) is False

    @patch.dict(os.environ, {"WIFE_EMAIL": "sara@example.com"})
    @patch("backend.services.command_service.CommandService._send_confirmation")
    def test_process_stop_command(self, mock_send, session):
        email_data = {
            "from": "sara@example.com",
            "subject": "Re: Fwd: Receipt",
            "body": "STOP amazon\nSent from my iPhone",
        }

        result = CommandService.process_command(email_data)
        assert result is True

        # Verify DB
        pref = session.exec(
            select(Preference).where(Preference.item == "amazon")
        ).first()
        assert pref is not None
        assert pref.type == "Blocked Sender"

        mock_send.assert_called_once()
        assert "Blocked sender/category: amazon" in mock_send.call_args[0][0]

    @patch.dict(os.environ, {"WIFE_EMAIL": "sara@example.com"})
    @patch("backend.services.command_service.CommandService._send_confirmation")
    def test_process_more_command(self, mock_send, session):
        # Test cleaning args too
        email_data = {"from": "sara@example.com", "body": "MORE  starbucks "}

        result = CommandService.process_command(email_data)
        assert result is True

        pref = session.exec(
            select(Preference).where(Preference.item == "starbucks")
        ).first()
        assert pref is not None
        assert pref.type == "Always Forward"

    @patch.dict(os.environ, {"WIFE_EMAIL": "sara@example.com"})
    @patch("backend.services.command_service.CommandService._send_confirmation")
    def test_process_settings_command(self, mock_send, session):
        # Pre-seed DB
        session.add(Preference(item="uber", type="Blocked Category"))
        session.commit()

        email_data = {"from": "sara@example.com", "body": "SETTINGS"}

        result = CommandService.process_command(email_data)
        assert result is True

        mock_send.assert_called_once()
        msg = mock_send.call_args[0][0]
        assert "Blocked Category: uber" in msg

    @patch.dict(os.environ, {"WIFE_EMAIL": "sara@example.com"})
    def test_ignore_no_command(self, session):
        email_data = {"from": "sara@example.com", "body": "Hey honey, check this out"}

        result = CommandService.process_command(email_data)
        assert result is False

        prefs = session.exec(select(Preference)).all()
        assert len(prefs) == 0
