from typing import List

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field
from sqlmodel import Session, select

from backend.database import get_session
from backend.models import CategoryRule, ManualRule, Preference
from backend.services.email_service import EmailService
from backend.services.scheduler import process_emails
from backend.services.settings_service import SettingsService

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


# Category Rules endpoints


@router.get("/category-rules", response_model=List[CategoryRule])
def get_category_rules(session: Session = Depends(get_session)):
    """Get all category rules ordered by priority"""
    return session.exec(
        select(CategoryRule).order_by(CategoryRule.priority.desc())  # type: ignore
    ).all()


@router.post("/category-rules", response_model=CategoryRule)
def create_category_rule(rule: CategoryRule, session: Session = Depends(get_session)):
    """Create a new category rule"""
    try:
        return SettingsService.create_category_rule(
            match_type=rule.match_type,
            pattern=rule.pattern,
            assigned_category=rule.assigned_category,
            priority=rule.priority,
            session=session,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/category-rules/{rule_id}", response_model=CategoryRule)
def update_category_rule(
    rule_id: int, updated_rule: CategoryRule, session: Session = Depends(get_session)
):
    """Update an existing category rule"""
    try:
        return SettingsService.update_category_rule(
            rule_id=rule_id,
            match_type=updated_rule.match_type,
            pattern=updated_rule.pattern,
            assigned_category=updated_rule.assigned_category,
            priority=updated_rule.priority,
            session=session,
        )
    except ValueError as e:
        status_code = 404 if "not found" in str(e).lower() else 400
        raise HTTPException(status_code=status_code, detail=str(e))


@router.delete("/category-rules/{rule_id}")
def delete_category_rule(rule_id: int, session: Session = Depends(get_session)):
    """Delete a category rule"""
    rule = session.get(CategoryRule, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Category rule not found")
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
    return {"template": SettingsService.get_email_template(session)}


@router.post("/email-template")
def update_email_template(
    data: EmailTemplateUpdate, session: Session = Depends(get_session)
):
    """Update the email template"""
    try:
        return SettingsService.update_email_template(data.template, session)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


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
    """Get all email accounts (both DB and Env-defined)"""
    from backend.models import EmailAccount
    from backend.services.email_service import EmailService

    # 1. Get DB Accounts
    db_accounts = session.exec(select(EmailAccount)).all()
    response_list = [
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
        for acc in db_accounts
    ]

    # 2. Get Env Accounts (via EmailService)
    # EmailService.get_all_accounts returns simple dicts with credentials
    # We need to filter out ones that match DB accounts to avoid duplicates
    all_service_accounts = EmailService.get_all_accounts()

    db_emails = {acc.email.lower() for acc in db_accounts}

    # Start fake IDs at -1 and go down
    fake_id = -1

    now_str = "2024-01-01T00:00:00"  # Placeholder timestamp for env accounts

    for acc in all_service_accounts:
        email = acc.get("email", "").lower()
        if email and email not in db_emails:
            # This is an env-only account
            response_list.append(
                EmailAccountResponse(
                    id=fake_id,
                    email=email,
                    host=acc.get("imap_server", "unknown"),
                    port=993,  # Default assumption for env accounts if not specified
                    username=email,  # Usually same as email
                    is_active=True,
                    created_at=now_str,
                    updated_at=now_str,
                )
            )
            fake_id -= 1

    return response_list


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
    except Exception:
        logging.exception("Password encryption failed")
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
                raise HTTPException(
                    status_code=500, detail="Failed to decrypt password"
                )

            result = EmailService.test_connection(
                account.username, password, account.host
            )

        return {
            "account": account.email,
            "success": result["success"],
            # Do not expose low-level exception messages to the client
            "error": None if result["success"] else "Failed to connect to email server",
        }
    except ValueError as e:
        logging.error(f"Account test failed for {account_id}: {e}")
        raise HTTPException(status_code=500, detail="Email account test failed")
    except Exception:
        logging.exception(f"Unexpected error testing account {account_id}")
        raise HTTPException(status_code=500, detail="Email account test failed")
