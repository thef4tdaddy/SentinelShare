"""
Email Parser - Handles the conversion of raw IMAP bytes into structured Python objects/dicts.

This service isolates the data-heavy parsing code from the network-heavy IMAP code,
making it easier to test parsing logic independently and swap out parsing libraries if needed.
"""

import email
import email.message
import logging
from email.header import decode_header
from typing import Optional


class EmailParser:
    @staticmethod
    def decode_subject(subject_header: str) -> str:
        """
        Decode an email subject header.

        Args:
            subject_header: Raw subject header value

        Returns:
            Decoded subject string
        """
        try:
            subject, encoding = decode_header(subject_header)[0]
            if isinstance(subject, bytes):
                subject = subject.decode(encoding or "utf-8", errors="ignore")
            return subject
        except Exception as e:
            logging.warning(f"Error decoding subject: {e}")
            return subject_header

    @staticmethod
    def extract_text_from_html(html_body: str) -> str:
        """
        Extract plain text from HTML content.

        Args:
            html_body: HTML content

        Returns:
            Plain text extracted from HTML
        """
        try:
            from bs4 import BeautifulSoup

            soup = BeautifulSoup(html_body, "html.parser")
            return soup.get_text(separator=" ", strip=True)
        except Exception as e:
            logging.warning(f"Error extracting text from HTML: {e}")
            return ""

    @staticmethod
    def parse_multipart_body(msg: email.message.Message) -> tuple[str, str]:
        """
        Parse body from a multipart email message.

        Args:
            msg: Email message object

        Returns:
            Tuple of (plain_text_body, html_body)
        """
        body = ""
        html_body = ""

        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))

            # Skip attachments
            if "attachment" in content_disposition:
                continue

            try:
                payload = part.get_payload(decode=True)
                if payload and isinstance(payload, bytes):
                    decoded = payload.decode("utf-8", errors="ignore")
                    if content_type == "text/plain":
                        body += decoded
                    elif content_type == "text/html":
                        html_body += decoded
            except Exception:
                # Skip parts that fail to decode
                continue

        return body, html_body

    @staticmethod
    def parse_simple_body(msg: email.message.Message) -> tuple[str, str]:
        """
        Parse body from a non-multipart email message.

        Args:
            msg: Email message object

        Returns:
            Tuple of (plain_text_body, html_body)
        """
        body = ""
        html_body = ""

        try:
            payload = msg.get_payload(decode=True)
            if payload and isinstance(payload, bytes):
                decoded = payload.decode("utf-8", errors="ignore")
                if msg.get_content_type() == "text/html":
                    html_body = decoded
                else:
                    body = decoded
        except Exception:
            logging.exception("Failed to decode non-multipart email payload")

        return body, html_body

    @staticmethod
    def parse_email_body(msg: email.message.Message) -> tuple[str, str]:
        """
        Extract plain text and HTML body from an email message.

        Args:
            msg: Email message object

        Returns:
            Tuple of (plain_text_body, html_body)
        """
        if msg.is_multipart():
            body, html_body = EmailParser.parse_multipart_body(msg)
        else:
            body, html_body = EmailParser.parse_simple_body(msg)

        # Fallback: If no plain text body, extract from HTML
        if not body and html_body:
            body = EmailParser.extract_text_from_html(html_body)

        return body, html_body

    @staticmethod
    def parse_email_message(
        raw_email: bytes, account_email: Optional[str] = None
    ) -> dict:
        """
        Parse a raw email into a structured dictionary.

        Args:
            raw_email: Raw email bytes
            account_email: Email address of the account that received this email

        Returns:
            Dictionary containing parsed email data with keys:
            - message_id
            - reply_to
            - from
            - subject
            - body
            - html_body
            - date
            - account_email
            - raw (optional, for forwarding as attachment/original)
        """
        msg = email.message_from_bytes(raw_email)

        # Parse subject
        subject_header = msg.get("Subject", "")
        subject = EmailParser.decode_subject(subject_header)

        # Extract bodies
        body, html_body = EmailParser.parse_email_body(msg)

        return {
            "message_id": msg.get("Message-ID"),
            "reply_to": msg.get("Reply-To"),
            "from": msg.get("From"),
            "subject": subject,
            "body": body,
            "html_body": html_body,
            "date": msg.get("Date"),
            "account_email": account_email,
            "raw": raw_email,
        }
