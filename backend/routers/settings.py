from typing import List

from backend.database import get_session
from backend.models import ManualRule, Preference
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("/preferences", response_model=List[Preference])
def get_preferences(session: Session = Depends(get_session)):
    return session.exec(select(Preference)).all()


@router.post("/preferences", response_model=Preference)
def create_preference(pref: Preference, session: Session = Depends(get_session)):
    session.add(pref)
    session.commit()
    session.refresh(pref)
    return pref


@router.delete("/preferences/{pref_id}")
def delete_preference(pref_id: int, session: Session = Depends(get_session)):
    pref = session.get(Preference, pref_id)
    if not pref:
        raise HTTPException(status_code=404, detail="Preference not found")
    session.delete(pref)
    session.commit()
    return {"ok": True}


@router.get("/rules", response_model=List[ManualRule])
def get_rules(session: Session = Depends(get_session)):
    return session.exec(select(ManualRule)).all()


@router.post("/rules", response_model=ManualRule)
def create_rule(rule: ManualRule, session: Session = Depends(get_session)):
    session.add(rule)
    session.commit()
    session.refresh(rule)
    return rule


@router.delete("/rules/{rule_id}")
def delete_rule(rule_id: int, session: Session = Depends(get_session)):
    rule = session.get(ManualRule, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    session.delete(rule)
    session.commit()
    return {"ok": True}


from backend.services.scheduler import process_emails
from fastapi import BackgroundTasks


@router.post("/trigger-poll")
def trigger_poll(
    background_tasks: BackgroundTasks, session: Session = Depends(get_session)
):
    background_tasks.add_task(process_emails)
    return {"status": "triggered", "message": "Email poll started in background"}


import json
import os

from backend.services.email_service import EmailService


@router.post("/test-connections")
def test_connections():
    results = []

    # 1. Try Multi-Account Config
    email_accounts_json = os.environ.get("EMAIL_ACCOUNTS")

    if email_accounts_json:
        try:
            accounts = json.loads(email_accounts_json)
        except json.JSONDecodeError:
            # Try single quote fix
            try:
                fixed_json = email_accounts_json.replace("'", '"')
                accounts = json.loads(fixed_json)
            except:
                accounts = []

        if isinstance(accounts, list):
            for acc in accounts:
                user = acc.get("email")
                pwd = acc.get("password")
                server = acc.get("imap_server", "imap.gmail.com")

                if user:
                    res = EmailService.test_connection(user, pwd, server)
                    results.append(
                        {
                            "account": user,
                            "success": res["success"],
                            "error": res["error"],
                        }
                    )

    # 2. Fallback to Legacy Single Account (if no accounts found/processed yet)
    if not results:
        user = os.environ.get("GMAIL_EMAIL")
        pwd = os.environ.get("GMAIL_PASSWORD")
        server = os.environ.get("IMAP_SERVER", "imap.gmail.com")

        if user:
            res = EmailService.test_connection(user, pwd, server)
            results.append(
                {"account": user, "success": res["success"], "error": res["error"]}
            )

    return results
