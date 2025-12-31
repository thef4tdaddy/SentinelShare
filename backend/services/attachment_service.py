"""
Attachment Service - Handles extraction and temporary storage of email attachments.

This service prepares for future attachment handling while currently providing
utilities to identify and skip attachments during email parsing.
"""

import email
import logging
from typing import Optional


class AttachmentService:
    @staticmethod
    def is_attachment(part: email.message.Message) -> bool:
        """
        Check if an email part is an attachment.

        Args:
            part: Email message part

        Returns:
            True if the part is an attachment, False otherwise
        """
        content_disposition = str(part.get("Content-Disposition", ""))
        return "attachment" in content_disposition

    @staticmethod
    def get_attachment_filename(part: email.message.Message) -> Optional[str]:
        """
        Get the filename of an attachment.

        Args:
            part: Email message part

        Returns:
            Filename if available, None otherwise
        """
        try:
            filename = part.get_filename()
            return filename
        except Exception as e:
            logging.warning(f"Error getting attachment filename: {e}")
            return None

    @staticmethod
    def extract_attachment_data(part: email.message.Message) -> Optional[bytes]:
        """
        Extract the raw data of an attachment.

        Args:
            part: Email message part

        Returns:
            Raw attachment bytes, or None if extraction fails
        """
        try:
            payload = part.get_payload(decode=True)
            if isinstance(payload, bytes):
                return payload
            return None
        except Exception as e:
            logging.error(f"Error extracting attachment data: {e}")
            return None

    @staticmethod
    def list_attachments(msg: email.message.Message) -> list[dict]:
        """
        List all attachments in an email message.

        Args:
            msg: Email message object

        Returns:
            List of dictionaries with attachment metadata:
            - filename: Name of the attachment
            - content_type: MIME type of the attachment
            - size: Size in bytes (if available)
        """
        attachments: list[dict] = []

        if not msg.is_multipart():
            return attachments

        for part in msg.walk():
            if AttachmentService.is_attachment(part):
                filename = AttachmentService.get_attachment_filename(part)
                content_type = part.get_content_type()

                attachment_info: dict = {
                    "filename": filename,
                    "content_type": content_type,
                }

                # Try to get size
                try:
                    payload = part.get_payload(decode=True)
                    if payload and isinstance(payload, bytes):
                        attachment_info["size"] = len(payload)
                except Exception:
                    pass

                attachments.append(attachment_info)

        return attachments
