import json
import logging
import os
from typing import Optional


class AccountService:
    @staticmethod
    async def get_oauth2_access_token(account_id: int) -> Optional[str]:
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
                logging.error(f"Error parsing EMAIL_ACCOUNTS: {e}")

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

        accounts = AccountService.get_all_accounts()
        for acc in accounts:
            if acc["email"].lower() == account_email.lower():
                return acc

        return None
