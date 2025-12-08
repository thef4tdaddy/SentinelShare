import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.message import EmailMessage

class EmailForwarder:
    @staticmethod
    def forward_email(original_email_data: dict, target_email: str):
        sender_email = os.environ.get("SENDER_EMAIL")
        password = os.environ.get("SENDER_PASSWORD")
        smtp_server = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
        smtp_port = 587

        if not sender_email or not password:
            print("❌ SMTP Credentials missing")
            return False

        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = target_email
        msg['Subject'] = f"Fwd: {original_email_data.get('subject', 'No Subject')}"

        # Create body
        body_text = f"Forwarding receipt from {original_email_data.get('from')}:\n\n"
        body_text += original_email_data.get('body', '')
        
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
