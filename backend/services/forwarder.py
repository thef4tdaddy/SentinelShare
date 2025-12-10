import os
import smtplib
from email.message import EmailMessage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from urllib.parse import urlparse

from backend.constants import DEFAULT_EMAIL_TEMPLATE
from backend.database import engine
from backend.models import GlobalSettings
from sqlmodel import Session, select


class EmailForwarder:
    @staticmethod
    def forward_email(original_email_data: dict, target_email: str):
        sender_email = os.environ.get("SENDER_EMAIL")
        password = os.environ.get("SENDER_PASSWORD")
        smtp_server = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
        smtp_port = 587

        if not sender_email or not password:
            # Fallback to first account in EMAIL_ACCOUNTS
            import json

            try:
                accounts_json = os.environ.get("EMAIL_ACCOUNTS")
                if accounts_json:
                    accounts = json.loads(accounts_json)
                    if accounts and isinstance(accounts, list):
                        first_acc = accounts[0]
                        sender_email = first_acc.get("email")
                        password = first_acc.get("password")

                        # Infer SMTP server from IMAP if possible
                        imap_s = first_acc.get("imap_server", "")
                        # Parse hostname from imap_s, handling both URLs and plain hostnames
                        parsed = urlparse(imap_s)
                        hostname = parsed.hostname if parsed.hostname else imap_s
                        if hostname and (
                            hostname == "gmail.com" or hostname.endswith(".gmail.com")
                        ):
                            smtp_server = "smtp.gmail.com"
                        elif hostname and (
                            hostname == "mail.me.com"
                            or hostname.endswith(".mail.me.com")
                            or hostname == "icloud.com"
                            or hostname.endswith(".icloud.com")
                        ):
                            smtp_server = "smtp.mail.me.com"
                        elif hostname and hostname.startswith("imap."):
                            # Try guessing smtp.domain
                            smtp_server = hostname.replace("imap.", "smtp.", 1)
            except:
                pass

        if not sender_email or not password:
            print("❌ SMTP Credentials missing (SENDER_EMAIL or EMAIL_ACCOUNTS)")
            return False

        msg = MIMEMultipart()
        msg["From"] = sender_email
        msg["To"] = target_email
        msg["Subject"] = f"Fwd: {original_email_data.get('subject', 'No Subject')}"

        # Get template from database
        template = DEFAULT_EMAIL_TEMPLATE
        try:
            with Session(engine) as session:
                setting = session.exec(
                    select(GlobalSettings).where(GlobalSettings.key == "email_template")
                ).first()
                if setting:
                    template = setting.value
        except Exception:
            pass  # Use default template if DB access fails

        # Helper to extract a simple name for commands (e.g. "Amazon" from "Amazon.com")
        from_header = original_email_data.get("from", "")
        simple_name = "sender"
        if "@" in from_header:
            try:
                # Extract domain part "amazon.com"
                domain = from_header.split("@")[1].split(">")[0].strip()
                # Extract main name "amazon"
                simple_name = domain.split(".")[0]
            except:
                pass

        # Construct Action Links
        # Strategies:
        # 1. HTTP Links (preferred, requires APP_URL)
        # 2. Mailto Links (fallback)

        app_url = os.environ.get("APP_URL")
        # Strip trailing slash if present
        if app_url and app_url.endswith("/"):
            app_url = app_url[:-1]

        import hashlib
        import hmac
        import urllib.parse
        from datetime import datetime, timezone

        def make_link(command, arg):
            if app_url:
                # HTTP Link Strategy
                # /api/actions/quick?cmd=STOP&arg=amazon&ts=123&sig=abc
                ts = str(datetime.now(timezone.utc).timestamp())
                secret = os.environ.get(
                    "SECRET_KEY", "default-insecure-secret-please-change"
                )
                msg = f"{command}:{arg}:{ts}"
                sig = hmac.new(
                    secret.encode(), msg.encode(), hashlib.sha256
                ).hexdigest()

                params = {"cmd": command, "arg": arg, "ts": ts, "sig": sig}
                return f"{app_url}/api/actions/quick?{urllib.parse.urlencode(params)}"
            else:
                # Fallback to Mailto
                subject_re = f"Re: {original_email_data.get('subject', 'No Subject')}"
                if command == "SETTINGS":
                    body = "SETTINGS"
                else:
                    body = f"{command} {arg}\n\n(Sent via SentinelShare Quick Action)"

                params = {"subject": subject_re, "body": body}
                return f"mailto:{sender_email}?{urllib.parse.urlencode(params).replace('+', '%20')}"

        link_stop = make_link("STOP", simple_name)
        link_more = make_link("MORE", simple_name)
        link_settings = make_link("SETTINGS", "")  # No arg for settings

        # Create HTML Header
        # We need to detect if using mailto or http to change the footer text
        action_type_text = (
            "Clicking an action opens a web confirmation."
            if app_url
            else "Clicking an action opens your email app. Just hit Send!"
        )

        header_html = f"""
        <div style="font-family: sans-serif; background-color: #f4f4f5; padding: 16px; border-radius: 8px; margin-bottom: 20px; border: 1px solid #e4e4e7;">
            <div style="font-weight: bold; color: #18181b; margin-bottom: 12px; font-size: 16px;">
                🛡️ SentinelAction: {simple_name.capitalize()}
            </div>
            <div style="display: flex; gap: 10px; flex-wrap: wrap;">
                <a href="{link_stop}" style="text-decoration: none; background-color: #ef4444; color: white; padding: 8px 16px; border-radius: 6px; font-size: 14px; font-weight: 500;">
                    🚫 Block {simple_name.capitalize()}
                </a>
                <a href="{link_more}" style="text-decoration: none; background-color: #22c55e; color: white; padding: 8px 16px; border-radius: 6px; font-size: 14px; font-weight: 500;">
                    ✅ Always Forward
                </a>
                <a href="{link_settings}" style="text-decoration: none; background-color: #71717a; color: white; padding: 8px 16px; border-radius: 6px; font-size: 14px; font-weight: 500;">
                    ⚙️ Settings
                </a>
            </div>
            <div style="font-size: 11px; color: #71717a; margin-top: 12px;">
                {action_type_text}
            </div>
        </div>
        <hr style="border: 0; border-top: 1px solid #e5e7eb; margin: 20px 0;">
        """

        # Create body by substituting variables in template
        # We prefer HTML now.
        body_content = original_email_data.get("body", "")

        # If the original body is just plain text, wrap it. If it's HTML, prepend our header.
        # Ideally we want to send a proper HTML email.

        final_html = f"""
        <html>
            <body>
                {header_html}
                <div style="font-family: sans-serif;">
                    {body_content.replace(chr(10), "<br>")}
                </div>
            </body>
        </html>
        """

        # Attach HTML part
        msg.attach(MIMEText(final_html, "html"))
        # Also attach plain text fallback just in case
        msg.attach(
            MIMEText(
                f"[SentinelAction: Reply 'STOP {simple_name}' to block]\n\n{body_content}",
                "plain",
            )
        )

        try:
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(sender_email, password)
                server.send_message(msg)
            print(f"✅ Email forwarded to {target_email}")
            return True
        except Exception as e:
            print(f"❌ Error forwarding email: {e}")
            return False
