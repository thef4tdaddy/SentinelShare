"""Unit tests for EmailParser"""

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from unittest.mock import Mock, patch

from backend.services.email_parser import EmailParser


class TestEmailParser:
    """Test cases for EmailParser"""

    def test_decode_subject_simple(self):
        """Test decoding simple subject"""
        result = EmailParser.decode_subject("Test Subject")
        assert result == "Test Subject"

    def test_decode_subject_encoded(self):
        """Test decoding encoded subject"""
        # Base64 encoded "Test Subject"
        encoded = "=?utf-8?b?VGVzdCBTdWJqZWN0?="
        result = EmailParser.decode_subject(encoded)
        assert result == "Test Subject"

    def test_decode_subject_bytes(self):
        """Test decoding subject with bytes"""
        result = EmailParser.decode_subject("Test")
        assert result == "Test"

    def test_decode_subject_error(self):
        """Test decoding subject with error returns original"""
        # Mock decode_header to raise an exception
        with patch("backend.services.email_parser.decode_header") as mock_decode:
            mock_decode.side_effect = Exception("Decode error")
            result = EmailParser.decode_subject("Test")
            assert result == "Test"

    def test_extract_text_from_html(self):
        """Test extracting text from HTML"""
        # Test with actual BeautifulSoup parsing
        result = EmailParser.extract_text_from_html(
            "<html><body><p>Plain text</p></body></html>"
        )

        assert "Plain text" in result

    def test_extract_text_from_html_error(self):
        """Test extracting text from HTML with error"""
        # Test that invalid HTML doesn't crash
        result = EmailParser.extract_text_from_html("")
        assert result == ""

    def test_parse_multipart_body_text_and_html(self):
        """Test parsing multipart message with text and HTML"""
        msg = MIMEMultipart()
        text_part = MIMEText("Plain text", "plain")
        html_part = MIMEText("<html>HTML content</html>", "html")
        msg.attach(text_part)
        msg.attach(html_part)

        body, html_body = EmailParser.parse_multipart_body(msg)

        assert "Plain text" in body
        assert "<html>HTML content</html>" in html_body

    def test_parse_multipart_body_skip_attachment(self):
        """Test parsing multipart message skips attachments"""
        msg = MIMEMultipart()
        text_part = MIMEText("Plain text", "plain")
        attachment = MIMEText("Attachment data")
        attachment.add_header("Content-Disposition", "attachment", filename="test.txt")
        msg.attach(text_part)
        msg.attach(attachment)

        body, html_body = EmailParser.parse_multipart_body(msg)

        assert "Plain text" in body
        assert "Attachment data" not in body

    def test_parse_multipart_body_decode_error(self):
        """Test parsing multipart body handles decode errors"""
        msg = MIMEMultipart()

        # Create a part that will cause decode error
        bad_part = Mock()
        bad_part.get_content_type.return_value = "text/plain"
        bad_part.get.return_value = None
        bad_part.get_payload.side_effect = Exception("Decode error")

        # Mock walk to return our bad part
        with patch.object(msg, "walk", return_value=[msg, bad_part]):
            body, html_body = EmailParser.parse_multipart_body(msg)

            # Should return empty strings without crashing
            assert body == ""
            assert html_body == ""

    def test_parse_simple_body_text(self):
        """Test parsing simple text message"""
        msg = MIMEText("Plain text content")

        body, html_body = EmailParser.parse_simple_body(msg)

        assert body == "Plain text content"
        assert html_body == ""

    def test_parse_simple_body_html(self):
        """Test parsing simple HTML message"""
        msg = MIMEText("<html>HTML content</html>", "html")

        body, html_body = EmailParser.parse_simple_body(msg)

        assert body == ""
        assert html_body == "<html>HTML content</html>"

    def test_parse_simple_body_decode_error(self):
        """Test parsing simple body handles decode errors"""
        msg = Mock()
        msg.get_payload.side_effect = Exception("Decode error")
        msg.get_content_type.return_value = "text/plain"

        body, html_body = EmailParser.parse_simple_body(msg)

        assert body == ""
        assert html_body == ""

    def test_parse_email_body_multipart(self):
        """Test parse_email_body with multipart message"""
        msg = MIMEMultipart()
        text_part = MIMEText("Text content")
        msg.attach(text_part)

        body, html_body = EmailParser.parse_email_body(msg)

        assert "Text content" in body

    def test_parse_email_body_simple(self):
        """Test parse_email_body with simple message"""
        msg = MIMEText("Simple content")

        body, html_body = EmailParser.parse_email_body(msg)

        assert body == "Simple content"

    @patch("backend.services.email_parser.EmailParser.extract_text_from_html")
    def test_parse_email_body_html_fallback(self, mock_extract):
        """Test parse_email_body falls back to HTML extraction"""
        mock_extract.return_value = "Extracted text"

        msg = MIMEText("<html>HTML only</html>", "html")

        body, html_body = EmailParser.parse_email_body(msg)

        assert body == "Extracted text"
        assert html_body == "<html>HTML only</html>"
        mock_extract.assert_called_once_with("<html>HTML only</html>")

    def test_parse_email_message(self):
        """Test parsing complete email message"""
        msg = MIMEText("Test body")
        msg["Subject"] = "Test Subject"
        msg["From"] = "sender@test.com"
        msg["Date"] = "Mon, 01 Jan 2024 12:00:00 +0000"
        msg["Message-ID"] = "<test@test.com>"
        msg["Reply-To"] = "reply@test.com"

        raw_email = msg.as_bytes()
        result = EmailParser.parse_email_message(raw_email, "account@test.com")

        assert result["subject"] == "Test Subject"
        assert result["from"] == "sender@test.com"
        assert result["body"] == "Test body"
        assert result["date"] == "Mon, 01 Jan 2024 12:00:00 +0000"
        assert result["message_id"] == "<test@test.com>"
        assert result["reply_to"] == "reply@test.com"
        assert result["account_email"] == "account@test.com"
        assert result["raw"] == raw_email

    def test_parse_email_message_multipart(self):
        """Test parsing multipart email message"""
        msg = MIMEMultipart()
        msg["Subject"] = "Multipart Test"
        msg["From"] = "sender@test.com"
        msg["Message-ID"] = "<multi@test.com>"

        text_part = MIMEText("Text part")
        html_part = MIMEText("<html>HTML part</html>", "html")
        msg.attach(text_part)
        msg.attach(html_part)

        raw_email = msg.as_bytes()
        result = EmailParser.parse_email_message(raw_email, "account@test.com")

        assert result["subject"] == "Multipart Test"
        assert "Text part" in result["body"]
        assert "<html>HTML part</html>" in result["html_body"]

    def test_parse_email_message_no_subject(self):
        """Test parsing email with no subject"""
        msg = MIMEText("Body")
        msg["From"] = "sender@test.com"

        raw_email = msg.as_bytes()
        result = EmailParser.parse_email_message(raw_email)

        # Should handle missing subject gracefully
        assert "subject" in result
        assert result["from"] == "sender@test.com"
