import email
import imaplib
import json
import logging
import os
from email.header import decode_header
from typing import Optional


class EmailService:
    @staticmethod
    def get_all_accounts() -> list:
        """
        Retrieves all configured email accounts from environment variables.
        Handles both the legacy single-account setup and the multi-account EMAIL_ACCOUNTS JSON.
        """
        all_accounts = []

        # 1. Check Multi-Account Config
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
                        if acc.get("email") and acc.get("password"):
                            all_accounts.append(
                                {
                                    "email": acc.get("email"),
                                    "password": acc.get("password"),
                                    "imap_server": acc.get(
                                        "imap_server", "imap.gmail.com"
                                    ),
                                }
                            )
            except Exception as e:
                print(f"❌ Error parsing EMAIL_ACCOUNTS: {type(e).__name__}")

        # 2. Legacy / Primary Account Fallback
        # Only add if it wasn't already included in EMAIL_ACCOUNTS and exists
        legacy_user = os.environ.get("GMAIL_EMAIL") or os.environ.get("SENDER_EMAIL")
        legacy_pass = os.environ.get("GMAIL_PASSWORD") or os.environ.get(
            "SENDER_PASSWORD"
        )
        legacy_imap = os.environ.get("IMAP_SERVER", "imap.gmail.com")

        if legacy_user and legacy_pass:
            # Check if already added
            if not any(a["email"].lower() == legacy_user.lower() for a in all_accounts):
                all_accounts.append(
                    {
                        "email": legacy_user,
                        "password": legacy_pass,
                        "imap_server": legacy_imap,
                    }
                )

        # 3. Dedicated iCloud check
        icloud_user = os.environ.get("ICLOUD_EMAIL")
        icloud_pass = os.environ.get("ICLOUD_PASSWORD")
        if icloud_user and icloud_pass:
            if not any(a["email"].lower() == icloud_user.lower() for a in all_accounts):
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
    def test_connection(email_user, email_pass, imap_server="imap.gmail.com"):
        if not email_user or not email_pass:
            return {"success": False, "error": "Credentials missing"}

        try:
            mail = imaplib.IMAP4_SSL(imap_server)
            mail.login(email_user, email_pass)
            mail.logout()
            return {"success": True, "error": None}
        except Exception:
            logging.exception("Error when testing email connection")
            return {"success": False, "error": "Unable to connect to email server"}

    @staticmethod
    def fetch_recent_emails(
        email_user, email_pass, imap_server="imap.gmail.com", limit=20
    ):
        if not email_user or not email_pass:
            print("❌ IMAP Credentials missing")
            return []

        try:
            mail = imaplib.IMAP4_SSL(imap_server)
            mail.login(email_user, email_pass)
            mail.select("inbox")

            # Fetch emails from the last 3 days to ensure we don't miss any
            # even if the inbox is busy.
            from datetime import datetime, timedelta

            # IMAP date format: "01-Jan-2023"
            since_date = (datetime.now() - timedelta(days=3)).strftime("%d-%b-%Y")

            # Escape just in case, though strftime is safe
            search_criterion = f'(SINCE "{since_date}")'

            print(f"   🔍 IMAP Search: {search_criterion}")
            status, messages = mail.search(None, search_criterion)

            if status != "OK":
                return []

            email_ids = messages[0].split()
            print(f"   📬 Recent emails found (last 3 days): {len(email_ids)}")

            # If there are too many, we still limit to avoid timeout, but the date filter helps relevance
            # Increasing limit safety net to 100 to handle busy catch-all inboxes
            BATCH_LIMIT = 100
            if len(email_ids) > BATCH_LIMIT:
                print(f"   ⚠️ Too many emails, taking last {BATCH_LIMIT}")
                email_ids = email_ids[-BATCH_LIMIT:]

            print(f"   📥 Fetching {len(email_ids)} emails...")

            emails_data = []

            for e_id in email_ids:
                typ, data = mail.fetch(e_id, "(BODY[])")
                if typ != "OK":
                    print(f"   ⚠️ Error fetching email {e_id}: Status {typ}")
                    continue

                for response_part in data:
                    if isinstance(response_part, tuple):
                        # print(f"   ✅ Got tuple for {e_id}") # noisy
                        msg = email.message_from_bytes(response_part[1])

                        # Decode subject
                        subject, encoding = decode_header(msg["Subject"])[0]
                        if isinstance(subject, bytes):
                            subject = subject.decode(encoding if encoding else "utf-8")

                        sender = msg.get("From")

                        # Get body
                        body = ""
                        html_body = ""

                        if msg.is_multipart():
                            for part in msg.walk():
                                content_type = part.get_content_type()
                                content_disposition = str(
                                    part.get("Content-Disposition")
                                )

                                if "attachment" in content_disposition:
                                    continue

                                if content_type == "text/plain":
                                    try:
                                        body = part.get_payload(decode=True).decode()
                                    except Exception:
                                        pass
                                elif content_type == "text/html":
                                    try:
                                        html_body = part.get_payload(
                                            decode=True
                                        ).decode()
                                    except Exception:
                                        pass
                        else:
                            content_type = msg.get_content_type()
                            try:
                                payload = msg.get_payload(decode=True).decode()
                                if content_type == "text/html":
                                    html_body = payload
                                else:
                                    body = payload
                            except Exception:
                                pass

                        # Fallback to HTML if no plain text, or if plain text is empty/useless
                        if not body and html_body:
                            from bs4 import BeautifulSoup

                            soup = BeautifulSoup(html_body, "html.parser")
                            body = soup.get_text(separator=" ", strip=True)

                        emails_data.append(
                            {
                                "id": e_id.decode(),  # IMAP ID
                                "message_id": msg.get("Message-ID"),
                                "subject": subject,
                                "from": sender,
                                "body": body,
                                "html_body": html_body,
                                "date": msg.get("Date"),
                                "account_email": email_user,
                            }
                        )

            mail.close()
            mail.logout()
            return emails_data

        except Exception as e:
            # CodeQL: Avoid logging full exception details
            print(f"❌ IMAP Error: {type(e).__name__}")
            return []

    @staticmethod
    def fetch_email_by_id(
        email_user, email_pass, message_id, imap_server="imap.gmail.com"
    ):
        """
        Fetch a single email by its Message-ID header.
        """
        if not email_user or not email_pass or not message_id:
            return None

        try:
            mail = imaplib.IMAP4_SSL(imap_server)
            mail.login(email_user, email_pass)
            mail.select("inbox")

            # Search by Message-ID
            # Message-ID usually contains <...>, verify if stored ID has them or not.
            # Stored ID usually is the raw header value.
            # IMAP search uses "HEADER Message-ID <val>"

            # Escape quotes in message_id just in case
            safe_id = message_id.replace('"', '\\"')
            search_criterion = f'(HEADER Message-ID "{safe_id}")'

            status, messages = mail.search(None, search_criterion)

            if status != "OK" or not messages[0]:
                # Try without surrounding brackets if the stored ID has/hasn't them
                # (Some servers are picky or ID format varies)
                logging.info(
                    f"Email not found by exact ID: {message_id}, trying loose search"
                )
                return None

            email_ids = messages[0].split()
            # Fetch the most recent match (should be unique usually)
            latest_email_id = email_ids[-1]

            typ, data = mail.fetch(latest_email_id, "(BODY[])")
            if typ != "OK":
                return None

            raw_email = None
            for response_part in data:
                if isinstance(response_part, tuple):
                    raw_email = response_part[1]
                    break

            if raw_email:
                msg = email.message_from_bytes(raw_email)

                # Extract body (similar logic to fetch_recent_emails)
                body = ""
                html_body = ""

                if msg.is_multipart():
                    for part in msg.walk():
                        content_type = part.get_content_type()
                        content_disposition = str(part.get("Content-Disposition"))
                        if "attachment" in content_disposition:
                            continue
                        if content_type == "text/plain":
                            try:
                                body = part.get_payload(decode=True).decode()
                            except Exception:
                                pass
                        elif content_type == "text/html":
                            try:
                                html_body = part.get_payload(decode=True).decode()
                            except Exception:
                                pass
                else:
                    payload = msg.get_payload(decode=True).decode()
                    if msg.get_content_type() == "text/html":
                        html_body = payload
                    else:
                        body = payload

                # Fallback to HTML if needed
                if not body and html_body:
                    from bs4 import BeautifulSoup

                    soup = BeautifulSoup(html_body, "html.parser")
                    body = soup.get_text(separator=" ", strip=True)

                # Return dictionary with body and raw content (if needed for forwarding as attachment/original)
                return {
                    "subject": msg.get(
                        "Subject"
                    ),  # Should decode? Caller usually has subject.
                    "body": body,
                    "html_body": html_body,
                    "raw": raw_email,
                }

            mail.logout()
            return None
        except Exception as e:
            logging.error(f"Error fetching email by ID {message_id}: {e}")
            return None
