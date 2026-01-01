import logging

from backend.services.imap_service import ImapService


class ConnectionService:
    @staticmethod
    def test_connection(
        email_user,
        email_pass=None,
        imap_server="imap.gmail.com",
        auth_method="password",
        access_token=None,
    ):
        """
        Test IMAP connection with either password or OAuth2 authentication.

        Args:
            email_user: Email/username for authentication
            email_pass: Password (for password auth, optional for OAuth2)
            imap_server: IMAP server hostname
            auth_method: "password" or "oauth2"
            access_token: OAuth2 access token (required for oauth2)

        Returns:
            Dictionary with success status and error message if any
        """
        if auth_method == "password":
            if not email_user or not email_pass:
                return {"success": False, "error": "Credentials missing"}
        elif auth_method == "oauth2":
            if not email_user or not access_token:
                return {
                    "success": False,
                    "error": "Email and access token required for OAuth2",
                }

        try:
            mail = ImapService.connect(
                email_user, email_pass, imap_server, 993, auth_method, access_token
            )
            if mail:
                ImapService.close_and_logout(mail)
                return {"success": True, "error": None}
            else:
                return {
                    "success": False,
                    "error": "Unable to connect to email server",
                }
        except Exception:
            logging.exception("Error when testing email connection")
            # Return a generic error message to avoid exposing internal exception details
            return {
                "success": False,
                "error": "Unable to connect to email server",
            }
