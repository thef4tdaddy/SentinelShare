from fastapi import APIRouter, Depends
from sqlmodel import Session, select
from backend.database import get_session
from backend.models import ProcessingRun
from typing import List

router = APIRouter(prefix="/api/history", tags=["history"])


@router.get("/processing-runs", response_model=List[ProcessingRun])
def get_processing_runs(
    limit: int = 50, 
    skip: int = 0,
    session: Session = Depends(get_session)
):
    """Get processing run history with pagination"""
    statement = (
        select(ProcessingRun)
        .order_by(ProcessingRun.started_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return session.exec(statement).all()


@router.get("/processing-runs/{run_id}", response_model=ProcessingRun)
def get_processing_run(run_id: int, session: Session = Depends(get_session)):
    """Get a specific processing run by ID"""
    return session.get(ProcessingRun, run_id)
