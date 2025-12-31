import csv
import io
import os
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlmodel import Session, and_, func, select

from backend.database import get_session
from backend.models import CategoryRule, ManualRule, ProcessedEmail, ProcessingRun
from backend.security import decrypt_content, sanitize_csv_field
from backend.services.detector import ReceiptDetector
from backend.services.email_service import EmailService
from backend.services.forwarder import EmailForwarder

router = APIRouter(prefix="/api/history", tags=["history"])

# Constants
RUN_GROUPING_WINDOW_SECONDS = (
    300  # 5 minutes - emails within this window are grouped into same run
)
DEFAULT_CURRENCY = "USD"


# Valid status values
class EmailStatus(str, Enum):
    FORWARDED = "forwarded"
    BLOCKED = "blocked"
    IGNORED = "ignored"
    ERROR = "error"


def parse_iso_date(date_str: str) -> datetime:
    """Parse ISO date string, handling Z timezone notation

    Args:
        date_str: ISO 8601 formatted date string (non-empty)

    Returns:
        datetime object

    Raises:
        HTTPException: If date format is invalid
    """
    try:
        return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid date format: {date_str}. Expected ISO 8601 format (e.g., 2025-12-10T10:00:00Z)",
        )


def apply_email_filters(
    query,
    filters: List[Any],
    status: Optional[EmailStatus] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    sender: Optional[str] = None,
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None,
):
    """Apply standard email filters to a query."""
    if status:
        filters.append(ProcessedEmail.status == status.value)
    if date_from and date_from.strip():
        date_from_obj = parse_iso_date(date_from)
        filters.append(ProcessedEmail.processed_at >= date_from_obj)  # type: ignore
    if date_to and date_to.strip():
        date_to_obj = parse_iso_date(date_to)
        filters.append(ProcessedEmail.processed_at <= date_to_obj)  # type: ignore
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


@router.get("/emails")
def get_email_history(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    status: Optional[EmailStatus] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    sender: Optional[str] = None,
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None,
    session: Session = Depends(get_session),
):
    """Get paginated email history with optional filtering.

    Args:
        page: Page number for pagination (1-based, must be >= 1).
        per_page: Number of records per page (must be between 1 and 100).
        status: Optional email status filter (e.g., forwarded, blocked, ignored, error).
        date_from: Optional start of date range filter (ISO 8601 string).
        date_to: Optional end of date range filter (ISO 8601 string).
        sender: Optional filter for sender email address.
        min_amount: Minimum amount (must be >= 0).
        max_amount: Maximum amount (must be >= 0).
        session: Database session dependency.

    Raises:
        HTTPException: If amounts are negative or min_amount > max_amount.
    """

    # Validate amount values
    if min_amount is not None and min_amount < 0:
        raise HTTPException(
            status_code=400,
            detail=f"min_amount must be non-negative, got {min_amount}",
        )
    if max_amount is not None and max_amount < 0:
        raise HTTPException(
            status_code=400,
            detail=f"max_amount must be non-negative, got {max_amount}",
        )
    if min_amount is not None and max_amount is not None and min_amount > max_amount:
        raise HTTPException(
            status_code=400,
            detail=f"min_amount ({min_amount}) cannot be greater than max_amount ({max_amount})",
        )

    # Build query
    query = select(ProcessedEmail)
    filters: List[Any] = []

    # Use helper to apply filters
    query = apply_email_filters(
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


@router.post("/reprocess/{email_id}")
def reprocess_email(email_id: int, session: Session = Depends(get_session)):
    """Re-analyze a specific email using current rules and logic."""
    email = session.get(ProcessedEmail, email_id)
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")

    # 1. Get content from encrypted storage
    body = decrypt_content(email.encrypted_body) if email.encrypted_body else ""
    html_body = decrypt_content(email.encrypted_html) if email.encrypted_html else ""

    # 2. Fallback to IMAP if content is gone (retention expired)
    if not body and not html_body:
        acc_email = email.account_email or ""
        creds = EmailService.get_credentials_for_account(acc_email)
        if not creds:
            raise HTTPException(
                status_code=400,
                detail="Cannot fallback to IMAP: Credentials missing for this account",
            )

        fetched = EmailService.fetch_email_by_id(
            email.account_email, creds["password"], email.email_id, creds["imap_server"]
        )
        if not fetched:
            raise HTTPException(status_code=404, detail="Email not found in IMAP inbox")

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


@router.post("/feedback")
def submit_feedback(
    email_id: int = Body(...),
    is_receipt: bool = Body(...),
    session: Session = Depends(get_session),
):
    """Store user feedback for future rule learning."""
    email = session.get(ProcessedEmail, email_id)
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")

    # Store feedback
    email.reason = f"User Feedback: Should be receipt={is_receipt}. " + (
        email.reason or ""
    )
    session.add(email)

    # 2. If it SHOULD have been a receipt, generate a suggested rule
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


class UpdateCategoryRequest(BaseModel):
    category: str = Field(..., min_length=1)
    create_rule: Optional[bool] = False
    match_type: Optional[str] = Field(default="sender", pattern="^(sender|subject)$")


@router.patch("/emails/{email_id}/category")
def update_email_category(
    email_id: int,
    request: UpdateCategoryRequest,
    session: Session = Depends(get_session),
):
    """
    Update the category of an email and optionally create a rule for future categorization.
    """
    email = session.get(ProcessedEmail, email_id)
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")

    # Validate and trim category
    category = request.category.strip()
    if not category:
        raise HTTPException(
            status_code=400, detail="category cannot be empty or whitespace"
        )

    # Validate match_type
    if request.match_type not in ["sender", "subject"]:
        raise HTTPException(
            status_code=400, detail="match_type must be either 'sender' or 'subject'"
        )

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
    if request.create_rule:
        # Determine the pattern based on match type
        if request.match_type == "sender":
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
                # No sufficiently significant words found in subject; avoid creating an over-broad rule
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
            .where(CategoryRule.match_type == request.match_type)
        ).first()

        if not existing_rule:
            new_rule = CategoryRule(
                match_type=request.match_type,
                pattern=pattern,
                assigned_category=category,
                priority=10,
            )
            session.add(new_rule)
            session.commit()
            response["rule_created"] = True
            response[
                "message"
            ] += f" and rule created: {request.match_type}='{pattern}' → '{category}'"
        else:
            response["message"] += " (rule already exists)"

    return response


@router.post("/reprocess-all-ignored")
def reprocess_all_ignored(session: Session = Depends(get_session)):
    """Reprocess all 'ignored' emails from the last 24 hours (if bodies are available)."""
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
            "date": email.received_at,  # format_email_date will handle datetime objects
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


@router.get("/stats")
def get_history_stats(
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    session: Session = Depends(get_session),
):
    """Get statistics for email processing history"""

    # Build base query
    query = select(ProcessedEmail)
    filters: List[Any] = []

    # Use helper to apply filters
    query = apply_email_filters(
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


@router.get("/runs")
def get_recent_runs(
    limit: int = Query(20, ge=1, le=100), session: Session = Depends(get_session)
):
    """Get aggregated information about recent processing runs"""
    # Query the actual ProcessingRun table
    query = select(ProcessingRun).order_by(ProcessingRun.started_at.desc()).limit(limit)  # type: ignore
    runs_db = session.exec(query).all()

    runs = []
    for r in runs_db:
        # Map ProcessingRun to the format expected by frontend
        # Front end expects:
        # run_time, first_processed, last_processed, total_emails, forwarded, blocked, errors, email_ids

        # approximate "blocked" as processed - forwarded (since we don't store blocked count explicitly in run yet)
        # Actually in scheduler.py: run.emails_processed = count of new emails
        # run.emails_forwarded = count of forwarded
        # blocked = processed - forwarded

        blocked = max(0, r.emails_processed - r.emails_forwarded)

        runs.append(
            {
                "run_time": r.started_at,
                "first_processed": r.started_at,  # Simplified
                "last_processed": r.completed_at or r.started_at,
                "total_emails": r.emails_checked,  # Use checked as total seen
                "forwarded": r.emails_forwarded,
                "blocked": blocked,
                "errors": 1 if r.status == "error" else 0,
                "email_ids": [],  # Frontend doesn't use this currently
            }
        )

    return {"runs": runs}


@router.get("/processing-runs", response_model=List[ProcessingRun])
def get_processing_runs(
    limit: int = 50, skip: int = 0, session: Session = Depends(get_session)
):
    """Get processing run history with pagination"""
    statement = (
        select(ProcessingRun)
        .order_by(ProcessingRun.started_at.desc())  # type: ignore
        .offset(skip)
        .limit(limit)
    )
    return session.exec(statement).all()


@router.get("/processing-runs/{run_id}", response_model=ProcessingRun)
def get_processing_run(run_id: int, session: Session = Depends(get_session)):
    """Get a specific processing run by ID"""
    run = session.get(ProcessingRun, run_id)
    if not run:
        raise HTTPException(
            status_code=404, detail=f"Processing run {run_id} not found"
        )
    return run


class ExportFormat(str, Enum):
    CSV = "csv"


@router.get("/export")
def export_history(
    format: ExportFormat = Query(ExportFormat.CSV),
    status: Optional[EmailStatus] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    sender: Optional[str] = None,
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None,
    session: Session = Depends(get_session),
):
    """Export email history as CSV file with optional filtering"""

    # Build query with filtering via shared helper
    query = select(ProcessedEmail)
    filters: List[Any] = []

    query = apply_email_filters(
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

    # Stream CSV content to avoid loading all emails and full CSV into memory
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
            # Link to receipt - using email_id as reference
            link = sanitize_csv_field(
                f"Email ID: {email.email_id}" if email.email_id else ""
            )

            writer.writerow([date_str, vendor, amount, currency, category, link])
            yield output.getvalue()
            output.seek(0)
            output.truncate(0)

    # Generate filename with current date (UTC for consistency)
    current_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    filename = f"expenses_{current_date}.csv"

    # Return as streaming response
    return StreamingResponse(
        csv_generator(),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
