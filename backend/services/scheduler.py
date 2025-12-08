from apscheduler.schedulers.background import BackgroundScheduler
from backend.services.email_service import EmailService
from backend.services.detector import ReceiptDetector
from backend.services.forwarder import EmailForwarder
from backend.database import get_session, engine
from backend.models import ProcessedEmail, GlobalSettings
from sqlmodel import Session, select
import os
from datetime import datetime

scheduler = BackgroundScheduler()

import json

def process_emails():
    print("🔄 Checking for new emails...")
    
    all_emails = []
    
    # 1. Try Multi-Account Config
    email_accounts_json = os.environ.get("EMAIL_ACCOUNTS")
    if email_accounts_json:
        try:
            accounts = json.loads(email_accounts_json)
            if isinstance(accounts, list):
                print(f"👥 Processing {len(accounts)} accounts...")
                for acc in accounts:
                    user = acc.get("email")
                    pwd = acc.get("password")
                    server = acc.get("imap_server", "imap.gmail.com")
                    
                    if user and pwd:
                        print(f"   Scanning {user}...")
                        fetched = EmailService.fetch_unseen_emails(user, pwd, server)
                        all_emails.extend(fetched)
        except json.JSONDecodeError:
            print("❌ Error parsing EMAIL_ACCOUNTS JSON")

    # 2. Fallback to Legacy Single Account (if no accounts processed yet)
    if not all_emails and not email_accounts_json:
        user = os.environ.get("GMAIL_EMAIL")
        pwd = os.environ.get("GMAIL_PASSWORD")
        server = os.environ.get("IMAP_SERVER", "imap.gmail.com")
        
        if user and pwd:
             print(f"👤 Processing single account {user}...")
             all_emails = EmailService.fetch_unseen_emails(user, pwd, server)
    
    emails = all_emails
    
    if not emails:
        print("📭 No new emails.")
        return

    with Session(engine) as session:
        # Check target email (Wife)
        target_email = os.environ.get("WIFE_EMAIL")
        if not target_email:
            print("❌ WIFE_EMAIL not set, cannot forward.")
            return

        for email_data in emails:
            # Check if already processed (deduplication by Message-ID)
            msg_id = email_data.get("message_id")
            if msg_id:
                existing = session.exec(select(ProcessedEmail).where(ProcessedEmail.email_id == msg_id)).first()
                if existing:
                    print(f"⚠️ Email {msg_id} already processed. Skipping.")
                    continue
            
            # Detect
            is_receipt = ReceiptDetector.is_receipt(email_data)
            category = ReceiptDetector.categorize_receipt(email_data)
            
            status = "ignored"
            reason = "Not a receipt"
            
            if is_receipt:
                # Forward
                success = EmailForwarder.forward_email(email_data, target_email)
                status = "forwarded" if success else "error"
                reason = "Detected as receipt" if success else "SMTP Error"
            
            # Save to DB
            processed = ProcessedEmail(
                email_id=msg_id or "unknown",
                subject=email_data.get("subject", ""),
                sender=email_data.get("from", ""),
                received_at=datetime.utcnow(), # Approximate
                processed_at=datetime.utcnow(),
                status=status,
                category=category,
                reason=reason
            )
            session.add(processed)
            session.commit()
            print(f"💾 Saved email status: {status}")

def start_scheduler():
    poll_interval = int(os.environ.get("POLL_INTERVAL", "60"))
    scheduler.add_job(process_emails, 'interval', minutes=poll_interval)
    scheduler.start()
    print(f"⏰ Scheduler started. Polling every {poll_interval} minutes.")

def stop_scheduler():
    scheduler.shutdown()
    print("🛑 Scheduler stopped.")
