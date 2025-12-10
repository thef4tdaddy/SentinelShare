from email.mime.text import MIMEText
from unittest.mock import Mock, patch

from backend.services.email_service import EmailService


class TestEmailService:

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
            "test@example.com", "password123", "imap.gmail.com", limit=20
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
            "test@example.com", "password123", "imap.gmail.com", limit=5
        )

        # Should only fetch 5 emails
        assert len(emails) == 5
        assert mock_mail.fetch.call_count == 5

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
