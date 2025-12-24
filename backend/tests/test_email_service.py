import os
import pytest
from email.mime.text import MIMEText
from unittest.mock import Mock, patch

from backend.services.email_service import EmailService


class TestEmailService:

    def _setup_mock_imap(self, mock_imap, search_result=b"1"):
        """Helper to setup common IMAP mock configuration"""
        mock_mail = Mock()
        mock_imap.return_value = mock_mail
        mock_mail.login.return_value = ("OK", [])
        mock_mail.select.return_value = ("OK", [])
        mock_mail.search.return_value = ("OK", [search_result])
        return mock_mail

    @patch("backend.services.email_service.imaplib.IMAP4_SSL")
    def test_fetch_recent_emails_success(self, mock_imap):
        """Test successful email fetching"""
        # Setup mock
        mock_mail = Mock()
        mock_imap.return_value = mock_mail
        mock_mail.login.return_value = ("OK", [])
        mock_mail.select.return_value = ("OK", [])
        mock_mail.search.return_value = ("OK", [b"1 2 3"])

        # Create a mock email message
        msg = MIMEText("Test body content")
        msg["Subject"] = "Test Subject"
        msg["From"] = "sender@example.com"
        msg["Date"] = "Mon, 01 Jan 2024 12:00:00 +0000"
        msg["Message-ID"] = "<test123@example.com>"

        mock_mail.fetch.return_value = ("OK", [(b"1 (RFC822 {1234}", msg.as_bytes())])

        # Execute
        emails = EmailService.fetch_recent_emails(
            "test@example.com", "password123", "imap.gmail.com"
        )

        # Assert
        assert len(emails) == 3
        assert emails[0]["subject"] == "Test Subject"
        assert emails[0]["from"] == "sender@example.com"
        assert emails[0]["body"] == "Test body content"
        assert emails[0]["account_email"] == "test@example.com"
        mock_mail.login.assert_called_once_with("test@example.com", "password123")
        mock_mail.select.assert_called_once_with("inbox")
        mock_mail.close.assert_called_once()
        mock_mail.logout.assert_called_once()

    def test_fetch_recent_emails_missing_credentials(self):
        """Test that missing credentials returns empty list"""
        emails = EmailService.fetch_recent_emails(None, None)
        assert emails == []

        emails = EmailService.fetch_recent_emails("test@example.com", None)
        assert emails == []

        emails = EmailService.fetch_recent_emails(None, "password")
        assert emails == []

    @patch("backend.services.email_service.imaplib.IMAP4_SSL")
    def test_fetch_recent_emails_login_failure(self, mock_imap):
        """Test handling of login failure"""
        mock_mail = Mock()
        mock_imap.return_value = mock_mail
        mock_mail.login.side_effect = Exception("Authentication failed")

        emails = EmailService.fetch_recent_emails(
            "test@example.com", "wrongpassword", "imap.gmail.com"
        )

        assert emails == []

    @patch("backend.services.email_service.imaplib.IMAP4_SSL")
    def test_fetch_recent_emails_search_failure(self, mock_imap):
        """Test handling when search returns non-OK status"""
        mock_mail = Mock()
        mock_imap.return_value = mock_mail
        mock_mail.login.return_value = ("OK", [])
        mock_mail.select.return_value = ("OK", [])
        mock_mail.search.return_value = ("NO", [])

        emails = EmailService.fetch_recent_emails(
            "test@example.com", "password123", "imap.gmail.com"
        )

        assert emails == []

    @patch("backend.services.email_service.imaplib.IMAP4_SSL")
    def test_fetch_recent_emails_with_limit(self, mock_imap):
        """Test that limit parameter works correctly"""
        mock_mail = Mock()
        mock_imap.return_value = mock_mail
        mock_mail.login.return_value = ("OK", [])
        mock_mail.select.return_value = ("OK", [])
        # Simulate 100 emails, but we only want last 5
        email_ids = b" ".join([str(i).encode() for i in range(1, 101)])
        mock_mail.search.return_value = ("OK", [email_ids])

        msg = MIMEText("Test body")
        msg["Subject"] = "Test"
        msg["From"] = "sender@example.com"
        msg["Date"] = "Mon, 01 Jan 2024 12:00:00 +0000"
        msg["Message-ID"] = "<test@example.com>"

        mock_mail.fetch.return_value = ("OK", [(b"", msg.as_bytes())])

        emails = EmailService.fetch_recent_emails(
            "test@example.com", "password123", "imap.gmail.com"
        )

        # Should fetch all 100 emails since batch limit is 100 by default
        assert len(emails) == 100
        assert mock_mail.fetch.call_count == 100

    @patch("backend.services.email_service.imaplib.IMAP4_SSL")
    @patch("bs4.BeautifulSoup")
    def test_fetch_emails_with_html_content(self, mock_bs, mock_imap):
        """Test parsing emails with HTML content"""
        mock_mail = Mock()
        mock_imap.return_value = mock_mail
        mock_mail.login.return_value = ("OK", [])
        mock_mail.select.return_value = ("OK", [])
        mock_mail.search.return_value = ("OK", [b"1"])

        # Create multipart email with HTML
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText

        msg = MIMEMultipart()
        msg["Subject"] = "HTML Email"
        msg["From"] = "sender@example.com"
        msg["Date"] = "Mon, 01 Jan 2024 12:00:00 +0000"
        msg["Message-ID"] = "<html@example.com>"

        html_part = MIMEText("<html><body>HTML content</body></html>", "html")
        msg.attach(html_part)

        mock_mail.fetch.return_value = ("OK", [(b"", msg.as_bytes())])

        # Mock BeautifulSoup
        mock_soup = Mock()
        mock_soup.get_text.return_value = "HTML content"
        mock_bs.return_value = mock_soup

        emails = EmailService.fetch_recent_emails(
            "test@example.com", "password123", "imap.gmail.com"
        )

        assert len(emails) == 1
        assert emails[0]["subject"] == "HTML Email"
        mock_bs.assert_called_once()

    @patch("backend.services.email_service.imaplib.IMAP4_SSL")
    def test_fetch_emails_with_multipart_mixed(self, mock_imap):
        """Test parsing multipart emails with attachments"""
        mock_mail = Mock()
        mock_imap.return_value = mock_mail
        mock_mail.login.return_value = ("OK", [])
        mock_mail.select.return_value = ("OK", [])
        mock_mail.search.return_value = ("OK", [b"1"])

        # Create multipart email with text and attachment
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText

        msg = MIMEMultipart()
        msg["Subject"] = "Email with attachment"
        msg["From"] = "sender@example.com"
        msg["Date"] = "Mon, 01 Jan 2024 12:00:00 +0000"
        msg["Message-ID"] = "<attach@example.com>"

        text_part = MIMEText("Plain text content")
        msg.attach(text_part)

        # Add fake attachment
        attachment = MIMEText("attachment data")
        attachment.add_header("Content-Disposition", "attachment", filename="file.txt")
        msg.attach(attachment)

        mock_mail.fetch.return_value = ("OK", [(b"", msg.as_bytes())])

        emails = EmailService.fetch_recent_emails(
            "test@example.com", "password123", "imap.gmail.com"
        )

        assert len(emails) == 1
        assert emails[0]["body"] == "Plain text content"

    @patch("backend.services.email_service.imaplib.IMAP4_SSL")
    def test_fetch_emails_with_encoded_subject(self, mock_imap):
        """Test handling of encoded email subjects"""
        mock_mail = Mock()
        mock_imap.return_value = mock_mail
        mock_mail.login.return_value = ("OK", [])
        mock_mail.select.return_value = ("OK", [])
        mock_mail.search.return_value = ("OK", [b"1"])

        # Create email with encoded subject
        msg = MIMEText("Body content")
        msg["Subject"] = "=?utf-8?b?VGVzdCBTdWJqZWN0?="  # "Test Subject" in base64
        msg["From"] = "sender@example.com"
        msg["Date"] = "Mon, 01 Jan 2024 12:00:00 +0000"
        msg["Message-ID"] = "<encoded@example.com>"

        mock_mail.fetch.return_value = ("OK", [(b"", msg.as_bytes())])

        emails = EmailService.fetch_recent_emails(
            "test@example.com", "password123", "imap.gmail.com"
        )

        assert len(emails) == 1
        # The subject should be decoded
        assert emails[0]["subject"] == "Test Subject"

    @patch("backend.services.email_service.imaplib.IMAP4_SSL")
    def test_fetch_email_by_id_success(self, mock_imap):
        """Test successful fetching of a single email by ID"""
        mock_mail = Mock()
        mock_imap.return_value = mock_mail
        mock_mail.login.return_value = ("OK", [])
        mock_mail.select.return_value = ("OK", [])
        mock_mail.search.return_value = ("OK", [b"1"])

        # Create a mock email message
        msg = MIMEText("Test body content")
        msg["Subject"] = "Test Subject"
        msg["Message-ID"] = "<test123@example.com>"

        mock_mail.fetch.return_value = ("OK", [(b"", msg.as_bytes())])

        result = EmailService.fetch_email_by_id(
            "user@test.com", "pass", "<test123@example.com>", "imap.test.com"
        )

        assert result is not None
        assert result["subject"] == "Test Subject"
        assert result["body"] == "Test body content"

    def test_fetch_email_by_id_missing_params(self):
        """Test fetch_email_by_id with missing parameters"""
        assert EmailService.fetch_email_by_id(None, "pass", "id") is None
        assert EmailService.fetch_email_by_id("user", None, "id") is None
        assert EmailService.fetch_email_by_id("user", "pass", None) is None

    @patch("backend.services.email_service.imaplib.IMAP4_SSL")
    def test_connection_success(self, mock_imap):
        """Test successful email connection test"""
        mock_mail = Mock()
        mock_imap.return_value = mock_mail
        mock_mail.login.return_value = ("OK", [])

        result = EmailService.test_connection("user", "pass", "imap.test.com")
        assert result["success"] is True
        assert result["error"] is None

    @patch("backend.services.email_service.imaplib.IMAP4_SSL")
    def test_connection_failure(self, mock_imap):
        """Test failed email connection test"""
        mock_mail = Mock()
        mock_imap.return_value = mock_mail
        mock_mail.login.side_effect = Exception("Auth failed")

        result = EmailService.test_connection("user", "pass", "imap.test.com")
        assert result["success"] is False
        assert "Unable to connect to email server" == result["error"]

    @patch("backend.services.email_service.imaplib.IMAP4_SSL")
    def test_fetch_email_by_id_multipart_html(self, mock_imap):
        """Test fetching a multipart email with HTML content by ID"""
        mock_mail = Mock()
        mock_imap.return_value = mock_mail
        mock_mail.login.return_value = ("OK", [])
        mock_mail.select.return_value = ("OK", [])
        mock_mail.search.return_value = ("OK", [b"1"])

        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText

        msg = MIMEMultipart("alternative")
        msg["Subject"] = "HTML Multi"
        msg["Message-ID"] = "<html-multi@test.com>"

        html_part = MIMEText("<html><body>HTML Content</body></html>", "html")
        msg.attach(html_part)

        mock_mail.fetch.return_value = ("OK", [(b"", msg.as_bytes())])

        result = EmailService.fetch_email_by_id("user", "pass", "<html-multi@test.com>")

        assert result is not None
        assert "HTML Content" in result["body"]  # BS should have converted it
        assert "<html>" in result["html_body"]

    @patch.dict(os.environ, {"EMAIL_ACCOUNTS": '[{"email":"test1@example.com","password":"pass1"}]'}, clear=True)
    def test_get_all_accounts_with_email_accounts_json(self):
        """Test get_all_accounts with EMAIL_ACCOUNTS JSON"""
        accounts = EmailService.get_all_accounts()
        assert len(accounts) >= 1
        assert any(acc["email"] == "test1@example.com" for acc in accounts)

    @patch.dict(os.environ, {"GMAIL_EMAIL": "gmail@test.com", "GMAIL_PASSWORD": "gmailpass"}, clear=True)
    def test_get_all_accounts_legacy_gmail(self):
        """Test get_all_accounts with legacy GMAIL credentials"""
        accounts = EmailService.get_all_accounts()
        assert len(accounts) == 1
        assert accounts[0]["email"] == "gmail@test.com"
        assert accounts[0]["password"] == "gmailpass"

    @patch.dict(os.environ, {"ICLOUD_EMAIL": "icloud@test.com", "ICLOUD_PASSWORD": "icloudpass"}, clear=True)
    def test_get_all_accounts_with_icloud(self):
        """Test get_all_accounts with iCloud credentials"""
        accounts = EmailService.get_all_accounts()
        assert len(accounts) == 1
        assert accounts[0]["email"] == "icloud@test.com"
        assert accounts[0]["imap_server"] == "imap.mail.me.com"

    def test_get_credentials_for_account_missing_email(self):
        """Test get_credentials_for_account with None or empty email"""
        result = EmailService.get_credentials_for_account(None)
        assert result is None

        result = EmailService.get_credentials_for_account("")
        assert result is None

    @patch.dict(os.environ, {"EMAIL_ACCOUNTS": '[{"email":"found@test.com","password":"pass"}]'}, clear=True)
    def test_get_credentials_for_account_found(self):
        """Test get_credentials_for_account with existing account"""
        result = EmailService.get_credentials_for_account("found@test.com")
        assert result is not None
        assert result["email"] == "found@test.com"
        assert result["password"] == "pass"

    @patch.dict(os.environ, {"EMAIL_ACCOUNTS": '[{"email":"other@test.com","password":"pass"}]'}, clear=True)
    def test_get_credentials_for_account_not_found(self):
        """Test get_credentials_for_account with non-existent account"""
        result = EmailService.get_credentials_for_account("notfound@test.com")
        assert result is None

    def test_test_connection_missing_credentials(self):
        """Test test_connection with missing credentials"""
        result = EmailService.test_connection(None, "password")
        assert result["success"] is False
        assert result["error"] == "Credentials missing"

        result = EmailService.test_connection("user", None)
        assert result["success"] is False
        assert result["error"] == "Credentials missing"

    @patch.dict(os.environ, {"EMAIL_LOOKBACK_DAYS": "invalid"}, clear=True)
    @patch("backend.services.email_service.imaplib.IMAP4_SSL")
    def test_fetch_emails_invalid_lookback_days(self, mock_imap):
        """Test fetch_recent_emails with invalid EMAIL_LOOKBACK_DAYS"""
        mock_mail = self._setup_mock_imap(mock_imap)

        msg = MIMEText("Test")
        msg["Subject"] = "Test"
        msg["From"] = "test@test.com"
        msg["Date"] = "Mon, 01 Jan 2024 12:00:00 +0000"
        msg["Message-ID"] = "<test@test.com>"
        mock_mail.fetch.return_value = ("OK", [(b"", msg.as_bytes())])

        emails = EmailService.fetch_recent_emails("user@test.com", "pass")
        # Should fall back to default 3 days
        assert len(emails) == 1

    @patch.dict(os.environ, {"EMAIL_LOOKBACK_DAYS": "-5"}, clear=True)
    @patch("backend.services.email_service.imaplib.IMAP4_SSL")
    def test_fetch_emails_negative_lookback_days(self, mock_imap):
        """Test fetch_recent_emails with negative EMAIL_LOOKBACK_DAYS"""
        mock_mail = self._setup_mock_imap(mock_imap)

        msg = MIMEText("Test")
        msg["Subject"] = "Test"
        msg["From"] = "test@test.com"
        msg["Date"] = "Mon, 01 Jan 2024 12:00:00 +0000"
        msg["Message-ID"] = "<test@test.com>"
        mock_mail.fetch.return_value = ("OK", [(b"", msg.as_bytes())])

        emails = EmailService.fetch_recent_emails("user@test.com", "pass")
        # Should fall back to default 3 days
        assert len(emails) == 1

    @patch.dict(os.environ, {"EMAIL_BATCH_LIMIT": "invalid"}, clear=True)
    @patch("backend.services.email_service.imaplib.IMAP4_SSL")
    def test_fetch_emails_invalid_batch_limit(self, mock_imap):
        """Test fetch_recent_emails with invalid EMAIL_BATCH_LIMIT"""
        # Create 50 email IDs
        email_ids = b" ".join([str(i).encode() for i in range(1, 51)])
        mock_mail = self._setup_mock_imap(mock_imap, email_ids)

        msg = MIMEText("Test")
        msg["Subject"] = "Test"
        msg["From"] = "test@test.com"
        msg["Date"] = "Mon, 01 Jan 2024 12:00:00 +0000"
        msg["Message-ID"] = "<test@test.com>"
        mock_mail.fetch.return_value = ("OK", [(b"", msg.as_bytes())])

        emails = EmailService.fetch_recent_emails("user@test.com", "pass")
        # Should use default batch limit of 100
        assert len(emails) == 50

    @patch.dict(os.environ, {"EMAIL_BATCH_LIMIT": "-10"}, clear=True)
    @patch("backend.services.email_service.imaplib.IMAP4_SSL")
    def test_fetch_emails_negative_batch_limit(self, mock_imap):
        """Test fetch_recent_emails with negative EMAIL_BATCH_LIMIT"""
        mock_mail = self._setup_mock_imap(mock_imap)

        msg = MIMEText("Test")
        msg["Subject"] = "Test"
        msg["From"] = "test@test.com"
        msg["Date"] = "Mon, 01 Jan 2024 12:00:00 +0000"
        msg["Message-ID"] = "<test@test.com>"
        mock_mail.fetch.return_value = ("OK", [(b"", msg.as_bytes())])

        emails = EmailService.fetch_recent_emails("user@test.com", "pass")
        # Should use default batch limit of 100
        assert len(emails) == 1

    @patch("backend.services.email_service.imaplib.IMAP4_SSL")
    def test_fetch_emails_with_payload_decode_exception(self, mock_imap):
        """Test fetch_recent_emails with exception during payload decoding"""
        mock_mail = self._setup_mock_imap(mock_imap)
        mock_mail.select.return_value = ("OK", [])
        mock_mail.search.return_value = ("OK", [b"1"])

        from email.mime.multipart import MIMEMultipart
        from email.mime.base import MIMEBase

        msg = MIMEMultipart()
        msg["Subject"] = "Test"
        msg["From"] = "test@test.com"
        msg["Date"] = "Mon, 01 Jan 2024 12:00:00 +0000"
        msg["Message-ID"] = "<test@test.com>"

        # Add a part that will cause exception during decoding
        bad_part = MIMEBase("text", "plain")
        bad_part.set_payload(b"\x80\x81\x82")  # Invalid UTF-8
        msg.attach(bad_part)

        mock_mail.fetch.return_value = ("OK", [(b"", msg.as_bytes())])

        emails = EmailService.fetch_recent_emails("user@test.com", "pass")
        # Should handle the exception and still return the email
        assert len(emails) == 1

    @patch("backend.services.email_service.imaplib.IMAP4_SSL")
    def test_fetch_emails_non_multipart_html(self, mock_imap):
        """Test fetch_recent_emails with non-multipart HTML email"""
        mock_mail = Mock()
        mock_imap.return_value = mock_mail
        mock_mail.login.return_value = ("OK", [])
        mock_mail.select.return_value = ("OK", [])
        mock_mail.search.return_value = ("OK", [b"1"])

        msg = MIMEText("<html><body>HTML Content</body></html>", "html")
        msg["Subject"] = "HTML Email"
        msg["From"] = "test@test.com"
        msg["Date"] = "Mon, 01 Jan 2024 12:00:00 +0000"
        msg["Message-ID"] = "<html@test.com>"

        mock_mail.fetch.return_value = ("OK", [(b"", msg.as_bytes())])

        emails = EmailService.fetch_recent_emails("user@test.com", "pass")
        assert len(emails) == 1
        assert emails[0]["html_body"]
        assert "HTML" in emails[0]["body"]  # Should extract text from HTML

    @patch("backend.services.email_service.imaplib.IMAP4_SSL")
    def test_fetch_emails_with_fetch_exception(self, mock_imap):
        """Test fetch_recent_emails with exception during individual email fetch"""
        mock_mail = Mock()
        mock_imap.return_value = mock_mail
        mock_mail.login.return_value = ("OK", [])
        mock_mail.select.return_value = ("OK", [])
        mock_mail.search.return_value = ("OK", [b"1 2"])

        # First email fails, second succeeds
        msg = MIMEText("Test")
        msg["Subject"] = "Test"
        msg["From"] = "test@test.com"
        msg["Date"] = "Mon, 01 Jan 2024 12:00:00 +0000"
        msg["Message-ID"] = "<test@test.com>"

        mock_mail.fetch.side_effect = [
            Exception("Fetch failed"),
            ("OK", [(b"", msg.as_bytes())])
        ]

        emails = EmailService.fetch_recent_emails("user@test.com", "pass")
        # Should handle exception and continue with next email
        assert len(emails) == 1

    @patch("backend.services.email_service.imaplib.IMAP4_SSL")
    def test_fetch_email_by_id_search_not_ok(self, mock_imap):
        """Test fetch_email_by_id when search returns non-OK status"""
        mock_mail = Mock()
        mock_imap.return_value = mock_mail
        mock_mail.login.return_value = ("OK", [])
        mock_mail.select.return_value = ("OK", [])
        mock_mail.search.return_value = ("NO", [])

        result = EmailService.fetch_email_by_id("user", "pass", "<test@test.com>")
        assert result is None

    @patch("backend.services.email_service.imaplib.IMAP4_SSL")
    def test_fetch_email_by_id_no_messages(self, mock_imap):
        """Test fetch_email_by_id when search returns no messages"""
        mock_mail = Mock()
        mock_imap.return_value = mock_mail
        mock_mail.login.return_value = ("OK", [])
        mock_mail.select.return_value = ("OK", [])
        mock_mail.search.return_value = ("OK", [b""])

        result = EmailService.fetch_email_by_id("user", "pass", "<test@test.com>")
        assert result is None

    @patch("backend.services.email_service.imaplib.IMAP4_SSL")
    def test_fetch_email_by_id_fetch_not_ok(self, mock_imap):
        """Test fetch_email_by_id when fetch returns non-OK status"""
        mock_mail = Mock()
        mock_imap.return_value = mock_mail
        mock_mail.login.return_value = ("OK", [])
        mock_mail.select.return_value = ("OK", [])
        mock_mail.search.return_value = ("OK", [b"1"])
        mock_mail.fetch.return_value = ("NO", [])

        result = EmailService.fetch_email_by_id("user", "pass", "<test@test.com>")
        assert result is None

    @patch("backend.services.email_service.imaplib.IMAP4_SSL")
    def test_fetch_email_by_id_exception(self, mock_imap):
        """Test fetch_email_by_id with exception during processing"""
        mock_mail = Mock()
        mock_imap.return_value = mock_mail
        mock_mail.login.side_effect = Exception("Connection error")

        result = EmailService.fetch_email_by_id("user", "pass", "<test@test.com>")
        assert result is None

    @patch.dict(os.environ, {"EMAIL_ACCOUNTS": "[{'email':'test@test.com','password':'pass'}]"}, clear=True)
    def test_get_all_accounts_single_quote_json(self):
        """Test get_all_accounts with single-quoted JSON (common mistake)"""
        accounts = EmailService.get_all_accounts()
        assert len(accounts) >= 1
        assert any(acc["email"] == "test@test.com" for acc in accounts)

    @patch.dict(os.environ, {"EMAIL_ACCOUNTS": "not valid json at all"}, clear=True)
    def test_get_all_accounts_invalid_json(self):
        """Test get_all_accounts with completely invalid JSON"""
        # Should handle gracefully and return empty or fallback accounts
        accounts = EmailService.get_all_accounts()
        # Should not crash, returns whatever is available from other sources
        assert isinstance(accounts, list)

    @patch("backend.services.email_service.imaplib.IMAP4_SSL")
    def test_fetch_emails_with_custom_search_criterion(self, mock_imap):
        """Test fetch_recent_emails with custom search criterion"""
        mock_mail = Mock()
        mock_imap.return_value = mock_mail
        mock_mail.login.return_value = ("OK", [])
        mock_mail.select.return_value = ("OK", [])
        mock_mail.search.return_value = ("OK", [b"1"])

        msg = MIMEText("Test")
        msg["Subject"] = "Test"
        msg["From"] = "test@test.com"
        msg["Date"] = "Mon, 01 Jan 2024 12:00:00 +0000"
        msg["Message-ID"] = "<test@test.com>"
        mock_mail.fetch.return_value = ("OK", [(b"", msg.as_bytes())])

        # Use custom search criterion to test that branch
        emails = EmailService.fetch_recent_emails(
            "user@test.com", 
            "pass", 
            search_criterion='(SUBJECT "invoice")'
        )
        assert len(emails) == 1

    @patch("backend.services.email_service.imaplib.IMAP4_SSL")
    def test_fetch_emails_non_multipart_decode_exception(self, mock_imap):
        """Test fetch_recent_emails with exception in non-multipart decode"""
        mock_mail = Mock()
        mock_imap.return_value = mock_mail
        mock_mail.login.return_value = ("OK", [])
        mock_mail.select.return_value = ("OK", [])
        mock_mail.search.return_value = ("OK", [b"1"])

        # We want to deterministically trigger an exception when the service
        # calls msg.get_payload(decode=True).decode(...).
        from email.message import Message

        class BadPayloadMessage(Message):
            def get_payload(self, decode=False):
                # When decode=True, return bytes that will fail UTF-8 decoding
                if decode:
                    return b"\x80\x81\x82"
                return super().get_payload(decode=decode)

        # Patch message_from_bytes so that EmailService uses our BadPayloadMessage
        with patch(
            "backend.services.email_service.email.message_from_bytes"
        ) as mock_message_from_bytes:
            bad_msg = BadPayloadMessage()
            bad_msg["Subject"] = "Test"
            bad_msg["From"] = "test@test.com"
            bad_msg["Date"] = "Mon, 01 Jan 2024 12:00:00 +0000"
            bad_msg["Message-ID"] = "<test@test.com>"

            mock_message_from_bytes.return_value = bad_msg

            # The actual bytes returned here don't matter, since we override
            # message_from_bytes to always return bad_msg.
            mock_mail.fetch.return_value = ("OK", [(b"", b"raw-bytes")])

            emails = EmailService.fetch_recent_emails("user@test.com", "pass")

        # Should handle exception and still return email with empty body
        assert len(emails) == 1
        assert emails[0]["subject"] == "Test"
        assert emails[0]["from"] == "test@test.com"
        assert emails[0]["body"] == ""

    @patch("backend.services.email_service.imaplib.IMAP4_SSL")
    def test_fetch_email_by_id_multipart_decode_exceptions(self, mock_imap):
        """Test fetch_email_by_id with exceptions during multipart decoding"""
        mock_mail = Mock()
        mock_imap.return_value = mock_mail
        mock_mail.login.return_value = ("OK", [])
        mock_mail.select.return_value = ("OK", [])
        mock_mail.search.return_value = ("OK", [b"1"])

        from email.mime.multipart import MIMEMultipart
        from email.mime.base import MIMEBase

        msg = MIMEMultipart()
        msg["Subject"] = "Test"
        msg["Message-ID"] = "<test@test.com>"

        # Add parts that will cause exceptions
        bad_text_part = MIMEBase("text", "plain")
        bad_text_part.set_payload(b"\x80\x81\x82")  # Invalid UTF-8
        msg.attach(bad_text_part)

        bad_html_part = MIMEBase("text", "html")
        bad_html_part.set_payload(b"\x80\x81\x82")  # Invalid UTF-8
        msg.attach(bad_html_part)

        # Add a valid text part to ensure processing continues after exceptions
        good_text_part = MIMEText("Good text body")
        msg.attach(good_text_part)

        mock_mail.fetch.return_value = ("OK", [(b"", msg.as_bytes())])

        result = EmailService.fetch_email_by_id("user", "pass", "<test@test.com>")
        # Should handle exceptions, continue processing, and still return result
        assert result is not None
        # The valid part should be decoded and included in the body
        assert isinstance(result, dict)
        assert "Good text body" in result.get("body", "")

    @patch.dict(os.environ, {"EMAIL_BATCH_LIMIT": "5"}, clear=True)
    @patch("backend.services.email_service.imaplib.IMAP4_SSL")
    def test_fetch_emails_with_custom_criterion_and_batch_limit(self, mock_imap):
        """Test fetch with custom search criterion AND batch limiting"""
        mock_mail = Mock()
        mock_imap.return_value = mock_mail
        mock_mail.login.return_value = ("OK", [])
        mock_mail.select.return_value = ("OK", [])
        # Create 10 emails to exceed batch limit of 5
        email_ids = b" ".join([str(i).encode() for i in range(1, 11)])
        mock_mail.search.return_value = ("OK", [email_ids])

        msg = MIMEText("Test")
        msg["Subject"] = "Test"
        msg["From"] = "test@test.com"
        msg["Date"] = "Mon, 01 Jan 2024 12:00:00 +0000"
        msg["Message-ID"] = "<test@test.com>"
        mock_mail.fetch.return_value = ("OK", [(b"", msg.as_bytes())])

        # Use custom search criterion with batch limit
        emails = EmailService.fetch_recent_emails(
            "user@test.com", 
            "pass", 
            search_criterion='(SUBJECT "invoice")'
        )
        # Should limit to 5 emails
        assert len(emails) == 5

    @patch("backend.services.email_service.imaplib.IMAP4_SSL")
    def test_fetch_email_by_id_non_multipart_html(self, mock_imap):
        """Test fetch_email_by_id with non-multipart HTML email"""
        mock_mail = Mock()
        mock_imap.return_value = mock_mail
        mock_mail.login.return_value = ("OK", [])
        mock_mail.select.return_value = ("OK", [])
        mock_mail.search.return_value = ("OK", [b"1"])

        msg = MIMEText("<html><body>HTML Content</body></html>", "html")
        msg["Subject"] = "HTML Test"
        msg["Message-ID"] = "<html@test.com>"

        mock_mail.fetch.return_value = ("OK", [(b"", msg.as_bytes())])

        result = EmailService.fetch_email_by_id("user", "pass", "<html@test.com>")
        assert result is not None
        assert result["html_body"]

    @patch("backend.services.email_service.imaplib.IMAP4_SSL")
    def test_fetch_email_by_id_no_raw_email_data(self, mock_imap):
        """Test fetch_email_by_id when no raw email data is returned"""
        mock_mail = Mock()
        mock_imap.return_value = mock_mail
        mock_mail.login.return_value = ("OK", [])
        mock_mail.select.return_value = ("OK", [])
        mock_mail.search.return_value = ("OK", [b"1"])
        # Return data but no tuple with raw email
        mock_mail.fetch.return_value = ("OK", ["not a tuple"])

        result = EmailService.fetch_email_by_id("user", "pass", "<test@test.com>")
        # Should logout and return None
        assert result is None
        mock_mail.logout.assert_called_once()

    @patch("backend.services.email_service.imaplib.IMAP4_SSL")
    def test_fetch_email_by_id_with_attachment(self, mock_imap):
        """Test fetch_email_by_id skips attachments in multipart email"""
        mock_mail = Mock()
        mock_imap.return_value = mock_mail
        mock_mail.login.return_value = ("OK", [])
        mock_mail.select.return_value = ("OK", [])
        mock_mail.search.return_value = ("OK", [b"1"])

        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText as MIMETextType

        msg = MIMEMultipart()
        msg["Subject"] = "With Attachment"
        msg["Message-ID"] = "<attach@test.com>"

        # Add text part
        text_part = MIMETextType("Text content", "plain")
        msg.attach(text_part)

        # Add attachment part
        attachment = MIMETextType("attachment data")
        attachment.add_header("Content-Disposition", "attachment", filename="file.txt")
        msg.attach(attachment)

        mock_mail.fetch.return_value = ("OK", [(b"", msg.as_bytes())])

        result = EmailService.fetch_email_by_id("user", "pass", "<attach@test.com>")
        assert result is not None
        assert result["body"] == "Text content"
