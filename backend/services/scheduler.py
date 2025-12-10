import os
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from backend.database import engine, get_session
from backend.models import ProcessedEmail, ProcessingRun
from backend.services.detector import ReceiptDetector
from backend.services.email_service import EmailService
from backend.services.forwarder import EmailForwarder
from sqlmodel import Session, select

scheduler = BackgroundScheduler()

import json


def process_emails():
    print("🔄 Checking for new emails...")

    # Get the poll interval for tracking
    poll_interval = int(os.environ.get("POLL_INTERVAL", "60"))

    # Initialize run_id to None in case of early exception
    run_id = None

    # Create a processing run record
    try:
        with Session(engine) as session:
            processing_run = ProcessingRun(
                started_at=datetime.utcnow(),
                check_interval_minutes=poll_interval,
                status="running",
            )
            session.add(processing_run)
            session.commit()
            session.refresh(processing_run)
            run_id = processing_run.id
    except Exception as e:
        print(f"❌ Error creating processing run record: {e}")
        return

    all_emails = []
    emails_processed_count = 0
    emails_forwarded_count = 0
    error_occurred = False
    error_msg = None

    try:
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
                            fetched = EmailService.fetch_recent_emails(
                                user, pwd, server
                            )
                            # Tag each email with the source account
                            for email_data in fetched:
                                email_data["account_email"] = user
                            all_emails.extend(fetched)
            except Exception as e:
                print(f"❌ Critical Error parsing EMAIL_ACCOUNTS JSON: {e}")
                print(f"   Raw Value: [REDACTED]")
                error_occurred = True
                error_msg = f"JSON parsing error: {str(e)}"

        # 2. Fallback to Legacy Single Account (if no accounts processed yet)
        if not all_emails and not email_accounts_json:
            user = os.environ.get("GMAIL_EMAIL")
            pwd = os.environ.get("GMAIL_PASSWORD")
            server = os.environ.get("IMAP_SERVER", "imap.gmail.com")

            if user and pwd:
                print(f"👤 Processing single account {user}...")
                fetched = EmailService.fetch_recent_emails(user, pwd, server)
                # Tag each email with the source account
                for email_data in fetched:
                    email_data["account_email"] = user
                all_emails = fetched

        emails = all_emails

        if not emails:
            print("📭 No new emails.")
            # Update the processing run with zero emails
            with Session(engine) as session:
                run = session.get(ProcessingRun, run_id)
                if run:
                    run.completed_at = datetime.utcnow()
                    run.emails_checked = 0
                    run.emails_processed = 0
                    run.emails_forwarded = 0
                    # Preserve error status if there was an error during processing
                    run.status = "error" if error_occurred else "completed"
                    run.error_message = error_msg if error_occurred else None
                    session.add(run)
                    session.commit()
            return

        with Session(engine) as session:
            # Check target email (Wife)
            target_email = os.environ.get("WIFE_EMAIL")
            if not target_email:
                print("❌ WIFE_EMAIL not set, cannot forward.")
                error_msg = "WIFE_EMAIL not configured"
                # Update run with error
                run = session.get(ProcessingRun, run_id)
                if run:
                    run.completed_at = datetime.utcnow()
                    run.emails_checked = len(emails)
                    run.emails_processed = 0
                    run.emails_forwarded = 0
                    run.status = "error"
                    run.error_message = error_msg
                    session.add(run)
                    session.commit()
                return

            for email_data in emails:
                # Check if already processed (deduplication by Message-ID)
                msg_id = email_data.get("message_id")
                if msg_id:
                    existing = session.exec(
                        select(ProcessedEmail).where(ProcessedEmail.email_id == msg_id)
                    ).first()
                    if existing:
                        print(f"⚠️ Email {msg_id} already processed. Skipping.")
                        continue

                # This is a new email to process
                emails_processed_count += 1

                # Get the account this email belongs to
                account_email = email_data.get("account_email", "unknown")

                # Detect
                is_receipt = ReceiptDetector.is_receipt(email_data)
                category = ReceiptDetector.categorize_receipt(email_data)

                print(
                    f"   🔍 Analyzing: {email_data.get('subject')} | From: {email_data.get('from')}"
                )
                print(f"      -> Is Receipt: {is_receipt} | Category: {category}")

                status = "ignored"
                reason = "Not a receipt"

                if is_receipt:
                    # Forward
                    print(f"      🚀 Forwarding to {target_email}...")
                    success = EmailForwarder.forward_email(email_data, target_email)
                    status = "forwarded" if success else "error"
                    reason = "Detected as receipt" if success else "SMTP Error"
                    if success:
                        emails_forwarded_count += 1

                # Save to DB
                processed = ProcessedEmail(
                    email_id=msg_id or "unknown",
                    subject=email_data.get("subject", ""),
                    sender=email_data.get("from", ""),
                    received_at=datetime.utcnow(),  # Approximate
                    processed_at=datetime.utcnow(),
                    status=status,
                    account_email=account_email,
                    category=category,
                    reason=reason,
                )
                session.add(processed)
                session.commit()
                print(f"💾 Saved email status: {status} (Account: {account_email})")

            # Update the processing run with final counts
            run = session.get(ProcessingRun, run_id)
            if run:
                run.completed_at = datetime.utcnow()
                run.emails_checked = len(emails)
                run.emails_processed = emails_processed_count
                run.emails_forwarded = emails_forwarded_count
                run.status = "error" if error_occurred else "completed"
                run.error_message = error_msg
                session.add(run)
                session.commit()

    except Exception as e:
        print(f"❌ Error during email processing: {e}")
        # Update run with error only if run_id was successfully created
        if run_id is not None:
            with Session(engine) as session:
                run = session.get(ProcessingRun, run_id)
                if run:
                    run.completed_at = datetime.utcnow()
                    run.status = "error"
                    run.error_message = str(e)
                    session.add(run)
                    session.commit()


def start_scheduler():
    poll_interval = int(os.environ.get("POLL_INTERVAL", "60"))
    scheduler.add_job(process_emails, "interval", minutes=poll_interval)
    scheduler.start()
    print(f"⏰ Scheduler started. Polling every {poll_interval} minutes.")


def stop_scheduler():
    scheduler.shutdown()
    print("🛑 Scheduler stopped.")
