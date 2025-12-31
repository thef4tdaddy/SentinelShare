"""Service for generating reports and managing email history operations."""

import csv
import io
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from sqlmodel import Session, and_, func, select

from backend.models import CategoryRule, ManualRule, ProcessedEmail
from backend.security import decrypt_content, sanitize_csv_field
from backend.services.detector import ReceiptDetector
from backend.services.email_service import EmailService
from backend.services.forwarder import EmailForwarder

# Constants
RUN_GROUPING_WINDOW_SECONDS = 300  # 5 minutes
DEFAULT_CURRENCY = "USD"


class ReportService:
    """Service for email history reports and analytics."""

    @staticmethod
    def apply_email_filters(
        query,
        filters: List[Any],
        status: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        sender: Optional[str] = None,
        min_amount: Optional[float] = None,
        max_amount: Optional[float] = None,
    ):
        """Apply standard email filters to a query."""
        if status:
            filters.append(ProcessedEmail.status == status)
        if date_from:
            filters.append(ProcessedEmail.processed_at >= date_from)  # type: ignore
        if date_to:
            filters.append(ProcessedEmail.processed_at <= date_to)  # type: ignore
        if sender and sender.strip():
            # Case-insensitive partial match for sender; escape SQL wildcard characters
            sender_escaped = (
                sender.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            )
            filters.append(
                ProcessedEmail.sender.ilike(f"%{sender_escaped}%", escape="\\")  # type: ignore[union-attr]
            )
        if min_amount is not None:
            filters.append(ProcessedEmail.amount >= min_amount)  # type: ignore
        if max_amount is not None:
            filters.append(ProcessedEmail.amount <= max_amount)  # type: ignore

        if filters:
            query = query.where(and_(*filters))

        return query

    @staticmethod
    def get_paginated_emails(
        session: Session,
        page: int = 1,
        per_page: int = 50,
        status: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        sender: Optional[str] = None,
        min_amount: Optional[float] = None,
        max_amount: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Get paginated email history with optional filtering."""
        # Build query
        query = select(ProcessedEmail)
        filters: List[Any] = []

        # Apply filters
        query = ReportService.apply_email_filters(
            query,
            filters,
            status,
            date_from,
            date_to,
            sender,
            min_amount,
            max_amount,
        )

        # Order by processed_at descending
        query = query.order_by(ProcessedEmail.processed_at.desc())  # type: ignore

        # Get total count
        count_query = select(func.count()).select_from(ProcessedEmail)
        if filters:
            count_query = count_query.where(and_(*filters))
        total = session.exec(count_query).one()

        # Apply pagination
        offset = (page - 1) * per_page
        query = query.offset(offset).limit(per_page)

        emails = session.exec(query).all()

        return {
            "emails": emails,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total,
                "total_pages": (total + per_page - 1) // per_page,
            },
        }

    @staticmethod
    def reprocess_email(email_id: int, session: Session) -> Dict[str, Any]:
        """Re-analyze a specific email using current rules and logic."""
        email = session.get(ProcessedEmail, email_id)
        if not email:
            raise ValueError("Email not found")

        # 1. Get content from encrypted storage
        body = decrypt_content(email.encrypted_body) if email.encrypted_body else ""
        html_body = decrypt_content(email.encrypted_html) if email.encrypted_html else ""

        # 2. Fallback to IMAP if content is gone (retention expired)
        if not body and not html_body:
            acc_email = email.account_email or ""
            creds = EmailService.get_credentials_for_account(acc_email)
            if not creds:
                raise ValueError(
                    "Cannot fallback to IMAP: Credentials missing for this account"
                )

            fetched = EmailService.fetch_email_by_id(
                email.account_email, creds["password"], email.email_id, creds["imap_server"]
            )
            if not fetched:
                raise ValueError("Email not found in IMAP inbox")

            body = fetched.get("body", "")
            html_body = fetched.get("html_body", "")

        # 3. Analyze
        email_data = {
            "subject": email.subject,
            "from": email.sender,
            "body": body,
            "html_body": html_body,
        }

        analysis = ReceiptDetector.debug_is_receipt(email_data, session=session)
        category = ReceiptDetector.categorize_receipt(email_data)

        return {
            "analysis": analysis,
            "category": category,
            "current_status": email.status,
            "suggested_status": "forwarded" if analysis["final_decision"] else "blocked",
        }

    @staticmethod
    def submit_feedback(email_id: int, is_receipt: bool, session: Session) -> Dict[str, str]:
        """Store user feedback for future rule learning."""
        email = session.get(ProcessedEmail, email_id)
        if not email:
            raise ValueError("Email not found")

        # Store feedback
        email.reason = f"User Feedback: Should be receipt={is_receipt}. " + (
            email.reason or ""
        )
        session.add(email)

        # If it SHOULD have been a receipt, generate a suggested rule
        if is_receipt:
            from backend.services.learning_service import LearningService

            suggestion = LearningService.generate_rule_from_email(email)
            if suggestion:
                new_rule = ManualRule(
                    email_pattern=suggestion["email_pattern"],
                    subject_pattern=suggestion["subject_pattern"],
                    purpose=suggestion["purpose"],
                    confidence=suggestion["confidence"],
                    is_shadow_mode=True,  # Always start in shadow mode
                    match_count=0,
                )
                session.add(new_rule)

        session.commit()
        return {"status": "success", "message": "Feedback recorded and rule suggested"}

    @staticmethod
    def update_email_category(
        email_id: int,
        category: str,
        create_rule: bool,
        match_type: str,
        session: Session,
    ) -> Dict[str, Any]:
        """Update the category of an email and optionally create a rule."""
        email = session.get(ProcessedEmail, email_id)
        if not email:
            raise ValueError("Email not found")

        # Validate and trim category
        category = category.strip()
        if not category:
            raise ValueError("category cannot be empty or whitespace")

        # Validate match_type
        if match_type not in ["sender", "subject"]:
            raise ValueError("match_type must be either 'sender' or 'subject'")

        # Update the category
        old_category = email.category
        email.category = category
        session.add(email)
        session.commit()

        response: Dict[str, Any] = {
            "status": "success",
            "message": f"Category updated from '{old_category}' to '{category}'",
            "rule_created": False,
        }

        # Create a category rule if requested
        if create_rule:
            # Determine the pattern based on match type
            if match_type == "sender":
                # Extract domain from sender email
                sender = email.sender or ""
                if "@" in sender:
                    domain = sender.split("@", 1)[1]
                    pattern = f"*@{domain}"
                else:
                    pattern = f"*{sender}*"
            else:  # subject
                # Use a wildcard pattern with key words from subject
                subject = email.subject or ""
                # Take first significant word (simplified logic)
                words = [w for w in subject.lower().split() if len(w) > 3]
                if words:
                    pattern = f"*{words[0]}*"
                else:
                    # No sufficiently significant words found in subject
                    response[
                        "message"
                    ] += " (no suitable subject keywords found, rule not created)"
                    return response

            # Normalize pattern to lowercase for consistency
            pattern = pattern.lower()

            # Check if a similar rule already exists (case-insensitive)
            existing_rule = session.exec(
                select(CategoryRule)
                .where(func.lower(CategoryRule.pattern) == pattern)
                .where(CategoryRule.match_type == match_type)
            ).first()

            if not existing_rule:
                new_rule = CategoryRule(
                    match_type=match_type,
                    pattern=pattern,
                    assigned_category=category,
                    priority=10,
                )
                session.add(new_rule)
                session.commit()
                response["rule_created"] = True
                response[
                    "message"
                ] += f" and rule created: {match_type}='{pattern}' → '{category}'"
            else:
                response["message"] += " (rule already exists)"

        return response

    @staticmethod
    def reprocess_all_ignored(session: Session) -> Dict[str, Any]:
        """Reprocess all 'ignored' emails from the last 24 hours."""
        now = datetime.now(timezone.utc)
        day_ago = now - timedelta(hours=24)

        ignored_emails = session.exec(
            select(ProcessedEmail)
            .where(ProcessedEmail.status == "ignored")
            .where(ProcessedEmail.processed_at >= day_ago)  # type: ignore
            .where(ProcessedEmail.encrypted_body is not None)
        ).all()

        reprocessed_count = 0
        forwarded_count = 0
        target_email = os.environ.get("WIFE_EMAIL")

        for email in ignored_emails:
            body = decrypt_content(email.encrypted_body or "")
            html_body = decrypt_content(email.encrypted_html or "")

            email_data = {
                "subject": email.subject,
                "from": email.sender,
                "body": body,
                "html_body": html_body,
                "message_id": email.email_id,
                "date": email.received_at,
            }

            is_receipt = ReceiptDetector.is_receipt(email_data, session=session)
            if is_receipt and target_email:
                success = EmailForwarder.forward_email(email_data, target_email)
                if success:
                    email.status = "forwarded"
                    email.category = ReceiptDetector.categorize_receipt(email_data)
                    email.reason = "Reprocessed: Now detected as receipt"
                    session.add(email)
                    forwarded_count += 1

            reprocessed_count += 1

        session.commit()
        return {
            "status": "success",
            "reprocessed": reprocessed_count,
            "newly_forwarded": forwarded_count,
            "message": f"Successfully reprocessed {reprocessed_count} emails. {forwarded_count} were newly forwarded.",
        }

    @staticmethod
    def get_history_stats(
        session: Session,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Get statistics for email processing history."""
        # Build base query
        query = select(ProcessedEmail)
        filters: List[Any] = []

        # Apply filters
        query = ReportService.apply_email_filters(
            query,
            filters,
            date_from=date_from,
            date_to=date_to,
        )

        emails = session.exec(query).all()

        # Calculate stats
        total = len(emails)
        forwarded = sum(1 for e in emails if e.status == "forwarded")
        blocked = sum(1 for e in emails if e.status == "blocked" or e.status == "ignored")
        errors = sum(1 for e in emails if e.status == "error")

        # Calculate total amount
        total_amount = sum(e.amount for e in emails if e.amount)

        # Group by status
        status_breakdown: Dict[str, int] = {}
        for email in emails:
            status = email.status
            if status:
                status_breakdown[status] = status_breakdown.get(status, 0) + 1

        return {
            "total": total,
            "forwarded": forwarded,
            "blocked": blocked,
            "errors": errors,
            "total_amount": total_amount,
            "status_breakdown": status_breakdown,
        }

    @staticmethod
    def generate_csv_export(
        session: Session,
        status: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        sender: Optional[str] = None,
        min_amount: Optional[float] = None,
        max_amount: Optional[float] = None,
    ):
        """Generate CSV export of email history with streaming."""
        # Build query with filtering
        query = select(ProcessedEmail)
        filters: List[Any] = []

        query = ReportService.apply_email_filters(
            query,
            filters,
            status,
            date_from,
            date_to,
            sender,
            min_amount,
            max_amount,
        )

        # Order by processed_at descending
        query = query.order_by(ProcessedEmail.processed_at.desc())  # type: ignore

        # Stream CSV content to avoid loading all emails into memory
        def csv_generator():
            output = io.StringIO()
            writer = csv.writer(output)

            # Write headers
            writer.writerow(
                ["Date", "Vendor", "Amount", "Currency", "Category", "Link to Receipt"]
            )
            yield output.getvalue()
            output.seek(0)
            output.truncate(0)

            # Stream data rows directly from the query
            for email in session.exec(query):
                date_str = (
                    email.received_at.strftime("%Y-%m-%d %H:%M:%S")
                    if email.received_at
                    else ""
                )
                vendor = sanitize_csv_field(email.sender or "")
                amount = f"{email.amount:.2f}" if email.amount is not None else ""
                currency = DEFAULT_CURRENCY
                category = sanitize_csv_field(email.category or "")
                link = sanitize_csv_field(
                    f"Email ID: {email.email_id}" if email.email_id else ""
                )

                writer.writerow([date_str, vendor, amount, currency, category, link])
                yield output.getvalue()
                output.seek(0)
                output.truncate(0)

        return csv_generator()
