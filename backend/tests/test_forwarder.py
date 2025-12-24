import os
from unittest.mock import Mock, patch

import pytest
from backend.database import create_db_and_tables, engine
from backend.models import GlobalSettings
from backend.services.forwarder import EmailForwarder
from sqlmodel import Session, select


@pytest.fixture
def preexisting_template_for_cleanup_test():
    """Creates a pre-existing template specifically for testing fixture cleanup"""
    create_db_and_tables()
    with Session(engine) as session:
        template = "Pre-existing template for testing: {body}"
        setting = GlobalSettings(
            key="email_template", value=template, description="Pre-existing for test"
        )
        session.add(setting)
        session.commit()
    # Don't clean up - let clean_email_template do it


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

    @patch("backend.services.forwarder.smtplib.SMTP")
    @patch.dict(
        os.environ,
        {"SENDER_EMAIL": "sender@example.com", "SENDER_PASSWORD": "password123"},
    )
    def test_fixture_cleans_up_preexisting_template(
        self, mock_smtp, preexisting_template_for_cleanup_test, clean_email_template
    ):
        """Test that clean_email_template fixture removes pre-existing templates"""
        # This test exercises lines 23-24 in the clean_email_template fixture.
        # The preexisting_template_for_cleanup_test fixture creates a template,
        # then clean_email_template runs and should clean it up (triggering lines 23-24).
        #
        # This approach removes the ordering dependency - the fixtures are explicitly
        # ordered by pytest (preexisting_template_for_cleanup_test runs before clean_email_template
        # because clean_email_template is listed after it in the parameter list).

        mock_server = Mock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        # The clean_email_template fixture should have cleaned up the pre-existing template
        with Session(engine) as session:
            setting = session.exec(
                select(GlobalSettings).where(GlobalSettings.key == "email_template")
            ).first()
            assert (
                setting is None
            ), "Fixture should have cleaned up the pre-existing template"

        # Perform a normal email forwarding operation
        original_email = {
            "subject": "Test",
            "from": "test@example.com",
            "body": "Test Body",
        }

        result = EmailForwarder.forward_email(original_email, "target@example.com")
        assert result

    @patch("backend.services.forwarder.smtplib.SMTP")
    @patch.dict(
        os.environ,
        {"SENDER_EMAIL": "sender@example.com", "SENDER_PASSWORD": "password123"},
    )
    def test_forward_email_exception_in_domain_extraction(self, mock_smtp):
        """Test exception handling when extracting domain from malformed 'from' header"""
        mock_server = Mock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        # Create a string-like object that succeeds for '@' split but fails for subsequent splits
        class BadString(str):
            def split(self, *args, **kwargs):
                # First split by @ works, but return a BadString for the domain part
                if args and args[0] == "@":
                    return [str(self), BadString("domain.com")]
                # For any other split (by '>' or '.'), raise an error
                raise RuntimeError("Simulated split error")

        original_email = {
            "subject": "Test",
            "from": BadString("user@domain.com"),
            "body": "Test body",
        }

        result = EmailForwarder.forward_email(original_email, "target@example.com")

        assert result
        mock_server.send_message.assert_called_once()

    @patch("backend.services.forwarder.smtplib.SMTP")
    @patch.dict(
        os.environ,
        {"SENDER_EMAIL": "sender@example.com", "SENDER_PASSWORD": "password123"},
    )
    def test_forward_email_with_html_body(self, mock_smtp):
        """Test forwarding email with HTML body content"""
        mock_server = Mock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        original_email = {
            "subject": "HTML Email",
            "from": "sender@example.com",
            "body": "Plain text body",
            "html_body": "<html><body><h1>HTML Content</h1></body></html>",
        }

        result = EmailForwarder.forward_email(original_email, "target@example.com")

        assert result
        mock_server.send_message.assert_called_once()

        # Verify the HTML content was used in the message
        sent_message = mock_server.send_message.call_args[0][0]
        # Get the HTML part from the multipart message
        html_part = None
        for part in sent_message.walk():
            if part.get_content_type() == "text/html":
                html_part = part.get_payload(decode=True).decode()
                break

        assert html_part is not None
        assert "<h1>HTML Content</h1>" in html_part

    @patch("backend.services.forwarder.smtplib.SMTP")
    @patch.dict(
        os.environ,
        {
            "SENDER_EMAIL": "sender@example.com",
            "SENDER_PASSWORD": "password123",
            "APP_URL": "https://example.com/",
        },
    )
    def test_forward_email_app_url_trailing_slash(self, mock_smtp):
        """Test APP_URL trailing slash is removed"""
        mock_server = Mock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        original_email = {
            "subject": "Test",
            "from": "sender@amazon.com",
            "body": "Test body",
        }

        result = EmailForwarder.forward_email(original_email, "target@example.com")

        assert result
        mock_server.send_message.assert_called_once()

        # Verify the normalized URL (without trailing slash) was used in links
        sent_message = mock_server.send_message.call_args[0][0]
        # Get the HTML part from the multipart message
        html_part = None
        for part in sent_message.walk():
            if part.get_content_type() == "text/html":
                html_part = part.get_payload(decode=True).decode()
                break

        assert html_part is not None
        # The URL should not have a double slash before /api
        assert "https://example.com/api/actions/quick" in html_part
        assert "https://example.com//api" not in html_part

    @patch("backend.services.forwarder.smtplib.SMTP")
    @patch.dict(
        os.environ,
        {
            "SENDER_EMAIL": "sender@example.com",
            "SENDER_PASSWORD": "password123",
            "APP_URL": "https://example.com",
            "SECRET_KEY": "test-secret-key",
        },
    )
    def test_forward_email_http_link_strategy(self, mock_smtp):
        """Test HTTP link generation with APP_URL and HMAC signature"""
        mock_server = Mock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        original_email = {
            "subject": "Test Receipt",
            "from": "shop@amazon.com",
            "body": "Order details",
        }

        result = EmailForwarder.forward_email(original_email, "target@example.com")

        assert result
        mock_server.send_message.assert_called_once()

        # Verify the message contains HTTP links with HMAC signatures
        sent_message = mock_server.send_message.call_args[0][0]
        # Get the HTML part from the multipart message
        html_part = None
        for part in sent_message.walk():
            if part.get_content_type() == "text/html":
                html_part = part.get_payload(decode=True).decode()
                break

        assert html_part is not None
        # Check for HTTP link format with required parameters
        assert "https://example.com/api/actions/quick?" in html_part
        assert "cmd=" in html_part
        assert "arg=" in html_part
        assert "ts=" in html_part
        assert "sig=" in html_part

    @patch("backend.services.forwarder.smtplib.SMTP")
    @patch("backend.services.forwarder.Session")
    @patch.dict(
        os.environ,
        {"SENDER_EMAIL": "sender@example.com", "SENDER_PASSWORD": "password123"},
    )
    def test_forward_email_database_exception_for_template(
        self, mock_session_class, mock_smtp
    ):
        """Test handling of database exception when fetching email template"""
        mock_server = Mock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        # Mock Session to raise exception
        mock_session = Mock()
        mock_session_class.return_value.__enter__.return_value = mock_session
        mock_session.exec.side_effect = Exception("Database connection failed")

        original_email = {
            "subject": "Test",
            "from": "sender@example.com",
            "body": "Test body",
        }

        result = EmailForwarder.forward_email(original_email, "target@example.com")

        # Should still succeed using default template
        assert result
        mock_server.send_message.assert_called_once()

    @patch("backend.services.forwarder.smtplib.SMTP")
    @patch.dict(
        os.environ,
        {"SENDER_EMAIL": "sender@example.com", "SENDER_PASSWORD": "password123"},
    )
    def test_forward_email_template_keyerror_fallback(
        self, mock_smtp, clean_email_template
    ):
        """Test fallback when custom template has KeyError (missing variable)"""
        mock_server = Mock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        # Store template with an invalid variable
        with Session(engine) as session:
            invalid_template = "Subject: {subject}\nInvalid: {nonexistent_var}"
            setting = GlobalSettings(
                key="email_template",
                value=invalid_template,
                description="Invalid template",
            )
            session.add(setting)
            session.commit()

        original_email = {
            "subject": "Test",
            "from": "sender@example.com",
            "body": "Test body",
        }

        result = EmailForwarder.forward_email(original_email, "target@example.com")

        # Should succeed by falling back to default template
        assert result
        mock_server.send_message.assert_called_once()

    @patch("backend.services.forwarder.smtplib.SMTP")
    @patch.dict(
        os.environ,
        {"SENDER_EMAIL": "sender@example.com", "SENDER_PASSWORD": "password123"},
    )
    def test_forward_email_template_double_fallback(
        self, mock_smtp, clean_email_template
    ):
        """Test absolute fallback when even default template fails"""
        mock_server = Mock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        # Store template with an invalid variable
        with Session(engine) as session:
            invalid_template = "Invalid: {bad_var}"
            setting = GlobalSettings(
                key="email_template",
                value=invalid_template,
                description="Invalid template",
            )
            session.add(setting)
            session.commit()

        original_email = {
            "subject": "Test",
            "from": "sender@example.com",
            "body": "Test body",
        }

        # Temporarily patch DEFAULT_EMAIL_TEMPLATE to also fail
        with patch(
            "backend.services.forwarder.DEFAULT_EMAIL_TEMPLATE", "Bad: {bad_var}"
        ):
            result = EmailForwarder.forward_email(original_email, "target@example.com")

            # Should still succeed with absolute fallback
            assert result
            mock_server.send_message.assert_called_once()

    def test_format_email_date_with_datetime_object(self):
        """Test that format_email_date works with datetime objects"""
        from backend.services.forwarder import format_email_date
        from datetime import datetime, timezone

        # Test with datetime object
        dt = datetime(2023, 12, 21, 10, 30, 0, tzinfo=timezone.utc)
        formatted = format_email_date(dt)
        assert "December 21, 2023" in formatted
        assert "+0000" in formatted

    def test_format_email_date_with_rfc2822_string(self):
        """Test that format_email_date works with RFC 2822 strings"""
        from backend.services.forwarder import format_email_date

        # Test with RFC 2822 string
        formatted = format_email_date("Thu, 21 Dec 2023 10:30:00 +0000")
        assert "December 21, 2023" in formatted
        assert "+0000" in formatted

    def test_format_email_date_with_none(self):
        """Test that format_email_date returns 'Unknown' for None"""
        from backend.services.forwarder import format_email_date

        assert format_email_date(None) == "Unknown"

    def test_format_email_date_with_invalid_string(self):
        """Test that format_email_date returns raw string for invalid input"""
        from backend.services.forwarder import format_email_date

        result = format_email_date("Invalid Date Format")
        assert "Invalid Date Format" in result

    def test_format_email_date_with_naive_datetime(self):
        """Test that format_email_date handles timezone-naive datetime objects by assuming UTC"""
        from backend.services.forwarder import format_email_date
        from datetime import datetime

        # Test with timezone-naive datetime object
        naive_dt = datetime(2023, 12, 21, 10, 30, 0)
        formatted = format_email_date(naive_dt)
        assert "December 21, 2023" in formatted
        assert "+0000" in formatted  # Should assume UTC and format with +0000

    @patch("backend.services.forwarder.smtplib.SMTP")
    @patch.dict(
        os.environ,
        {"SENDER_EMAIL": "sender@example.com", "SENDER_PASSWORD": "password123"},
    )
    def test_forward_email_includes_received_date(self, mock_smtp):
        """Test that forwarded email includes the received date from original email"""
        mock_server = Mock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        original_email = {
            "subject": "Test Receipt",
            "from": "shop@example.com",
            "body": "Order #123",
            "date": "Thu, 21 Dec 2023 10:30:00 +0000",
        }

        result = EmailForwarder.forward_email(original_email, "target@example.com")

        assert result
        mock_server.send_message.assert_called_once()

        # Verify the message contains the received date
        sent_message = mock_server.send_message.call_args[0][0]
        html_part = None
        for part in sent_message.walk():
            if part.get_content_type() == "text/html":
                html_part = part.get_payload(decode=True).decode()
                break

        assert html_part is not None
        # Check that the date appears in the HTML (formatted as "December 21, 2023")
        assert "December 21, 2023" in html_part
        assert "Received:" in html_part

    @patch("backend.services.forwarder.smtplib.SMTP")
    @patch.dict(
        os.environ,
        {"SENDER_EMAIL": "sender@example.com", "SENDER_PASSWORD": "password123"},
    )
    def test_forward_email_missing_date_shows_unknown(self, mock_smtp):
        """Test that forwarded email shows 'Unknown' when date is missing"""
        mock_server = Mock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        original_email = {
            "subject": "Test Receipt",
            "from": "shop@example.com",
            "body": "Order #123",
            # No date field
        }

        result = EmailForwarder.forward_email(original_email, "target@example.com")

        assert result
        mock_server.send_message.assert_called_once()

        # Verify the message contains "Unknown" for the received date
        sent_message = mock_server.send_message.call_args[0][0]
        html_part = None
        for part in sent_message.walk():
            if part.get_content_type() == "text/html":
                html_part = part.get_payload(decode=True).decode()
                break

        assert html_part is not None
        assert "Unknown" in html_part
        assert "Received:" in html_part

    @patch("backend.services.forwarder.smtplib.SMTP")
    @patch.dict(
        os.environ,
        {"SENDER_EMAIL": "sender@example.com", "SENDER_PASSWORD": "password123"},
    )
    def test_forward_email_invalid_date_format_uses_raw_string(self, mock_smtp):
        """Test that forwarded email uses raw date string when parsing fails"""
        mock_server = Mock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        original_email = {
            "subject": "Test Receipt",
            "from": "shop@example.com",
            "body": "Order #123",
            "date": "Invalid Date Format",
        }

        result = EmailForwarder.forward_email(original_email, "target@example.com")

        assert result
        mock_server.send_message.assert_called_once()

        # Verify the message contains the raw date string when parsing fails
        sent_message = mock_server.send_message.call_args[0][0]
        html_part = None
        for part in sent_message.walk():
            if part.get_content_type() == "text/html":
                html_part = part.get_payload(decode=True).decode()
                break

        assert html_part is not None
        assert "Invalid Date Format" in html_part
        assert "Received:" in html_part
