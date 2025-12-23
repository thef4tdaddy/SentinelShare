from typing import List

from backend.database import engine, get_session
from backend.models import LearningCandidate, ManualRule
from backend.services.learning_service import LearningService
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlmodel import Session, desc, select

router = APIRouter(prefix="/api/learning", tags=["learning"])


def run_scan_wrapper(days: int):
    """
    Background task wrapper that manages its own DB session.
    """
    with Session(engine) as session:
        try:
            count = LearningService.scan_history(session, days)
            logging.info(f"✅ Background Scan Complete. Found {count} new candidates.")
        except Exception as e:
            logging.error(f"❌ Background Scan Failed: {e}", exc_info=True)


@router.post("/scan")
async def scan_history(
    background_tasks: BackgroundTasks,
    days: int = 30,
    session: Session = Depends(get_session),
):
    """
    Triggers a background scan of email history (last N days).
    """
    background_tasks.add_task(run_scan_wrapper, days)
    return {"message": "Scan started in background", "days": days}


@router.get("/candidates", response_model=List[LearningCandidate])
def get_candidates(session: Session = Depends(get_session)):
    """
    Returns all discovered rule candidates.
    """
    return session.exec(
        select(LearningCandidate).order_by(desc(LearningCandidate.created_at))
    ).all()


@router.post("/approve/{candidate_id}")
def approve_candidate(candidate_id: int, session: Session = Depends(get_session)):
    """
    Converts a candidate into a permanent ManualRule.
    """
    candidate = session.get(LearningCandidate, candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    # Create the rule
    # If we have a subject pattern, we use it with the sender content
    # Strategy: "Sender AND Subject" is safer than just "Sender"

    new_rule = ManualRule(
        purpose=f"Learned from {candidate.sender}",
        confidence=1.0,
        priority=50,
        is_shadow_mode=False,
        email_pattern=f"*{candidate.sender}*",
    )

    if candidate.subject_pattern:
        new_rule.subject_pattern = candidate.subject_pattern

    session.add(new_rule)

    # Remove the candidate after approval
    session.delete(candidate)

    session.commit()
    session.refresh(new_rule)
    return {"message": "Rule approved", "rule": new_rule}


@router.delete("/ignore/{candidate_id}")
def ignore_candidate(candidate_id: int, session: Session = Depends(get_session)):
    candidate = session.get(LearningCandidate, candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    session.delete(candidate)
    session.commit()
    return {"message": "Candidate ignored"}
