from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select, func, and_
from backend.database import get_session
from backend.models import ProcessedEmail
from typing import Optional
from datetime import datetime

router = APIRouter(prefix="/api/history", tags=["history"])

# Constants
RUN_GROUPING_WINDOW_SECONDS = 300  # 5 minutes - emails within this window are grouped into same run


def parse_iso_date(date_str: str) -> datetime:
    """Parse ISO date string, handling Z timezone notation"""
    return datetime.fromisoformat(date_str.replace('Z', '+00:00'))

@router.get("/emails")
def get_email_history(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    status: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    session: Session = Depends(get_session)
):
    """Get paginated email history with optional filtering"""
    
    # Build query
    query = select(ProcessedEmail)
    
    # Apply filters
    filters = []
    if status:
        filters.append(ProcessedEmail.status == status)
    if date_from:
        try:
            date_from_obj = parse_iso_date(date_from)
            filters.append(ProcessedEmail.processed_at >= date_from_obj)
        except ValueError:
            pass
    if date_to:
        try:
            date_to_obj = parse_iso_date(date_to)
            filters.append(ProcessedEmail.processed_at <= date_to_obj)
        except ValueError:
            pass
    
    if filters:
        query = query.where(and_(*filters))
    
    # Order by processed_at descending
    query = query.order_by(ProcessedEmail.processed_at.desc())
    
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
            "total_pages": (total + per_page - 1) // per_page
        }
    }

@router.get("/stats")
def get_history_stats(
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    session: Session = Depends(get_session)
):
    """Get statistics for email processing history"""
    
    # Build base query
    query = select(ProcessedEmail)
    
    # Apply date filters
    filters = []
    if date_from:
        try:
            date_from_obj = parse_iso_date(date_from)
            filters.append(ProcessedEmail.processed_at >= date_from_obj)
        except ValueError:
            pass
    if date_to:
        try:
            date_to_obj = parse_iso_date(date_to)
            filters.append(ProcessedEmail.processed_at <= date_to_obj)
        except ValueError:
            pass
    
    if filters:
        query = query.where(and_(*filters))
    
    emails = session.exec(query).all()
    
    # Calculate stats
    total = len(emails)
    forwarded = sum(1 for e in emails if e.status == "forwarded")
    blocked = sum(1 for e in emails if e.status == "blocked" or e.status == "ignored")
    errors = sum(1 for e in emails if e.status == "error")
    
    # Calculate total amount
    total_amount = sum(e.amount for e in emails if e.amount)
    
    # Group by status
    status_breakdown = {}
    for email in emails:
        status = email.status
        status_breakdown[status] = status_breakdown.get(status, 0) + 1
    
    return {
        "total": total,
        "forwarded": forwarded,
        "blocked": blocked,
        "errors": errors,
        "total_amount": total_amount,
        "status_breakdown": status_breakdown
    }

@router.get("/runs")
def get_recent_runs(
    limit: int = Query(20, ge=1, le=100),
    session: Session = Depends(get_session)
):
    """Get aggregated information about recent processing runs"""
    
    # Get all emails and group by processing time windows (e.g., 5-minute intervals)
    # This is a simple approach - in production you might want a separate runs table
    
    query = select(ProcessedEmail).order_by(ProcessedEmail.processed_at.desc())
    all_emails = session.exec(query).all()
    
    if not all_emails:
        return {"runs": []}
    
    # Group emails into runs based on time proximity (5 minutes)
    runs = []
    current_run = None
    
    for email in all_emails:
        if current_run is None or (current_run["last_processed"] - email.processed_at).total_seconds() > RUN_GROUPING_WINDOW_SECONDS:
            # Start a new run
            if current_run:
                runs.append(current_run)
            
            current_run = {
                "run_time": email.processed_at,
                "first_processed": email.processed_at,
                "last_processed": email.processed_at,
                "total_emails": 1,
                "forwarded": 1 if email.status == "forwarded" else 0,
                "blocked": 1 if email.status in ["blocked", "ignored"] else 0,
                "errors": 1 if email.status == "error" else 0,
                "email_ids": [email.id]
            }
        else:
            # Add to current run
            current_run["total_emails"] += 1
            current_run["first_processed"] = email.processed_at
            if email.status == "forwarded":
                current_run["forwarded"] += 1
            elif email.status in ["blocked", "ignored"]:
                current_run["blocked"] += 1
            elif email.status == "error":
                current_run["errors"] += 1
            current_run["email_ids"].append(email.id)
    
    # Add the last run
    if current_run:
        runs.append(current_run)
    
    # Return limited number of runs
    return {"runs": runs[:limit]}
