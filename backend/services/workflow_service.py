"""Service for workflow operations like manual overrides and rule creation."""

import json
import os
from datetime import datetime, timezone
from email.utils import parseaddr
from typing import Any, Dict

from sqlmodel import Session, select

from backend.constants import DEFAULT_MANUAL_RULE_PRIORITY
from backend.models import ManualRule, Preference, ProcessedEmail
from backend.security import encrypt_content, get_email_content_hash
from backend.services.detector import ReceiptDetector
from backend.services.email_service import EmailService
from backend.services.forwarder import EmailForwarder


class WorkflowService:
    """Service for managing email workflows and manual overrides."""

    @staticmethod
    def toggle_to_ignored(email_id: int, session: Session) -> Dict[str, Any]:
        """Toggle a forwarded or blocked email back to ignored status."""
        # Get the email
        email = session.get(ProcessedEmail, email_id)
        if not email:
            raise ValueError("Email not found")

        # Check if email is forwarded or blocked
        if email.status not in ["forwarded", "blocked"]:
            raise ValueError(
                f"Email status is '{email.status}'. Only 'forwarded' or 'blocked' emails can be changed to 'ignored'"
            )

        # Update email status to ignored
        previous_status = email.status
        email.status = "ignored"
        email.reason = f"Manually changed from {previous_status} to ignored"

        session.add(email)
        session.commit()
        session.refresh(email)

        return {
            "success": True,
            "email": email,
            "message": f"Email status changed from {previous_status} to ignored",
        }

    @staticmethod
    def toggle_ignored_to_forwarded(email_id: int, session: Session) -> Dict[str, Any]:
        """Toggle an ignored email: create a manual rule and forward the email."""
        # Get the email
        email = session.get(ProcessedEmail, email_id)
        if not email:
            raise ValueError("Email not found")

        # Check if email is ignored
        if email.status != "ignored":
            raise ValueError(f"Email status is '{email.status}', not 'ignored'")

        # Create a manual rule based on the email sender
        sender = email.sender or ""
        _, email_pattern = parseaddr(sender)

        if not email_pattern or "@" not in email_pattern:
            raise ValueError("Could not extract email pattern from sender")

        # Normalize to lowercase for consistency
        email_pattern = email_pattern.lower().strip()

        # Check if a manual rule with the same email_pattern already exists
        existing_rule = session.exec(
            select(ManualRule).where(ManualRule.email_pattern == email_pattern)
        ).first()

        rule_is_new = False
        if not existing_rule:
            # Truncate subject intelligently with ellipsis
            subj = email.subject or ""
            truncated_subject = subj[:47] + "..." if len(subj) > 50 else subj
            manual_rule = ManualRule(
                email_pattern=email_pattern,
                subject_pattern=None,
                priority=DEFAULT_MANUAL_RULE_PRIORITY,
                purpose=f"Auto-created from ignored email: {truncated_subject}",
            )
            session.add(manual_rule)
            rule_is_new = True
        else:
            manual_rule = existing_rule

        # Forward the email now
        target_email = os.environ.get("WIFE_EMAIL")
        if not target_email:
            session.rollback()
            raise ValueError("WIFE_EMAIL not configured")

        # Fetch original email content
        email_content = WorkflowService._fetch_email_content(email, session)

        # Prepare email data for forwarding
        email_data = {
            "message_id": email.email_id,
            "subject": email.subject,
            "from": email.sender,
            "body": email_content,
            "account_email": email.account_email,
            "date": email.received_at,
        }

        # Try to forward the email
        success = EmailForwarder.forward_email(email_data, target_email)

        if not success:
            session.rollback()
            raise ValueError("Failed to forward email")

        # Update email status to forwarded
        email.status = "forwarded"
        email.reason = "Manually toggled from ignored"

        # Commit changes
        session.add(email)
        session.commit()
        session.refresh(email)
        # Only refresh the rule if it was newly created in this transaction
        if rule_is_new:
            session.refresh(manual_rule)

        return {
            "success": True,
            "email": email,
            "rule": manual_rule,
            "message": f"Email forwarded and rule created for {email_pattern}",
        }

    @staticmethod
    def _fetch_email_content(email: ProcessedEmail, session: Session) -> str:
        """Fetch email content from storage or IMAP."""
        # 1. Get credentials for the source account
        creds = EmailService.get_credentials_for_account(str(email.account_email))

        if not creds:
            # Fallback to SENDER_EMAIL if specific account not found
            email_user = os.environ.get("SENDER_EMAIL")
            email_pass = os.environ.get("SENDER_PASSWORD")
            imap_server = "imap.gmail.com"
            print(
                f"⚠️ Account not found for {email.account_email}, falling back to SENDER_EMAIL"
            )
        else:
            email_user = creds["email"]
            email_pass = creds["password"]
            imap_server = creds["imap_server"]

        first_attempt_user = email_user

        # 2. Fetch content
        original_content = None
        if email_user and email_pass:
            print(f"DEBUG: Fetching email {email.email_id} for [REDACTED_ACCOUNT]")
            original_content = EmailService.fetch_email_by_id(
                email_user, email_pass, email.email_id, imap_server
            )

        # 2b. Universal Fallback: If not found, try all other accounts
        if not original_content:
            print("DEBUG: Email not found in initial account, trying all accounts...")
            try:
                accounts_json = os.environ.get("EMAIL_ACCOUNTS")
                if accounts_json:
                    accounts = json.loads(accounts_json)
                    for acc in accounts:
                        fallback_user = acc.get("email")
                        fallback_pass = acc.get("password")
                        fallback_server = acc.get("imap_server", "imap.gmail.com")

                        # Skip if already tried
                        if fallback_user == first_attempt_user:
                            continue

                        if fallback_user and fallback_pass:
                            print(
                                f"DEBUG: Fallback attempt for {email.email_id} on account [REDACTED_ACCOUNT]"
                            )
                            original_content = EmailService.fetch_email_by_id(
                                fallback_user,
                                fallback_pass,
                                email.email_id,
                                fallback_server,
                            )
                            if original_content:
                                print(
                                    "DEBUG: Found email in fallback account: [REDACTED_ACCOUNT]"
                                )
                                break
            except Exception as e:
                print(f"DEBUG: Fallback iteration error: {e}")

        # 3. Construct body
        if original_content:
            # Use the fetched content
            final_body = f"""<div style="background-color: #f0fdf4; padding: 10px; border: 1px solid #86efac; margin-bottom: 20px; border-radius: 6px;">
                <p><strong>[SentinelShare Notification]</strong></p>
                <p>This email was previously marked as <strong>{email.status}</strong> and is now being forwarded per your request.</p>
                <p><strong>Reason:</strong> {email.reason or 'Not a receipt'}</p>
                <p><em>A manual rule has been created to forward future emails from this sender.</em></p>
            </div>
            <hr>
            {original_content.get("html_body") or original_content.get("body")}
            """
        else:
            # Fallback to placeholder
            final_body = f"""[This email was previously marked as ignored and is now being forwarded]

Originally received: {email.received_at.strftime('%Y-%m-%d %H:%M:%S UTC') if email.received_at else 'Unknown'}
Category: {email.category or 'Unknown'}
Reason for initial ignore: {email.reason or 'Not a receipt'}

Note: Original email body is not available as it was not stored and could not be fetched from the server.
A manual rule has been created to forward future emails from this sender."""

        return final_body

    @staticmethod
    def upload_receipt(
        file_content: bytes,
        filename: str,
        content_type: str,
        session: Session,
    ) -> Dict[str, Any]:
        """Upload a receipt file and process it as a manual upload."""
        # Create receipts directory if it doesn't exist
        receipts_dir = os.path.join("data", "receipts")
        os.makedirs(receipts_dir, exist_ok=True)

        # Generate unique filename with timestamp
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")

        # Map content type to safe file extension
        extension_map = {
            "application/pdf": ".pdf",
            "image/png": ".png",
            "image/jpeg": ".jpg",
        }
        file_extension = extension_map.get(content_type, ".pdf")

        safe_filename = f"manual_{timestamp}{file_extension}"
        file_path = os.path.join(receipts_dir, safe_filename)

        # Save file to disk
        try:
            with open(file_path, "wb") as f:
                f.write(file_content)
        except Exception as e:
            raise ValueError(f"Failed to save file: {str(e)}")

        # Create a ProcessedEmail record for the manual upload
        file_content_hash = get_email_content_hash(
            {"body": safe_filename, "subject": filename or "Manual Upload"}
        )

        # For manual uploads, run categorization
        mock_email_data = {
            "subject": f"Manual Upload: {filename}",
            "body": f"File: {safe_filename}",
            "sender": "manual_upload",
        }

        category = ReceiptDetector.categorize_receipt(mock_email_data)

        processed = ProcessedEmail(
            email_id=f"manual_{timestamp}",
            subject=filename or "Manual Upload",
            sender="manual_upload",
            received_at=datetime.now(timezone.utc),
            processed_at=datetime.now(timezone.utc),
            status="manual_upload",
            account_email="manual",
            category=category,
            reason=f"Manual upload: {file_path}",
            content_hash=file_content_hash,
            encrypted_body=encrypt_content(f"File path: {file_path}"),
            encrypted_html=None,
        )

        try:
            session.add(processed)
            session.commit()
            session.refresh(processed)
        except Exception as e:
            # Cleanup file if DB insert fails
            if os.path.exists(file_path):
                os.remove(file_path)
            raise ValueError(f"Failed to create database record: {str(e)}")

        return {
            "success": True,
            "file_path": file_path,
            "record_id": processed.id,
            "message": f"Receipt uploaded successfully: {filename}",
        }

    @staticmethod
    def update_preferences(
        blocked_senders: list[str],
        allowed_senders: list[str],
        session: Session,
    ) -> Dict[str, Any]:
        """Update preferences via bulk replace."""
        try:
            # 1. Remove existing Blocked/Allowed preferences
            from sqlmodel import col

            existing = session.exec(
                select(Preference).where(
                    col(Preference.type).in_(["Blocked Sender", "Always Forward"])
                )
            ).all()
            for p in existing:
                session.delete(p)

            # 2. Add new Blocked Senders
            for item in blocked_senders:
                session.add(Preference(item=item, type="Blocked Sender"))

            # 3. Add new Allowed Senders
            for item in allowed_senders:
                session.add(Preference(item=item, type="Always Forward"))

            session.commit()
            return {"success": True, "message": "Preferences updated"}

        except Exception as e:
            session.rollback()
            raise ValueError(str(e))
