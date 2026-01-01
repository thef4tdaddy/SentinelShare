"""
IMAP Service - Handles raw IMAP connection lifecycle, folder selection, and message fetching.

This service isolates the network-heavy IMAP code from the data-heavy parsing code,
making it easier to mock the network layer for tests and swap out IMAP libraries if needed.
"""

import imaplib
import logging
from typing import Optional


class ImapService:
    @staticmethod
    def _imap_login(
        mail: imaplib.IMAP4_SSL,
        username: str,
        password: str,
        auth_method: str = "password",
        access_token: Optional[str] = None,
    ) -> None:
        """
        Perform IMAP login using either password or OAuth2.

        Args:
            mail: IMAP connection object
            username: Username/email for authentication
            password: Password (for password auth)
            auth_method: "password" or "oauth2"
            access_token: OAuth2 access token (for oauth2 auth)

        Raises:
            Exception: If login fails
        """
        if auth_method == "oauth2":
            if not access_token:
                raise ValueError("OAuth2 access token required for oauth2 auth_method")

            from backend.services.oauth2_service import OAuth2Service

            auth_string = OAuth2Service.generate_xoauth2_string(username, access_token)
            mail.authenticate("XOAUTH2", lambda x: auth_string.encode())  # type: ignore[arg-type]
        elif auth_method == "password":
            # Standard password authentication
            if not password:
                raise ValueError("Password is required for password auth_method")
            mail.login(username, password)
        else:
            raise ValueError(f"Unsupported auth_method: {auth_method}")

    @staticmethod
    def connect(
        username: str,
        password: Optional[str] = None,
        imap_server: str = "imap.gmail.com",
        imap_port: int = 993,
        auth_method: str = "password",
        access_token: Optional[str] = None,
    ) -> Optional[imaplib.IMAP4_SSL]:
        """
        Connect to an IMAP server and authenticate.

        Args:
            username: Email address to authenticate with
            password: Password for authentication (required for password auth)
            imap_server: IMAP server hostname
            imap_port: IMAP server port
            auth_method: "password" or "oauth2"
            access_token: OAuth2 access token (required for oauth2 auth)

        Returns:
            Authenticated IMAP connection object, or None if connection fails
        """
        # Validate credentials based on auth method
        if auth_method == "password":
            if not username or not password:
                logging.warning("IMAP Credentials missing for password auth")
                return None
        elif auth_method == "oauth2":
            if not username or not access_token:
                logging.warning("OAuth2 credentials missing")
                return None

        try:
            mail = imaplib.IMAP4_SSL(imap_server, imap_port)
            ImapService._imap_login(
                mail, username, password or "", auth_method, access_token
            )
            return mail
        except Exception as e:
            logging.error(f"IMAP Connection Error: {type(e).__name__}")
            return None

    @staticmethod
    def select_folder(mail: imaplib.IMAP4_SSL, folder: str = "inbox") -> bool:
        """
        Select a folder/mailbox on the IMAP server.

        Args:
            mail: IMAP connection object
            folder: Folder name to select (default: "inbox")

        Returns:
            True if folder selection was successful, False otherwise
        """
        try:
            status, _ = mail.select(folder)
            return status == "OK"
        except Exception as e:
            logging.error(f"Error selecting folder {folder}: {e}")
            return False

    @staticmethod
    def search_messages(
        mail: imaplib.IMAP4_SSL, search_criterion: str
    ) -> Optional[list]:
        """
        Search for messages matching a criterion.

        Args:
            mail: IMAP connection object
            search_criterion: IMAP search criterion (e.g., '(SINCE "01-Jan-2024")')

        Returns:
            List of message IDs (as bytes), or None if search failed
        """
        try:
            status, messages = mail.search(None, search_criterion)
            if status != "OK":
                logging.warning("IMAP search returned non-OK status")
                return None
            return messages[0].split() if messages[0] else []
        except Exception as e:
            logging.error(f"Error searching messages: {e}")
            return None

    @staticmethod
    def fetch_message(mail: imaplib.IMAP4_SSL, message_id: bytes) -> Optional[bytes]:
        """
        Fetch a single message by its IMAP ID.

        Args:
            mail: IMAP connection object
            message_id: IMAP message ID (as bytes)

        Returns:
            Raw email bytes, or None if fetch failed
        """
        try:
            # Convert bytes to string for fetch command
            msg_id_str = message_id.decode("ascii")
            status, msg_data = mail.fetch(msg_id_str, "(BODY[])")

            # Check if fetch was successful
            if status != "OK":
                logging.warning(f"IMAP fetch returned non-OK status: {status}")
                return None

            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    return response_part[1]
            return None
        except Exception as e:
            # Use repr to properly format bytes in the log message
            logging.error(f"Error fetching message {message_id!r}: {e}")
            return None

    @staticmethod
    def search_by_message_id(
        mail: imaplib.IMAP4_SSL, message_id: str
    ) -> Optional[bytes]:
        """
        Search for a message by its Message-ID header.

        Args:
            mail: IMAP connection object
            message_id: Message-ID header value

        Returns:
            IMAP message ID (as bytes) of the first match, or None if not found
        """
        try:
            # Escape quotes in message_id
            safe_id = message_id.replace('"', '\\"')
            search_criterion = f'(HEADER Message-ID "{safe_id}")'
            status, messages = mail.search(None, search_criterion)

            if status != "OK" or not messages[0]:
                logging.info(f"Email not found by Message-ID: {message_id}")
                return None

            email_ids = messages[0].split()
            # Return the most recent match (should be unique usually)
            return email_ids[-1] if email_ids else None
        except Exception as e:
            logging.error(f"Error searching by Message-ID {message_id}: {e}")
            return None

    @staticmethod
    def close_and_logout(mail: imaplib.IMAP4_SSL) -> None:
        """
        Close the selected folder and logout from the IMAP server.

        Args:
            mail: IMAP connection object
        """
        try:
            mail.close()
        except Exception:
            pass  # Folder might not be selected
        try:
            mail.logout()
        except Exception as e:
            logging.debug(f"Error during IMAP logout: {e}")
