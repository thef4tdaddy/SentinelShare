import os

from backend.database import engine
from backend.models import Preference
from sqlmodel import Session, select


class CommandService:
    @staticmethod
    def is_command_email(email_data: dict) -> bool:
        """
        Check if the email is a command from the authorized wife email.
        """
        sender = (email_data.get("from") or "").lower()
        wife_email = (os.environ.get("WIFE_EMAIL") or "").lower()

        if not wife_email:
            return False

        return wife_email in sender

    @staticmethod
    def process_command(email_data: dict) -> bool:
        """
        Parse and execute commands from the email body.
        Returns True if a command was found and executed.
        """
        body = (email_data.get("body") or "").strip()
        (email_data.get("subject") or "").strip()

        # Simple parser: Look for specific keywords at the start of lines or arguably just the first word
        # supported: STOP <item>, MORE <item>, SETTINGS

        lines = body.split("\n")
        command_executed = False

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Basic tokenization
            parts = line.split()
            if not parts:
                continue

            cmd = parts[0].upper()
            args = " ".join(parts[1:]) if len(parts) > 1 else ""

            if cmd == "STOP":
                if args:
                    CommandService._add_preference(args, "Blocked Sender")
                    CommandService._send_confirmation(
                        f"🚫 Blocked sender/category: {args}"
                    )
                    command_executed = True
                    break  # Only process one command per email for safety?

            elif cmd == "MORE":
                if args:
                    CommandService._add_preference(args, "Always Forward")
                    CommandService._send_confirmation(f"✅ Always forwarding: {args}")
                    command_executed = True
                    break

            elif cmd == "SETTINGS":
                CommandService._send_settings_summary()
                command_executed = True
                break

        return command_executed

    @staticmethod
    def _add_preference(item: str, type_: str):
        with Session(engine) as session:
            # Check for existing
            existing = session.exec(
                select(Preference).where(
                    Preference.item == item, Preference.type == type_
                )
            ).first()

            if not existing:
                pref = Preference(item=item, type=type_)
                session.add(pref)
                session.commit()
                print(f"⚙️ Preference added: {type_} -> {item}")
            else:
                print(f"⚙️ Preference already exists: {type_} -> {item}")

    @staticmethod
    def _send_confirmation(message: str):
        target_email = os.environ.get("WIFE_EMAIL")
        if not target_email:
            return

        # We reuse EmailForwarder logic but maybe need a simpler 'send_email' method.
        # Check if EmailForwarder supports generic sending or if we need to hack it.
        # Looking at forwarder.py would be good, but assuming we can construct a simple email.
        # For now, we'll try to use a simplified version of forwarding or just use smtp directly
        # But actually, let's see if we can add a 'send_notification' to EmailForwarder or here.

        # Re-implementing basic send here to avoid tight coupling if Forwarder is strict
        import smtplib
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText

        sender_email = os.environ.get("GMAIL_EMAIL")
        password = os.environ.get("GMAIL_PASSWORD")
        smtp_server = "smtp.gmail.com"
        smtp_port = 587

        try:
            msg = MIMEMultipart()
            msg["From"] = sender_email or ""
            msg["To"] = target_email
            msg["Subject"] = "SentinelShare Command Confirmed"

            msg.attach(MIMEText(message, "plain"))

            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(sender_email or "", password or "")
                server.send_message(msg)
                print(f"📨 Confirmation sent to {target_email}")
        except Exception as e:
            print(f"❌ Failed to send confirmation: {type(e).__name__}")

    @staticmethod
    def _send_settings_summary():
        with Session(engine) as session:
            prefs = session.exec(select(Preference)).all()

        lines = ["Current Preferences:"]
        for p in prefs:
            lines.append(f"- {p.type}: {p.item}")

        if not prefs:
            lines.append("No active preferences.")

        CommandService._send_confirmation("\n".join(lines))
