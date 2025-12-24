import os
from unittest.mock import MagicMock, patch

import pytest
from sqlmodel import Session, SQLModel, select

from backend.database import engine
from backend.models import Preference
from backend.services.command_service import CommandService


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

    @patch.dict(os.environ, {}, clear=True)
    def test_is_command_email_no_wife_email(self):
        """Test line 18: Return False when WIFE_EMAIL env var is not set"""
        assert CommandService.is_command_email({"from": "anyone@example.com"}) is False

    @patch.dict(os.environ, {"WIFE_EMAIL": "sara@example.com"})
    @patch("backend.services.command_service.CommandService._send_confirmation")
    def test_process_command_empty_body_only(self, mock_send, session):
        """Test line 40: Handle empty lines in email body with no commands"""
        # Test with body that has ONLY empty lines (no commands)
        email_data = {
            "from": "sara@example.com",
            "body": "\n\n   \n\n",  # Only empty lines
        }
        result = CommandService.process_command(email_data)
        assert result is False  # No command executed
        mock_send.assert_not_called()

    @patch.dict(os.environ, {"WIFE_EMAIL": "sara@example.com"})
    @patch("backend.services.command_service.CommandService._send_confirmation")
    def test_process_command_with_surrounding_empty_lines(self, mock_send, session):
        """Test line 40: Handle empty lines surrounding commands (line 45 is unreachable)"""
        # Test with body that has empty lines mixed with command
        email_data = {
            "from": "sara@example.com",
            "body": "\n\n   \n\nSTOP test\n   \n",  # Empty lines before and after
        }
        result = CommandService.process_command(email_data)
        assert result is True

        # Verify the command was processed despite empty lines
        pref = session.exec(select(Preference).where(Preference.item == "test")).first()
        assert pref is not None
        mock_send.assert_called_once()

    @patch.dict(os.environ, {"WIFE_EMAIL": "sara@example.com"})
    @patch("backend.services.command_service.CommandService._send_confirmation")
    def test_add_preference_duplicate(self, mock_send, session, capsys):
        """Test line 89: Adding a duplicate preference"""
        # First add
        email_data = {"from": "sara@example.com", "body": "STOP walmart"}
        CommandService.process_command(email_data)

        # Try to add the same preference again
        CommandService._add_preference("walmart", "Blocked Sender")

        # Check that duplicate message was printed
        captured = capsys.readouterr()
        assert "Preference already exists" in captured.out

        # Ensure confirmation was sent only for the first add via process_command
        mock_send.assert_called_once()

    @patch.dict(
        os.environ,
        {
            "WIFE_EMAIL": "sara@example.com",
            "GMAIL_EMAIL": "sender@example.com",
            "GMAIL_PASSWORD": "testpass",
        },
    )
    @patch("smtplib.SMTP")
    def test_send_confirmation(self, mock_smtp):
        """Test lines 93-127: _send_confirmation email sending"""
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        CommandService._send_confirmation("Test message")

        # Verify SMTP was called correctly
        mock_smtp.assert_called_once_with("smtp.gmail.com", 587)
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with("sender@example.com", "testpass")
        mock_server.send_message.assert_called_once()

    @patch.dict(os.environ, {}, clear=True)
    @patch("smtplib.SMTP")
    def test_send_confirmation_no_wife_email(self, mock_smtp):
        """Test lines 94-95: _send_confirmation returns early when no WIFE_EMAIL"""
        # Should return early without trying to send
        CommandService._send_confirmation("Test message")
        # Explicitly verify that no SMTP connection was attempted
        mock_smtp.assert_not_called()

    @patch.dict(
        os.environ,
        {
            "WIFE_EMAIL": "sara@example.com",
            "GMAIL_EMAIL": "sender@example.com",
            "GMAIL_PASSWORD": "testpass",
        },
    )
    @patch("smtplib.SMTP")
    def test_send_confirmation_failure(self, mock_smtp, capsys):
        """Test lines 126-127: _send_confirmation exception handling"""
        mock_smtp.side_effect = Exception("Connection failed")

        CommandService._send_confirmation("Test message")

        # Check that error was printed
        captured = capsys.readouterr()
        assert "Failed to send confirmation" in captured.out

    @patch.dict(os.environ, {"WIFE_EMAIL": "sara@example.com"})
    @patch("backend.services.command_service.CommandService._send_confirmation")
    def test_send_settings_summary_empty(self, mock_send, session):
        """Test line 139: _send_settings_summary with no preferences"""
        CommandService._send_settings_summary()

        mock_send.assert_called_once()
        msg = mock_send.call_args[0][0]
        assert "No active preferences" in msg
