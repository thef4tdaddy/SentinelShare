"""Unit tests for ImapService"""

import imaplib
from unittest.mock import Mock, patch

from backend.services.imap_service import ImapService


class TestImapService:
    """Test cases for ImapService"""

    @patch("backend.services.imap_service.imaplib.IMAP4_SSL")
    def test_connect_success_password(self, mock_imap):
        """Test successful connection with password auth"""
        mock_mail = Mock()
        mock_imap.return_value = mock_mail
        mock_mail.login.return_value = ("OK", [])

        result = ImapService.connect(
            "user@test.com", "password", "imap.test.com", 993, "password", None
        )

        assert result == mock_mail
        mock_imap.assert_called_once_with("imap.test.com", 993)
        mock_mail.login.assert_called_once_with("user@test.com", "password")

    @patch("backend.services.imap_service.imaplib.IMAP4_SSL")
    def test_connect_success_oauth2(self, mock_imap):
        """Test successful connection with OAuth2 auth"""
        mock_mail = Mock()
        mock_imap.return_value = mock_mail

        result = ImapService.connect(
            "user@test.com", None, "imap.test.com", 993, "oauth2", "token123"
        )

        assert result == mock_mail
        mock_mail.authenticate.assert_called_once()

    @patch("backend.services.imap_service.imaplib.IMAP4_SSL")
    def test_connect_missing_credentials_password(self, mock_imap):
        """Test connection fails with missing password credentials"""
        result = ImapService.connect(
            "user@test.com", None, "imap.test.com", 993, "password", None
        )

        assert result is None
        mock_imap.assert_not_called()

    @patch("backend.services.imap_service.imaplib.IMAP4_SSL")
    def test_connect_missing_credentials_oauth2(self, mock_imap):
        """Test connection fails with missing OAuth2 credentials"""
        result = ImapService.connect(
            "user@test.com", None, "imap.test.com", 993, "oauth2", None
        )

        assert result is None
        mock_imap.assert_not_called()

    @patch("backend.services.imap_service.imaplib.IMAP4_SSL")
    def test_connect_login_failure(self, mock_imap):
        """Test connection handles login failure"""
        mock_mail = Mock()
        mock_imap.return_value = mock_mail
        mock_mail.login.side_effect = imaplib.IMAP4.error("Authentication failed")

        result = ImapService.connect(
            "user@test.com", "wrongpass", "imap.test.com", 993, "password", None
        )

        assert result is None

    def test_select_folder_success(self):
        """Test successful folder selection"""
        mock_mail = Mock()
        mock_mail.select.return_value = ("OK", [])

        result = ImapService.select_folder(mock_mail, "inbox")

        assert result is True
        mock_mail.select.assert_called_once_with("inbox")

    def test_select_folder_failure(self):
        """Test folder selection failure"""
        mock_mail = Mock()
        mock_mail.select.return_value = ("NO", [])

        result = ImapService.select_folder(mock_mail, "nonexistent")

        assert result is False

    def test_select_folder_exception(self):
        """Test folder selection with exception"""
        mock_mail = Mock()
        mock_mail.select.side_effect = Exception("Connection error")

        result = ImapService.select_folder(mock_mail, "inbox")

        assert result is False

    def test_search_messages_success(self):
        """Test successful message search"""
        mock_mail = Mock()
        mock_mail.search.return_value = ("OK", [b"1 2 3"])

        result = ImapService.search_messages(mock_mail, '(SINCE "01-Jan-2024")')

        assert result == [b"1", b"2", b"3"]
        mock_mail.search.assert_called_once_with(None, '(SINCE "01-Jan-2024")')

    def test_search_messages_no_results(self):
        """Test message search with no results"""
        mock_mail = Mock()
        mock_mail.search.return_value = ("OK", [b""])

        result = ImapService.search_messages(mock_mail, '(SUBJECT "test")')

        assert result == []

    def test_search_messages_not_ok(self):
        """Test message search with non-OK status"""
        mock_mail = Mock()
        mock_mail.search.return_value = ("NO", [])

        result = ImapService.search_messages(mock_mail, '(SUBJECT "test")')

        assert result is None

    def test_search_messages_exception(self):
        """Test message search with exception"""
        mock_mail = Mock()
        mock_mail.search.side_effect = Exception("Search error")

        result = ImapService.search_messages(mock_mail, '(SUBJECT "test")')

        assert result is None

    def test_fetch_message_success(self):
        """Test successful message fetch"""
        mock_mail = Mock()
        raw_email = b"From: test@test.com\nSubject: Test\n\nBody"
        mock_mail.fetch.return_value = ("OK", [(b"1 (RFC822 {100}", raw_email)])

        result = ImapService.fetch_message(mock_mail, b"1")

        assert result == raw_email
        mock_mail.fetch.assert_called_once_with("1", "(BODY[])")

    def test_fetch_message_not_ok_status(self):
        """Test message fetch with non-OK status"""
        mock_mail = Mock()
        mock_mail.fetch.return_value = ("NO", [])

        result = ImapService.fetch_message(mock_mail, b"1")

        assert result is None

    def test_fetch_message_no_tuple(self):
        """Test message fetch with no tuple in response"""
        mock_mail = Mock()
        mock_mail.fetch.return_value = ("OK", ["not a tuple"])

        result = ImapService.fetch_message(mock_mail, b"1")

        assert result is None

    def test_fetch_message_exception(self):
        """Test message fetch with exception"""
        mock_mail = Mock()
        mock_mail.fetch.side_effect = Exception("Fetch error")

        result = ImapService.fetch_message(mock_mail, b"1")

        assert result is None

    def test_search_by_message_id_success(self):
        """Test successful search by Message-ID"""
        mock_mail = Mock()
        mock_mail.search.return_value = ("OK", [b"5"])

        result = ImapService.search_by_message_id(mock_mail, "<test@example.com>")

        assert result == b"5"

    def test_search_by_message_id_not_found(self):
        """Test search by Message-ID not found"""
        mock_mail = Mock()
        mock_mail.search.return_value = ("OK", [b""])

        result = ImapService.search_by_message_id(mock_mail, "<notfound@example.com>")

        assert result is None

    def test_search_by_message_id_escape_quotes(self):
        """Test search by Message-ID escapes quotes"""
        mock_mail = Mock()
        mock_mail.search.return_value = ("OK", [b"10"])

        result = ImapService.search_by_message_id(mock_mail, '<test"quote@example.com>')

        # Verify the search was called with escaped quotes
        call_args = mock_mail.search.call_args[0][1]
        assert '\\"' in call_args
        assert result == b"10"

    def test_close_and_logout_success(self):
        """Test successful close and logout"""
        mock_mail = Mock()

        ImapService.close_and_logout(mock_mail)

        mock_mail.close.assert_called_once()
        mock_mail.logout.assert_called_once()

    def test_close_and_logout_exception(self):
        """Test close and logout handles exceptions gracefully"""
        mock_mail = Mock()
        mock_mail.close.side_effect = Exception("Close error")
        mock_mail.logout.side_effect = Exception("Logout error")

        # Should not raise exception
        ImapService.close_and_logout(mock_mail)

        mock_mail.close.assert_called_once()
        mock_mail.logout.assert_called_once()
