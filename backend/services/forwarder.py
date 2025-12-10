import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.message import EmailMessage
from sqlmodel import Session, select
from backend.database import engine
from backend.models import GlobalSettings
from backend.constants import DEFAULT_EMAIL_TEMPLATE

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
                        if "gmail" in imap_s:
                            smtp_server = "smtp.gmail.com"
                        elif "mail.me.com" in imap_s or "icloud" in imap_s:
                            smtp_server = "smtp.mail.me.com"
                        elif imap_s.startswith("imap."):
                            # Try guessing smtp.domain
                            smtp_server = imap_s.replace("imap.", "smtp.", 1)
            except:
                pass

        if not sender_email or not password:
            print("❌ SMTP Credentials missing (SENDER_EMAIL or EMAIL_ACCOUNTS)")
            return False

        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = target_email
        msg['Subject'] = f"Fwd: {original_email_data.get('subject', 'No Subject')}"

        # Get template from database
        template = DEFAULT_EMAIL_TEMPLATE
        try:
            with Session(engine) as session:
                setting = session.exec(
                    select(GlobalSettings).where(GlobalSettings.key == "email_template")
                ).first()
                if setting:
                    template = setting.value
        except:
            pass  # Use default template if DB access fails
        
        # Create body by substituting variables in template
        body_text = template
        body_text = body_text.replace('{subject}', original_email_data.get('subject', 'No Subject'))
        body_text = body_text.replace('{from}', original_email_data.get('from', ''))
        body_text = body_text.replace('{body}', original_email_data.get('body', ''))
        
        msg.attach(MIMEText(body_text, 'plain'))

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
