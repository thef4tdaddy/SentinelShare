from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlmodel import Session, select

from backend.database import get_session
from backend.models import ProcessingRun
from backend.services.report_service import ReportService

router = APIRouter(prefix="/api/history", tags=["history"])


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

    # Parse date strings
    date_from_obj = (
        parse_iso_date(date_from) if date_from and date_from.strip() else None
    )
    date_to_obj = parse_iso_date(date_to) if date_to and date_to.strip() else None

    # Use service to get paginated emails
    return ReportService.get_paginated_emails(
        session=session,
        page=page,
        per_page=per_page,
        status=status.value if status else None,
        date_from=date_from_obj,
        date_to=date_to_obj,
        sender=sender,
        min_amount=min_amount,
        max_amount=max_amount,
    )


@router.post("/reprocess/{email_id}")
def reprocess_email(email_id: int, session: Session = Depends(get_session)):
    """Re-analyze a specific email using current rules and logic."""
    try:
        return ReportService.reprocess_email(email_id, session)
    except ValueError as e:
        raise HTTPException(
            status_code=404 if "not found" in str(e).lower() else 400, detail=str(e)
        )


@router.post("/feedback")
def submit_feedback(
    email_id: int = Body(...),
    is_receipt: bool = Body(...),
    session: Session = Depends(get_session),
):
    """Store user feedback for future rule learning."""
    try:
        return ReportService.submit_feedback(email_id, is_receipt, session)
    except ValueError as e:
        status_code = 404 if "not found" in str(e).lower() else 400
        raise HTTPException(status_code=status_code, detail=str(e))


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
    try:
        return ReportService.update_email_category(
            email_id=email_id,
            category=request.category,
            create_rule=request.create_rule or False,
            match_type=request.match_type or "sender",
            session=session,
        )
    except ValueError as e:
        status_code = 404 if "not found" in str(e).lower() else 400
        raise HTTPException(status_code=status_code, detail=str(e))


@router.post("/reprocess-all-ignored")
def reprocess_all_ignored(session: Session = Depends(get_session)):
    """Reprocess all 'ignored' emails from the last 24 hours (if bodies are available)."""
    return ReportService.reprocess_all_ignored(session)


@router.get("/stats")
def get_history_stats(
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    session: Session = Depends(get_session),
):
    """Get statistics for email processing history"""
    # Parse date strings
    date_from_obj = (
        parse_iso_date(date_from) if date_from and date_from.strip() else None
    )
    date_to_obj = parse_iso_date(date_to) if date_to and date_to.strip() else None

    return ReportService.get_history_stats(
        session=session,
        date_from=date_from_obj,
        date_to=date_to_obj,
    )


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
    # Parse date strings
    date_from_obj = (
        parse_iso_date(date_from) if date_from and date_from.strip() else None
    )
    date_to_obj = parse_iso_date(date_to) if date_to and date_to.strip() else None

    # Get CSV generator from service
    csv_generator = ReportService.generate_csv_export(
        session=session,
        status=status.value if status else None,
        date_from=date_from_obj,
        date_to=date_to_obj,
        sender=sender,
        min_amount=min_amount,
        max_amount=max_amount,
    )

    # Generate filename with current date (UTC for consistency)
    current_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    filename = f"expenses_{current_date}.csv"

    # Return as streaming response
    return StreamingResponse(
        csv_generator,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
