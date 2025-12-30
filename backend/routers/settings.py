from typing import List

from backend.constants import DEFAULT_EMAIL_TEMPLATE
from backend.database import get_session
from backend.models import GlobalSettings, ManualRule, Preference
from backend.services.email_service import EmailService
from backend.services.scheduler import process_emails
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field
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


# Email Account Management Endpoints


class EmailAccountCreate(BaseModel):
    email: EmailStr
    host: str = "imap.gmail.com"
    port: int = Field(default=993, ge=1, le=65535)
    username: str
    password: str  # WARNING: This password is sent in plain text in the request body; ensure this endpoint is only served over HTTPS/TLS. It will be encrypted before storage.


class EmailAccountResponse(BaseModel):
    id: int
    email: str
    host: str
    port: int
    username: str
    is_active: bool
    created_at: str
    updated_at: str
    auth_method: str = "password"  # "password" or "oauth2"
    provider: str | None = None  # "google", "microsoft", etc.


@router.get("/accounts", response_model=List[EmailAccountResponse])
def get_email_accounts(session: Session = Depends(get_session)):
    """Get all email accounts (without passwords)"""
    from backend.models import EmailAccount

    accounts = session.exec(select(EmailAccount)).all()
    return [
        EmailAccountResponse(
            id=acc.id,
            email=acc.email,
            host=acc.host,
            port=acc.port,
            username=acc.username,
            is_active=acc.is_active,
            created_at=acc.created_at.isoformat(),
            updated_at=acc.updated_at.isoformat(),
            auth_method=acc.auth_method,
            provider=acc.provider,
        )
        for acc in accounts
    ]


@router.post("/accounts", response_model=EmailAccountResponse)
def create_email_account(
    account: EmailAccountCreate, session: Session = Depends(get_session)
):
    """Create a new email account"""
    import logging
    from datetime import datetime, timezone

    from backend.models import EmailAccount
    from backend.services.encryption_service import EncryptionService

    # Normalize email to lowercase for case-insensitive comparison
    normalized_email = str(account.email).lower()

    # Check if account already exists (case-insensitive)
    existing = session.exec(
        select(EmailAccount).where(EmailAccount.email == normalized_email)
    ).first()
    if existing:
        raise HTTPException(
            status_code=400, detail="Account with this email already exists"
        )

    # Encrypt the password
    try:
        encrypted_password = EncryptionService.encrypt(account.password)
    except Exception as e:
        logging.error(f"Password encryption failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to encrypt password")

    # Create the account
    now = datetime.now(timezone.utc)
    new_account = EmailAccount(
        email=normalized_email,
        host=account.host,
        port=account.port,
        username=account.username,
        encrypted_password=encrypted_password,
        is_active=True,
        created_at=now,
        updated_at=now,
    )

    session.add(new_account)
    session.commit()
    session.refresh(new_account)

    return EmailAccountResponse(
        id=new_account.id,
        email=new_account.email,
        host=new_account.host,
        port=new_account.port,
        username=new_account.username,
        is_active=new_account.is_active,
        created_at=new_account.created_at.isoformat(),
        updated_at=new_account.updated_at.isoformat(),
        auth_method=new_account.auth_method,
        provider=new_account.provider,
    )


@router.delete("/accounts/{account_id}")
def delete_email_account(account_id: int, session: Session = Depends(get_session)):
    """Delete an email account"""
    from backend.models import EmailAccount

    account = session.get(EmailAccount, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    session.delete(account)
    session.commit()
    return {"ok": True}


@router.post("/accounts/{account_id}/test")
async def test_email_account(account_id: int, session: Session = Depends(get_session)):
    """Test connection for a specific email account"""
    import logging

    from backend.models import EmailAccount
    from backend.services.encryption_service import EncryptionService
    from backend.services.oauth2_service import OAuth2Service

    account = session.get(EmailAccount, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    try:
        if account.auth_method == "oauth2":
            # OAuth2 account - get valid access token
            access_token = await OAuth2Service.ensure_valid_token(session, account)
            if not access_token:
                raise HTTPException(
                    status_code=500, detail="Failed to obtain OAuth2 access token"
                )

            result = EmailService.test_connection(
                account.username,
                None,
                account.host,
                auth_method="oauth2",
                access_token=access_token,
            )
        else:
            # Password-based account
            if not account.encrypted_password:
                raise HTTPException(
                    status_code=500, detail="No password found for account"
                )

            password = EncryptionService.decrypt(account.encrypted_password)
            if not password:
                raise HTTPException(status_code=500, detail="Failed to decrypt password")

            result = EmailService.test_connection(
                account.username, password, account.host
            )

        return {
            "account": account.email,
            "success": result["success"],
            "error": result["error"],
        }
    except ValueError as e:
        logging.error(f"Account test failed for {account_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logging.exception(f"Unexpected error testing account {account_id}")
        raise HTTPException(status_code=500, detail=f"Test failed: {str(e)}")
