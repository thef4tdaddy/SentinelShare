from typing import List

from fastapi import APIRouter, Depends

from backend.auth_utils import get_current_user
from backend.database import get_session
from backend.models import ProcessedEmail, User
from sqlmodel import Session, select

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/activity", response_model=List[ProcessedEmail])
def get_activity(
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Get recent email activity for the current user."""
    statement = (
        select(ProcessedEmail)
        .where(ProcessedEmail.user_id == current_user.id)
        .order_by(ProcessedEmail.processed_at.desc())  # type: ignore
        .limit(limit)
    )
    return session.exec(statement).all()


@router.get("/stats")
def get_stats(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Get statistics for the current user."""
    # Simple aggregation for now
    total_emails = session.exec(
        select(ProcessedEmail).where(ProcessedEmail.user_id == current_user.id)
    ).all()
    forwarded = [e for e in total_emails if e.status == "forwarded"]
    blocked = [e for e in total_emails if e.status != "forwarded"]

    return {
        "total_forwarded": len(forwarded),
        "total_blocked": len(blocked),
        "total_processed": len(total_emails),
    }
