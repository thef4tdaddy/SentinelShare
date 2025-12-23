import os
from datetime import datetime, timedelta, timezone

from apscheduler.schedulers.background import BackgroundScheduler  # type: ignore
from backend.database import engine
from backend.models import ProcessedEmail, ProcessingRun
from backend.security import encrypt_content
from backend.services.detector import ReceiptDetector
from backend.services.email_service import EmailService
from backend.services.forwarder import EmailForwarder
from sqlmodel import Session, select

scheduler = BackgroundScheduler()


def redact_email(email):
    """
    Redacts the middle part of an email for safer logging, e.g. "j****e@domain.com"
    """
    if not isinstance(email, str) or "@" not in email:
        return "[REDACTED]"
    name, domain = email.split("@", 1)
    if len(name) <= 2:
        redacted = "*" * len(name)
    else:
        redacted = name[0] + "*" * (len(name) - 2) + name[-1]
    return f"{redacted}@{domain}"


def process_emails():
    # 0. Check for SECRET_KEY to ensure encryption services are available
    if not os.environ.get("SECRET_KEY"):
        print(
            "❌ SECRET_KEY not set. Skipping email processing to prevent encryption errors."
        )
        return

    print("🔄 Checking for new emails...")

    # Get the poll interval for tracking
    poll_interval = int(os.environ.get("POLL_INTERVAL", "60"))

    # Initialize run_id to None in case of early exception
    run_id = None

    # Create a processing run record
    try:
        with Session(engine) as session:
            processing_run = ProcessingRun(
                started_at=datetime.now(timezone.utc),
                check_interval_minutes=poll_interval,
                status="running",
            )
            session.add(processing_run)
            session.commit()
            session.refresh(processing_run)
            run_id = processing_run.id
    except Exception as e:
        print(f"❌ Error creating processing run record: {type(e).__name__}")
        return

    all_emails = []
    emails_processed_count = 0
    emails_forwarded_count = 0
    error_occurred = False
    error_msg = None

    try:
        # 1. Fetch from all configured accounts using centralized logic
        accounts = EmailService.get_all_accounts()
        if accounts:
            print(f"👥 Processing {len(accounts)} accounts...")
            for i, acc in enumerate(accounts):
                user = acc.get("email")
                pwd = acc.get("password")
                server = acc.get("imap_server", "imap.gmail.com")

                if user and pwd:
                    print(f"   Scanning account #{i+1}...")
                    try:
                        fetched = EmailService.fetch_recent_emails(user, pwd, server)
                        # Tag each email with the source account
                        for email_data in fetched:
                            email_data["account_email"] = user
                        all_emails.extend(fetched)
                    except Exception as e:
                        # CodeQL: Avoid logging full exception as it may contain credentials
                        print(f"❌ Error parsing EMAIL_ACCOUNTS: {type(e).__name__}")
                        error_occurred = True
                        error_msg = f"Error scanning account #{i+1}: Connection failed ({type(e).__name__})"
        else:
            print("⚠️ No email accounts configured.")

        emails = all_emails

        if not emails:
            print("📭 No new emails.")
            # Update the processing run with zero emails
            with Session(engine) as session:
                run = session.get(ProcessingRun, run_id)
                if run:
                    run.completed_at = datetime.now(timezone.utc)
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
                    run.completed_at = datetime.now(timezone.utc)
                    run.emails_checked = len(emails)
                    run.emails_processed = 0
                    run.emails_forwarded = 0
                    run.status = "error"
                    run.error_message = error_msg
                    session.add(run)
                    session.commit()
                return

            for email_data in emails:
                try:
                    # Check if already processed (deduplication by Message-ID)
                    msg_id = email_data.get("message_id")
                    if msg_id:
                        existing = session.exec(
                            select(ProcessedEmail).where(
                                ProcessedEmail.email_id == msg_id
                            )
                        ).first()
                        if existing:
                            print(f"⚠️ Email {msg_id} already processed. Skipping.")
                            continue

                    # This is a new email to process
                    emails_processed_count += 1

                    # Get the account this email belongs to
                    account_email = email_data.get("account_email", "unknown")

                    # Checks for Command (Reply from Wife)
                    from backend.services.command_service import CommandService

                    if CommandService.is_command_email(email_data):
                        print(
                            f"   💬 Detected command email from {email_data.get('from')}"
                        )
                        if CommandService.process_command(email_data):
                            status = "command_executed"
                            reason = "User command"
                        else:
                            status = "ignored"
                            reason = "Command from wife (no action)"

                        # Log it (with encryption and retention if needed, though commands usually don't need body retention)
                        processed = ProcessedEmail(
                            email_id=msg_id or "unknown",
                            subject=email_data.get("subject", ""),
                            sender=email_data.get("from", ""),
                            received_at=datetime.now(timezone.utc),
                            processed_at=datetime.now(timezone.utc),
                            status=status,
                            account_email=account_email,
                            category="command",
                            reason=reason,
                            retention_expires_at=datetime.now(timezone.utc)
                            + timedelta(hours=24),
                            encrypted_body=encrypt_content(email_data.get("body", "")),
                            encrypted_html=encrypt_content(
                                email_data.get("html_body", "")
                            ),
                        )
                        session.add(processed)
                        session.commit()
                        print(f"✅ Command processed with status: {status}")
                        continue

                    # Detect (passing session for manual rules/preferences)
                    is_receipt = ReceiptDetector.is_receipt(email_data, session=session)
                    category = ReceiptDetector.categorize_receipt(email_data)

                    # Shadow Mode Testing (Learning)
                    from backend.services.learning_service import LearningService

                    LearningService.run_shadow_mode(session, email_data)

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
                        received_at=datetime.now(timezone.utc),  # Approximate
                        processed_at=datetime.now(timezone.utc),
                        status=status,
                        account_email=account_email,
                        category=category,
                        reason=reason,
                        retention_expires_at=datetime.now(timezone.utc)
                        + timedelta(hours=24),
                        encrypted_body=encrypt_content(email_data.get("body", "")),
                        encrypted_html=encrypt_content(email_data.get("html_body", "")),
                    )
                    session.add(processed)
                    session.commit()
                    print(f"💾 Saved status: {status} (Account: {account_email})")

                except Exception as e:
                    import traceback

                    print(
                        f"❌ Error processing individual email {email_data.get('subject', 'unknown')}: {e}"
                    )
                    traceback.print_exc()
                    # Close and replace the session to avoid a broken session affecting subsequent emails
                    session.close()
                    session = Session(engine)
                    # Mark that an error occurred during this run and update error message
                    error_occurred = True
                    subject = email_data.get("subject", "unknown")
                    if error_msg:
                        error_msg += f"; error processing email '{subject}'"
                    else:
                        error_msg = f"Error processing email '{subject}'"
                    # Continue to next email

            # Update the processing run with final counts
            run = session.get(ProcessingRun, run_id)
            if run:
                run.completed_at = datetime.now(timezone.utc)
                run.emails_checked = len(emails)
                run.emails_processed = emails_processed_count
                run.emails_forwarded = emails_forwarded_count
                run.status = "error" if error_occurred else "completed"
                run.error_message = error_msg
                session.add(run)

                # Run rule promotion logic
                from backend.services.learning_service import LearningService

                LearningService.auto_promote_rules(session)

                session.commit()

    except Exception as e:
        print(f"❌ Error during email processing: {type(e).__name__}")
        # Update run with error only if run_id was successfully created
        if run_id is not None:
            with Session(engine) as session:
                run = session.get(ProcessingRun, run_id)
                if run:
                    run.completed_at = datetime.now(timezone.utc)
                    run.status = "error"
                    run.error_message = str(e)
                    session.add(run)
                    session.commit()


def start_scheduler():
    poll_interval = int(os.environ.get("POLL_INTERVAL", "60"))
    scheduler.add_job(process_emails, "interval", minutes=poll_interval)
    # Register the cleanup job
    scheduler.add_job(cleanup_expired_emails, "interval", hours=1)
    scheduler.start()
    print(f"⏰ Scheduler started. Polling every {poll_interval} minutes.")


def cleanup_expired_emails():
    """Cleanup encrypted bodies and HTML for emails older than 24 hours."""
    print("🧹 Cleaning up expired email bodies...")
    try:
        with Session(engine) as session:
            now = datetime.now(timezone.utc)
            expired_emails = session.exec(
                select(ProcessedEmail).where(ProcessedEmail.retention_expires_at < now)
            ).all()

            count = 0
            for email in expired_emails:
                if email.encrypted_body or email.encrypted_html:
                    email.encrypted_body = None
                    email.encrypted_html = None
                    session.add(email)
                    count += 1

            session.commit()
            if count > 0:
                print(f"✅ Cleaned up {count} expired email bodies.")
    except Exception as e:
        print(f"❌ Error during cleanup: {type(e).__name__}")


def stop_scheduler():
    scheduler.shutdown()
    print("🛑 Scheduler stopped.")
