from typing import List

from backend.database import get_session
from backend.models import ProcessedEmail
from fastapi import APIRouter, Depends
from sqlmodel import Session, select

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/activity", response_model=List[ProcessedEmail])
def get_activity(limit: int = 50, session: Session = Depends(get_session)):
    statement = (
        select(ProcessedEmail).order_by(ProcessedEmail.processed_at.desc()).limit(limit)  # type: ignore
    )
    return session.exec(statement).all()


@router.get("/stats")
def get_stats(session: Session = Depends(get_session)):
    # Simple aggregation for now
    total_emails = session.exec(
        select(ProcessedEmail)
    ).all()  # Potentially slow if many
    forwarded = [e for e in total_emails if e.status == "forwarded"]
    blocked = [e for e in total_emails if e.status != "forwarded"]

    return {
        "total_forwarded": len(forwarded),
        "total_blocked": len(blocked),
        "total_processed": len(total_emails),
    }
