import hmac
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request, UploadFile
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from sqlmodel import Session, select

from backend.database import engine, get_session
from backend.models import Preference
from backend.security import generate_hmac_signature, verify_dashboard_token
from backend.services.action_html_service import ActionHtmlService
from backend.services.command_service import CommandService
from backend.services.preference_service import PreferenceService
from backend.services.workflow_service import WorkflowService

router = APIRouter(prefix="/api/actions", tags=["actions"])


def verify_signature(cmd: str, arg: str, ts: str, sig: str) -> bool:
    # Simple HMAC verification
    msg = f"{cmd}:{arg}:{ts}"
    expected = generate_hmac_signature(msg)
    return hmac.compare_digest(expected, sig)


@router.get("/quick", response_class=HTMLResponse)
def quick_action(cmd: str, arg: str, ts: str, sig: str):
    """
    Handle one-click actions from emails (STOP, MORE, etc.)
    """
    if not verify_signature(cmd, arg, ts, sig):
        raise HTTPException(status_code=403, detail="Invalid signature")

    # Check timestamp expiration (e.g. 7 days link validity)
    try:
        link_ts = float(ts)
        now_ts = datetime.now(timezone.utc).timestamp()
        if now_ts - link_ts > 7 * 24 * 3600:  # 7 days
            return ActionHtmlService.render_error(
                "Link Expired", "This action link is too old."
            )
    except Exception:
        return ActionHtmlService.render_error(
            "Invalid Timestamp",
            "The timestamp format is invalid or could not be parsed.",
        )

    # Execute Command
    success = False
    message = ""

    # Map CMD to Preference Type
    if cmd.upper() == "STOP":
        CommandService._add_preference(arg, "Blocked Sender")
        success = True
        message = f"🚫 Successfully Blocked: {arg}"

    elif cmd.upper() == "MORE":
        CommandService._add_preference(arg, "Always Forward")
        success = True
        message = f"✅ Always Forwarding: {arg}"

    elif cmd.upper() == "BLOCK_CATEGORY":
        CommandService._add_preference(arg, "Blocked Category")
        success = True
        message = f"🚫 Blocked Category: {arg}"

    elif cmd.upper() == "SETTINGS":
        with Session(engine) as session:
            prefs = list(session.exec(select(Preference)).all())
        return ActionHtmlService.render_settings_view(prefs)

    if success:
        emoji = message.split()[0]
        return ActionHtmlService.render_success(message, emoji)

    return ActionHtmlService.render_unknown_command()


@router.get("/verify-dashboard")
def verify_dashboard(token: str):
    """Verify a token and return access details."""
    email = verify_dashboard_token(token)
    if not email:
        raise HTTPException(status_code=403, detail="Invalid or expired token")

    return {"success": True, "email": email}


class UpdatePreferencesRequest(BaseModel):
    token: str | None = None
    blocked_senders: list[str]
    allowed_senders: list[str]


@router.get("/preferences-for-sendee")
def get_preferences_for_sendee(
    request: Request,
    token: str | None = Query(None),
    session: Session = Depends(get_session),
):
    """
    Get current preferences for a sendee (via token) or admin (via session).
    """
    email = None

    if token:
        # 1. Token Access
        email = verify_dashboard_token(token)
        if not email:
            raise HTTPException(status_code=403, detail="Invalid or expired token")
    else:
        # 2. Admin Access (Session)
        if not request.session.get("authenticated"):
            raise HTTPException(status_code=401, detail="Unauthorized")
        email = "Admin"  # Placeholder for admin view

    prefs_dict = PreferenceService.get_preferences_dict(session)

    return {
        "success": True,
        "email": email,
        "blocked": prefs_dict["blocked"],
        "allowed": prefs_dict["allowed"],
    }


@router.post("/update-preferences")
def update_preferences(
    data: UpdatePreferencesRequest,
    request: Request,
    session: Session = Depends(get_session),
):
    """
    Update preferences via bulk replace. Supports Token or Admin Session.
    """
    # Verify Auth
    if data.token:
        email = verify_dashboard_token(data.token)
        if not email:
            raise HTTPException(status_code=403, detail="Invalid or expired token")
    else:
        if not request.session.get("authenticated"):
            raise HTTPException(status_code=401, detail="Unauthorized")

    # Use service to update preferences
    try:
        return WorkflowService.update_preferences(
            blocked_senders=data.blocked_senders,
            allowed_senders=data.allowed_senders,
            session=session,
        )
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))


class ToggleEmailRequest(BaseModel):
    """Request model for toggling email status"""

    email_id: int


# Alias for backward compatibility
ToggleIgnoredRequest = ToggleEmailRequest


@router.post("/toggle-to-ignored")
def toggle_to_ignored_email(
    request: ToggleEmailRequest, session: Session = Depends(get_session)
):
    """
    Toggle a forwarded or blocked email back to ignored status
    """
    try:
        return WorkflowService.toggle_to_ignored(request.email_id, session)
    except ValueError as e:
        status_code = 404 if "not found" in str(e).lower() else 400
        raise HTTPException(status_code=status_code, detail=str(e))


@router.post("/toggle-ignored")
def toggle_ignored_email(
    request: ToggleIgnoredRequest, session: Session = Depends(get_session)
):
    """
    Toggle an ignored email: create a manual rule and forward the email
    """
    try:
        return WorkflowService.toggle_ignored_to_forwarded(request.email_id, session)
    except ValueError as e:
        status_code = 404 if "not found" in str(e).lower() else 400
        if "not configured" in str(e).lower():
            status_code = 500
        raise HTTPException(status_code=status_code, detail=str(e))


@router.post("/upload")
async def upload_receipt(
    file: UploadFile,
    request: Request,
    session: Session = Depends(get_session),
):
    """
    Upload a receipt file (PDF, PNG, JPG) and process it as a manual upload.
    """
    # Validate file type
    allowed_types = ["application/pdf", "image/png", "image/jpeg"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type: {file.content_type}. Allowed: PDF, PNG, JPG",
        )

    # Validate file size (10MB limit)
    MAX_SIZE = 10 * 1024 * 1024  # 10MB
    content = await file.read()
    if len(content) > MAX_SIZE:
        raise HTTPException(status_code=400, detail="File size exceeds 10MB limit")

    # Use service to handle upload
    try:
        return WorkflowService.upload_receipt(
            file_content=content,
            filename=file.filename or "upload",
            content_type=file.content_type or "application/pdf",
            session=session,
        )
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
