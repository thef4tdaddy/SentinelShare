import email
import imaplib
import os
from datetime import datetime
from email.header import decode_header


class EmailService:
    @staticmethod
    def test_connection(email_user, email_pass, imap_server="imap.gmail.com"):
        if not email_user or not email_pass:
            return {"success": False, "error": "Credentials missing"}

        try:
            mail = imaplib.IMAP4_SSL(imap_server)
            mail.login(email_user, email_pass)
            mail.logout()
            return {"success": True, "error": None}
        except Exception as e:
            return {"success": False, "error": str(e)}

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

            # Fetch ALL emails, but we only process the last 'limit'
            # Note: valid only if server returns IDs in order, which is standard
            status, messages = mail.search(None, "ALL")
            if status != "OK":
                return []

            email_ids = messages[0].split()
            print(f"   📬 Total emails found in inbox: {len(email_ids)}")

            # Process latest first
            email_ids = email_ids[-limit:]
            print(f"   📥 Fetching last {len(email_ids)} emails...")

            emails_data = []

            for e_id in email_ids:
                res, msg_data = mail.fetch(e_id, "(RFC822)")
                for response_part in msg_data:
                    if isinstance(response_part, tuple):
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
                                    except:
                                        pass
                                elif content_type == "text/html":
                                    try:
                                        html_body = part.get_payload(
                                            decode=True
                                        ).decode()
                                    except:
                                        pass
                        else:
                            content_type = msg.get_content_type()
                            try:
                                payload = msg.get_payload(decode=True).decode()
                                if content_type == "text/html":
                                    html_body = payload
                                else:
                                    body = payload
                            except:
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
                                "date": msg.get("Date"),
                                "account_email": email_user,
                            }
                        )

            mail.close()
            mail.logout()
            return emails_data

        except Exception as e:
            print(f"❌ IMAP Error: {e}")
            return []
