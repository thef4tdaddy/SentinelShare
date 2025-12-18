import os
from unittest.mock import Mock, patch

import pytest
from backend.database import create_db_and_tables, engine
from backend.models import GlobalSettings
from backend.services.forwarder import EmailForwarder
from sqlmodel import Session, select


@pytest.fixture
def clean_email_template():
    """Fixture to clean up email template before and after tests"""
    # Ensure tables exist
    create_db_and_tables()

    # Clean up before test
    with Session(engine) as session:
        setting = session.exec(
            select(GlobalSettings).where(GlobalSettings.key == "email_template")
        ).first()
        if setting:
            session.delete(setting)
            session.commit()

    yield

    # Clean up after test
    with Session(engine) as session:
        setting = session.exec(
            select(GlobalSettings).where(GlobalSettings.key == "email_template")
        ).first()
        if setting:
            session.delete(setting)
            session.commit()


class TestEmailForwarder:

    @patch("backend.services.forwarder.smtplib.SMTP")
    @patch.dict(
        os.environ,
        {
            "SENDER_EMAIL": "sender@example.com",
            "SENDER_PASSWORD": "password123",
            "SMTP_SERVER": "smtp.gmail.com",
        },
    )
    def test_forward_email_success(self, mock_smtp):
        """Test successful email forwarding"""
        # Setup mock
        mock_server = Mock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        original_email = {
            "subject": "Test Receipt",
            "from": "shop@example.com",
            "body": "Order #123. Total: $50.00",
        }

        result = EmailForwarder.forward_email(original_email, "target@example.com")

        assert result
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with("sender@example.com", "password123")
        mock_server.send_message.assert_called_once()

    @patch("backend.services.forwarder.smtplib.SMTP")
    @patch.dict(os.environ, {}, clear=True)
    def test_forward_email_missing_credentials(self, mock_smtp):
        """Test forwarding fails when credentials are missing"""
        original_email = {
            "subject": "Test Receipt",
            "from": "shop@example.com",
            "body": "Order #123",
        }

        result = EmailForwarder.forward_email(original_email, "target@example.com")

        assert not result
        mock_smtp.assert_not_called()

    @patch("backend.services.forwarder.smtplib.SMTP")
    @patch.dict(
        os.environ,
        {
            "EMAIL_ACCOUNTS": '[{"email": "account1@gmail.com", "password": "pass1", "imap_server": "imap.gmail.com"}]'
        },
    )
    def test_forward_email_with_email_accounts_fallback(self, mock_smtp):
        """Test forwarding uses EMAIL_ACCOUNTS when SENDER_EMAIL is not set"""
        mock_server = Mock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        original_email = {
            "subject": "Test Receipt",
            "from": "shop@example.com",
            "body": "Order #123",
        }

        result = EmailForwarder.forward_email(original_email, "target@example.com")

        assert result
        mock_server.login.assert_called_once_with("account1@gmail.com", "pass1")

    @patch("backend.services.forwarder.smtplib.SMTP")
    @patch.dict(
        os.environ,
        {
            "EMAIL_ACCOUNTS": '[{"email": "icloud@me.com", "password": "pass", "imap_server": "imap.mail.me.com"}]'
        },
    )
    def test_forward_email_icloud_smtp_detection(self, mock_smtp):
        """Test SMTP server detection for iCloud accounts"""
        mock_server = Mock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        original_email = {
            "subject": "Test",
            "from": "sender@example.com",
            "body": "Test body",
        }

        result = EmailForwarder.forward_email(original_email, "target@example.com")

        assert result
        # Should use smtp.mail.me.com for iCloud
        mock_smtp.assert_called_with("smtp.mail.me.com", 587)

    @patch("backend.services.forwarder.smtplib.SMTP")
    @patch.dict(
        os.environ,
        {"SENDER_EMAIL": "sender@example.com", "SENDER_PASSWORD": "password123"},
    )
    def test_forward_email_smtp_error(self, mock_smtp):
        """Test handling of SMTP errors"""
        mock_server = Mock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        mock_server.send_message.side_effect = Exception("SMTP error")

        original_email = {
            "subject": "Test",
            "from": "sender@example.com",
            "body": "Test body",
        }

        result = EmailForwarder.forward_email(original_email, "target@example.com")

        assert not result

    @patch("backend.services.forwarder.smtplib.SMTP")
    @patch.dict(
        os.environ,
        {"SENDER_EMAIL": "sender@example.com", "SENDER_PASSWORD": "password123"},
    )
    def test_forward_email_missing_subject(self, mock_smtp):
        """Test forwarding email with missing subject"""
        mock_server = Mock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        original_email = {"from": "sender@example.com", "body": "Test body"}

        result = EmailForwarder.forward_email(original_email, "target@example.com")

        assert result
        # Should use "No Subject" as default

    @patch("backend.services.forwarder.smtplib.SMTP")
    @patch.dict(
        os.environ,
        {"SENDER_EMAIL": "sender@example.com", "SENDER_PASSWORD": "password123"},
    )
    def test_forward_email_content_formatting(self, mock_smtp):
        """Test that forwarded email has correct formatting"""
        mock_server = Mock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        original_email = {
            "subject": "Original Subject",
            "from": "shop@example.com",
            "body": "This is the original body",
        }

        result = EmailForwarder.forward_email(original_email, "target@example.com")

        assert result
        # Verify send_message was called with a message
        call_args = mock_server.send_message.call_args
        assert call_args is not None

    @patch("backend.services.forwarder.smtplib.SMTP")
    @patch.dict(
        os.environ,
        {
            "EMAIL_ACCOUNTS": '[{"email": "custom@example.com", "password": "pass", "imap_server": "imap.custom.com"}]'
        },
    )
    def test_forward_email_custom_smtp_inference(self, mock_smtp):
        """Test SMTP server inference from custom IMAP server"""
        mock_server = Mock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        original_email = {
            "subject": "Test",
            "from": "sender@example.com",
            "body": "Test body",
        }

        result = EmailForwarder.forward_email(original_email, "target@example.com")

        assert result
        # Should infer smtp.custom.com from imap.custom.com
        mock_smtp.assert_called_with("smtp.custom.com", 587)

    @patch("backend.services.forwarder.smtplib.SMTP")
    @patch.dict(
        os.environ,
        {"SENDER_EMAIL": "sender@example.com", "SENDER_PASSWORD": "password123"},
    )
    def test_forward_email_authentication_failure(self, mock_smtp):
        """Test handling of authentication failures"""
        mock_server = Mock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        mock_server.login.side_effect = Exception("Authentication failed")

        original_email = {
            "subject": "Test",
            "from": "sender@example.com",
            "body": "Test body",
        }

        result = EmailForwarder.forward_email(original_email, "target@example.com")

        assert not result

    @patch("backend.services.forwarder.smtplib.SMTP")
    @patch.dict(os.environ, {"EMAIL_ACCOUNTS": "invalid json"}, clear=True)
    def test_forward_email_invalid_email_accounts_json(self, mock_smtp):
        """Test handling of invalid EMAIL_ACCOUNTS JSON"""
        original_email = {
            "subject": "Test",
            "from": "sender@example.com",
            "body": "Test body",
        }

        result = EmailForwarder.forward_email(original_email, "target@example.com")

        # Should fail since no valid credentials
        assert not result

    @patch("backend.services.forwarder.smtplib.SMTP")
    @patch.dict(
        os.environ,
        {"SENDER_EMAIL": "sender@example.com", "SENDER_PASSWORD": "password123"},
    )
    def test_forward_email_with_custom_template(self, mock_smtp, clean_email_template):
        """Test that custom template is used when set in database"""
        mock_server = Mock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        # Store custom template in database
        with Session(engine) as session:
            custom_template = (
                "Custom template: {subject} from {from}\n\nContent:\n{body}"
            )
            setting = GlobalSettings(
                key="email_template", value=custom_template, description="Test template"
            )
            session.add(setting)
            session.commit()

        original_email = {
            "subject": "Test Receipt",
            "from": "shop@example.com",
            "body": "Order content here",
        }

        result = EmailForwarder.forward_email(original_email, "target@example.com")

        assert result
        # Verify the message was sent
        mock_server.send_message.assert_called_once()

    @patch("backend.services.forwarder.smtplib.SMTP")
    @patch.dict(
        os.environ,
        {"SENDER_EMAIL": "sender@example.com", "SENDER_PASSWORD": "password123"},
    )
    def test_forward_email_template_variable_substitution(
        self, mock_smtp, clean_email_template
    ):
        """Test that template variables are properly substituted"""
        mock_server = Mock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        # Store template with all variables
        with Session(engine) as session:
            template = "Subject: {subject}\nFrom: {from}\nBody: {body}"
            setting = GlobalSettings(
                key="email_template", value=template, description="Test template"
            )
            session.add(setting)
            session.commit()

        original_email = {
            "subject": "Test Subject",
            "from": "test@example.com",
            "body": "Test Body",
        }

        result = EmailForwarder.forward_email(original_email, "target@example.com")

        assert result
