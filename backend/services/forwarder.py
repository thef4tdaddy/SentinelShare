import hashlib
import hmac
import os
import smtplib
import urllib.parse
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from urllib.parse import urlparse

from backend.constants import DEFAULT_EMAIL_TEMPLATE
from backend.database import engine
from backend.models import GlobalSettings
from backend.services.email_service import EmailService
from sqlmodel import Session, select


class EmailForwarder:
    @staticmethod
    def forward_email(original_email_data: dict, target_email: str):
        sender_email = os.environ.get("SENDER_EMAIL")
        password = os.environ.get("SENDER_PASSWORD")
        smtp_server = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
        smtp_port = 587

        if not sender_email or not password:
            # Fallback to centralized account logic
            accounts = EmailService.get_all_accounts()
            if accounts:
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

        if not sender_email or not password:
            print("❌ SMTP Credentials missing (SENDER_EMAIL or EMAIL_ACCOUNTS)")
            return False

        msg = MIMEMultipart()
        msg["From"] = sender_email
        msg["To"] = target_email
        msg["Subject"] = f"Fwd: {original_email_data.get('subject', 'No Subject')}"

        # Helper to extract a simple name for commands (e.g. "Amazon" from "Amazon.com")
        from_header = original_email_data.get("from", "")
        simple_name = "Sender"
        if "@" in from_header:
            try:
                # Extract domain part "amazon.com"
                domain = from_header.split("@")[1].split(">")[0].strip()
                # Extract main name "amazon"
                simple_name = domain.split(".")[0].capitalize()
            except Exception:
                pass

        # Prepare content
        body_content = original_email_data.get("body", "")
        raw_html_body = original_email_data.get("html_body")

        if raw_html_body and len(raw_html_body.strip()) > 0:
            # Use the original HTML
            # Check if it's a full document (has <html> tag)
            # If our template wraps it in another <html>, we might want to strip the original outer tags
            # But specific complex parsing is risky. Most clients render nested HTML okay.
            body_content_html = raw_html_body
        else:
            # Basic HTML newline replacement for safety if plain text is passed
            body_content_html = body_content.replace(chr(10), "<br>")

        # Construct Action Links
        app_url = os.environ.get("APP_URL")
        # Strip trailing slash if present
        if app_url and app_url.endswith("/"):
            app_url = app_url[:-1]

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

        link_stop = make_link("STOP", simple_name.lower())  # Args usually lowercase
        link_more = make_link("MORE", simple_name.lower())
        link_settings = make_link("SETTINGS", "")

        action_type_text = (
            "Clicking an action opens a web confirmation."
            if app_url
            else "Clicking an action opens your email app. Just hit Send!"
        )

        # Get template from database or default
        template = DEFAULT_EMAIL_TEMPLATE
        try:
            with Session(engine) as session:
                setting = session.exec(
                    select(GlobalSettings).where(GlobalSettings.key == "email_template")
                ).first()
                if setting and setting.value and len(setting.value.strip()) > 0:
                    template = setting.value
        except Exception:
            pass  # Use default template if DB access fails

        # Render Template
        # We use safe substitution or try/except to allow for missing keys in custom templates
        final_html = ""
        try:
            # First try standard formatting
            final_html = template.format(
                simple_name=simple_name,
                link_stop=link_stop,
                link_more=link_more,
                link_settings=link_settings,
                action_type_text=action_type_text,
                body=body_content_html,
                subject=original_email_data.get("subject", ""),
                **{
                    "from": from_header
                },  # 'from' is a keyword in python, so we pass it as dict
            )
        except (KeyError, ValueError):
            # Fallback for old templates or malformed ones: try to at least put the body in
            # Or revert to DEFAULT if custom failed
            print("⚠️ Custom template failed rendering, falling back to default.")
            try:
                final_html = DEFAULT_EMAIL_TEMPLATE.format(
                    simple_name=simple_name,
                    link_stop=link_stop,
                    link_more=link_more,
                    link_settings=link_settings,
                    action_type_text=action_type_text,
                    body=body_content_html,
                    subject=original_email_data.get("subject", ""),
                    **{"from": from_header},
                )
            except Exception:
                # Absolute fallback
                final_html = f"<html><body>{body_content_html}</body></html>"

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
            print(f"❌ Error forwarding email: {type(e).__name__}")
            return False
