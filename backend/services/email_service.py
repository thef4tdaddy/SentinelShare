import json
import logging
import os
from datetime import datetime, timedelta
from typing import Optional

from backend.services.email_parser import EmailParser
from backend.services.imap_service import ImapService


class EmailService:
    @staticmethod
    async def _get_oauth2_access_token(account_id: int) -> Optional[str]:
        """
        Get a valid OAuth2 access token for an account, refreshing if necessary.

        Args:
            account_id: Database ID of the EmailAccount

        Returns:
            Valid access token, or None if failed
        """
        try:
            from sqlmodel import Session

            from backend.database import engine
            from backend.models import EmailAccount
            from backend.services.oauth2_service import OAuth2Service

            with Session(engine) as session:
                account = session.get(EmailAccount, account_id)
                if not account:
                    logging.error(f"Account {account_id} not found")
                    return None

                return await OAuth2Service.ensure_valid_token(session, account)
        except Exception as e:
            logging.error(f"Failed to get OAuth2 token for account {account_id}: {e}")
            return None

    @staticmethod
    def get_all_accounts() -> list:
        """
        Retrieves all configured email accounts from both database and environment variables.
        Database accounts take precedence. Handles both the legacy single-account setup
        and the multi-account EMAIL_ACCOUNTS JSON for backward compatibility.
        Supports both password-based and OAuth2 authentication.
        """
        all_accounts = []

        # 1. Fetch accounts from database (new method)
        try:
            from sqlmodel import Session, select

            from backend.database import engine
            from backend.models import EmailAccount
            from backend.services.encryption_service import EncryptionService

            with Session(engine) as session:
                db_accounts = session.exec(
                    select(EmailAccount).where(EmailAccount.is_active)
                ).all()

                for acc in db_accounts:
                    try:
                        account_dict = {
                            "email": acc.email.lower(),  # Normalize to lowercase
                            "imap_server": acc.host,
                            "imap_port": acc.port,
                            "username": acc.username,
                            "auth_method": acc.auth_method,
                            "account_id": acc.id,  # Store DB account ID for token refresh
                        }

                        if acc.auth_method == "oauth2":
                            # OAuth2 account - will need token refresh before use
                            # NOTE: OAuth2 accounts are not yet fully supported by scheduler
                            # TODO: Update scheduler to handle OAuth2 token refresh
                            account_dict["provider"] = acc.provider
                            account_dict["password"] = None  # No password for OAuth2
                        else:
                            # Password-based account
                            if acc.encrypted_password:
                                decrypted_password = EncryptionService.decrypt(
                                    acc.encrypted_password
                                )
                                if decrypted_password:
                                    account_dict["password"] = decrypted_password
                                else:
                                    logging.warning(
                                        f"Failed to decrypt password for {acc.email}, skipping"
                                    )
                                    continue
                            else:
                                logging.warning(
                                    f"No password found for password-based account {acc.email}, skipping"
                                )
                                continue

                        all_accounts.append(account_dict)
                    except Exception as e:
                        logging.error(f"Failed to process account {acc.email}: {e}")
        except Exception as e:
            logging.warning(f"Could not fetch accounts from database: {e}")

        # 2. Check Multi-Account Config (Environment)
        email_accounts_json = os.environ.get("EMAIL_ACCOUNTS")
        if email_accounts_json:
            try:
                try:
                    accounts = json.loads(email_accounts_json)
                except json.JSONDecodeError:
                    # Try single quote fix (common mistake in .env)
                    fixed_json = email_accounts_json.replace("'", '"')
                    accounts = json.loads(fixed_json)

                if isinstance(accounts, list):
                    for acc in accounts:
                        email_val = acc.get("email")
                        pass_val = acc.get("password")
                        if email_val and pass_val:
                            # Check if already added from DB
                            email_str = str(email_val).lower() if email_val else ""
                            if not any(
                                str(a.get("email", "")).lower() == email_str  # type: ignore[arg-type]
                                for a in all_accounts
                            ):
                                all_accounts.append(
                                    {
                                        "email": email_val,
                                        "password": pass_val,
                                        "imap_server": acc.get(
                                            "imap_server", "imap.gmail.com"
                                        ),
                                    }
                                )
            except Exception as e:
                print(f"❌ Error parsing EMAIL_ACCOUNTS: {type(e).__name__}")

        # 3. Legacy / Primary Account Fallback
        # Only add if it wasn't already included in EMAIL_ACCOUNTS and exists
        legacy_user = os.environ.get("GMAIL_EMAIL") or os.environ.get("SENDER_EMAIL")
        legacy_pass = os.environ.get("GMAIL_PASSWORD") or os.environ.get(
            "SENDER_PASSWORD"
        )
        legacy_imap = os.environ.get("IMAP_SERVER", "imap.gmail.com")

        if legacy_user and legacy_pass:
            # Check if already added
            legacy_user_lower = str(legacy_user).lower()
            if not any(str(a.get("email", "")).lower() == legacy_user_lower for a in all_accounts):  # type: ignore[arg-type]
                all_accounts.append(
                    {
                        "email": legacy_user,
                        "password": legacy_pass,
                        "imap_server": legacy_imap,
                    }
                )

        # 4. Dedicated iCloud check
        icloud_user = os.environ.get("ICLOUD_EMAIL")
        icloud_pass = os.environ.get("ICLOUD_PASSWORD")
        if icloud_user and icloud_pass:
            icloud_user_lower = str(icloud_user).lower()
            if not any(str(a.get("email", "")).lower() == icloud_user_lower for a in all_accounts):  # type: ignore[arg-type]
                all_accounts.append(
                    {
                        "email": icloud_user,
                        "password": icloud_pass,
                        "imap_server": "imap.mail.me.com",
                    }
                )

        return all_accounts

    @staticmethod
    def get_credentials_for_account(account_email: str) -> Optional[dict]:
        """
        Finds credentials for a specific account email.
        """
        if not account_email:
            return None

        accounts = EmailService.get_all_accounts()
        for acc in accounts:
            if acc["email"].lower() == account_email.lower():
                return acc

        return None

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

    @staticmethod
    def fetch_recent_emails(
        username,
        password=None,
        imap_server="imap.gmail.com",
        imap_port=993,
        search_criterion=None,
        lookback_days=None,
        auth_method="password",
        access_token=None,
    ):
        """
        Fetch recent emails from an IMAP server.

        Args:
            username: Email address to authenticate with
            password: Password for authentication (required for password auth)
            imap_server: IMAP server hostname (default: "imap.gmail.com")
            imap_port: IMAP server port (default: 993)
            search_criterion: Optional custom IMAP search criterion string.
            lookback_days: Optional integer number of days to look back.
                          If None, defaults to emails from the last N days,
                          where N is set by EMAIL_LOOKBACK_DAYS env var (default: 3)
            auth_method: "password" or "oauth2"
            access_token: OAuth2 access token (required for oauth2 auth)

        Returns:
            List of email dictionaries containing message_id, subject, body,
            html_body, from, date, reply_to, and account_email fields.
            Returns empty list on error or if no credentials provided.
        Environment Variables:
            EMAIL_LOOKBACK_DAYS: Number of days to look back for emails (default: 3).
                                Must be a positive integer.
            EMAIL_BATCH_LIMIT: Maximum number of emails to fetch (default: 100).
                             Prevents timeouts with large inboxes.
        """
        print("🔌 Connecting to IMAP server...")

        # Determine lookback days
        if lookback_days is None:
            default_lookback_days = 3
            raw_lookback = os.environ.get("EMAIL_LOOKBACK_DAYS")
            try:
                if raw_lookback is None:
                    lookback_days = default_lookback_days
                else:
                    lookback_days = int(raw_lookback)
                    if lookback_days <= 0:
                        raise ValueError(
                            "EMAIL_LOOKBACK_DAYS must be a positive integer"
                        )
            except (ValueError, TypeError):
                logging.warning(
                    "Invalid EMAIL_LOOKBACK_DAYS value %r; falling back to %d",
                    raw_lookback,
                    default_lookback_days,
                )
                lookback_days = default_lookback_days

        try:
            # Connect to the server using ImapService
            mail = ImapService.connect(
                username, password, imap_server, imap_port, auth_method, access_token
            )
            if not mail:
                return []

            # Select inbox folder
            if not ImapService.select_folder(mail, "inbox"):
                ImapService.close_and_logout(mail)
                return []

            custom_criterion_provided = search_criterion is not None
            if search_criterion is None:
                # Default to last N days
                since_date = (datetime.now() - timedelta(days=lookback_days)).strftime(
                    "%d-%b-%Y"
                )
                search_criterion = f'(SINCE "{since_date}")'

            print(f"🔍 IMAP Search: {search_criterion}")

            # Search for messages
            email_ids = ImapService.search_messages(mail, search_criterion)
            if email_ids is None:
                print("❌ No messages found!")
                ImapService.close_and_logout(mail)
                return []

            total_emails = len(email_ids)

            # Apply batch limit to prevent timeouts with validation
            default_batch_limit = 100
            raw_batch_limit = os.environ.get("EMAIL_BATCH_LIMIT")
            try:
                if raw_batch_limit is None:
                    batch_limit = default_batch_limit
                else:
                    batch_limit = int(raw_batch_limit)
                    if batch_limit <= 0:
                        raise ValueError("EMAIL_BATCH_LIMIT must be a positive integer")
            except (ValueError, TypeError):
                logging.warning(
                    "Invalid EMAIL_BATCH_LIMIT value %r; falling back to %d",
                    raw_batch_limit,
                    default_batch_limit,
                )
                batch_limit = default_batch_limit

            if total_emails > batch_limit:
                print(
                    f"⚠️ Limiting fetched emails to the last {batch_limit} out of {total_emails} "
                    f"matching messages to avoid timeouts."
                )
                # Keep only the most recent emails (higher IDs are newer in IMAP)
                email_ids = email_ids[-batch_limit:]

            # Log appropriately based on whether custom criterion was used
            if not custom_criterion_provided:
                print(
                    f"📬 Recent emails found (last {lookback_days} days): {len(email_ids)}"
                )
            else:
                print(f"📬 Emails matching search criterion: {len(email_ids)}")

            fetched_emails = []

            for e_id in email_ids:
                try:
                    # Fetch the raw email using ImapService
                    raw_email = ImapService.fetch_message(mail, e_id)
                    if raw_email:
                        # Parse the email using EmailParser
                        parsed_email = EmailParser.parse_email_message(
                            raw_email, username
                        )
                        # Remove the 'raw' field from fetched emails (only needed for forwarding)
                        parsed_email.pop("raw", None)
                        fetched_emails.append(parsed_email)
                except Exception as e:
                    print(f"❌ Error fetching email {e_id}: {e}")
                    continue

            ImapService.close_and_logout(mail)
            return fetched_emails

        except Exception as e:
            print(f"❌ IMAP Connection Error: {type(e).__name__}")
            return []

    @staticmethod
    def fetch_email_by_id(
        email_user,
        email_pass=None,
        message_id=None,
        imap_server="imap.gmail.com",
        auth_method="password",
        access_token=None,
    ):
        """
        Fetch a single email by its Message-ID header.

        Args:
            email_user: Email/username for authentication
            email_pass: Password (for password auth)
            message_id: Message-ID header value to search for
            imap_server: IMAP server hostname
            auth_method: "password" or "oauth2"
            access_token: OAuth2 access token (for oauth2 auth)

        Returns:
            Dictionary with email data, or None if not found
        """
        if not email_user or not message_id:
            return None

        if auth_method == "password" and not email_pass:
            return None
        elif auth_method == "oauth2" and not access_token:
            return None

        try:
            # Connect to the server using ImapService
            mail = ImapService.connect(
                email_user, email_pass, imap_server, 993, auth_method, access_token
            )
            if not mail:
                return None

            # Select inbox folder
            if not ImapService.select_folder(mail, "inbox"):
                ImapService.close_and_logout(mail)
                return None

            # Search by Message-ID
            imap_email_id = ImapService.search_by_message_id(mail, message_id)
            if not imap_email_id:
                ImapService.close_and_logout(mail)
                return None

            # Fetch the raw email
            raw_email = ImapService.fetch_message(mail, imap_email_id)
            ImapService.close_and_logout(mail)

            if raw_email:
                # Parse the email using EmailParser
                parsed_email = EmailParser.parse_email_message(raw_email, email_user)

                # Return dictionary with body and raw content (if needed for forwarding as attachment/original)
                return {
                    "subject": parsed_email.get("subject"),
                    "body": parsed_email.get("body"),
                    "html_body": parsed_email.get("html_body"),
                    "raw": raw_email,
                }

            return None
        except Exception as e:
            logging.error(f"Error fetching email by ID {message_id}: {e}")
            return None
