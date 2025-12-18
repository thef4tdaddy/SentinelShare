from typing import List

from backend.constants import DEFAULT_EMAIL_TEMPLATE
from backend.database import get_session
from backend.models import GlobalSettings, ManualRule, Preference
from backend.services.email_service import EmailService
from backend.services.scheduler import process_emails
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel
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


@router.post("/trigger-poll")
def trigger_poll(
    background_tasks: BackgroundTasks, session: Session = Depends(get_session)
):
    background_tasks.add_task(process_emails)
    return {"status": "triggered", "message": "Email poll started in background"}


# Email Template endpoints


class EmailTemplateUpdate(BaseModel):
    template: str


@router.get("/email-template")
def get_email_template(session: Session = Depends(get_session)):
    """Get the current email template"""
    setting = session.exec(
        select(GlobalSettings).where(GlobalSettings.key == "email_template")
    ).first()

    if setting:
        return {"template": setting.value}
    else:
        # Return default template if not set
        return {"template": DEFAULT_EMAIL_TEMPLATE}


@router.post("/email-template")
def update_email_template(
    data: EmailTemplateUpdate, session: Session = Depends(get_session)
):
    """Update the email template"""
    # Validate input
    if not data.template or not data.template.strip():
        raise HTTPException(status_code=400, detail="Template cannot be empty")
    if len(data.template) > 10000:
        raise HTTPException(
            status_code=400, detail="Template too long (max 10,000 characters)"
        )

    setting = session.exec(
        select(GlobalSettings).where(GlobalSettings.key == "email_template")
    ).first()

    if setting:
        setting.value = data.template
    else:
        setting = GlobalSettings(
            key="email_template",
            value=data.template,
            description="Email template for forwarding receipts",
        )
        session.add(setting)

    session.commit()
    session.refresh(setting)
    return {"template": setting.value, "message": "Template updated successfully"}


@router.post("/test-connections")
def test_connections():
    results = []

    accounts = EmailService.get_all_accounts()
    for acc in accounts:
        user = acc.get("email")
        pwd = acc.get("password")
        server = acc.get("imap_server")

        res = EmailService.test_connection(user, pwd, server)
        results.append(
            {
                "account": user,
                "success": res["success"],
                "error": res["error"],
            }
        )

    return results
