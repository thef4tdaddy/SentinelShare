import hmac
import html
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request, UploadFile
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from sqlmodel import Session, col, select

from backend.database import engine, get_session
from backend.models import Preference
from backend.security import generate_hmac_signature, verify_dashboard_token
from backend.services.command_service import CommandService
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

    # Escape user input for safe HTML rendering
    safe_arg = html.escape(arg)

    # Check timestamp expiration (e.g. 7 days link validity)
    try:
        link_ts = float(ts)
        now_ts = datetime.now(timezone.utc).timestamp()
        if now_ts - link_ts > 7 * 24 * 3600:  # 7 days
            return "<h1>❌ Link Expired</h1><p>This action link is too old.</p>"
    except Exception:
        return "<h1>❌ Invalid Timestamp</h1>"

    # Execute Command
    # We fake an 'email_data' dict for CommandService or use separate logic.
    # CommandService.process_command expects a dict.
    # Let's adapt CommandService to handle direct calls if possible.

    success = False
    message = ""

    # Map CMD to Preference Type
    if cmd.upper() == "STOP":
        CommandService._add_preference(
            arg, "Blocked Sender"
        )  # Could be category too based on arg logic
        # If arg implies category (e.g. 'restaurants'), we should handle that.
        # But for 'STOP amazon', it handles as blocked sender.
        # Ideally we differentiate STOP_SENDER vs STOP_CATEGORY in the link generation.
        success = True
        message = f"🚫 Successfully Blocked: {safe_arg}"

    elif cmd.upper() == "MORE":
        CommandService._add_preference(arg, "Always Forward")
        success = True
        message = f"✅ Always Forwarding: {safe_arg}"

    elif cmd.upper() == "BLOCK_CATEGORY":
        CommandService._add_preference(arg, "Blocked Category")
        success = True
        message = f"🚫 Blocked Category: {safe_arg}"

    elif cmd.upper() == "SETTINGS":
        with Session(engine) as session:
            prefs = session.exec(select(Preference)).all()

        blocked = [p for p in prefs if "Blocked" in p.type]
        allowed = [p for p in prefs if "Forward" in p.type]  # "Always Forward"

        html_list = ""

        if allowed:
            html_list += """
            <div style="margin-bottom: 24px;">
                <h3 style="color: #15803d; font-size: 14px; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 12px; display: flex; align-items: center; gap: 6px;">
                    ✅ Always Forwarding
                </h3>
                <div style="display: flex; flex-wrap: wrap; gap: 8px;">
            """
            for p in allowed:
                html_list += f"""
                <span style="background: #dcfce7; color: #166534; padding: 6px 12px; border-radius: 9999px; font-size: 13px; font-weight: 500; border: 1px solid #bbf7d0;">
                    {p.item}
                </span>
                """
            html_list += "</div></div>"

        if blocked:
            html_list += """
            <div style="margin-bottom: 24px;">
                <h3 style="color: #b91c1c; font-size: 14px; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 12px; display: flex; align-items: center; gap: 6px;">
                    🚫 Blocked
                </h3>
                <div style="display: flex; flex-wrap: wrap; gap: 8px;">
            """
            for p in blocked:
                html_list += f"""
                <span style="background: #fee2e2; color: #991b1b; padding: 6px 12px; border-radius: 9999px; font-size: 13px; font-weight: 500; border: 1px solid #fecaca;">
                    {p.item}
                </span>
                """
            html_list += "</div></div>"

        if not blocked and not allowed:
            html_list = """
            <div style="text-align: center; padding: 40px 20px; color: #71717a;">
                <p>No active preferences found yet.</p>
                <p style="font-size: 13px;">Use the action buttons in forwarded emails to build your list.</p>
            </div>
            """

        return f"""
         <!DOCTYPE html>
         <html>
            <head>
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <style>
                    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background-color: #f4f4f5; margin: 0; padding: 20px; color: #18181b; }}
                    .container {{ max-width: 500px; margin: 0 auto; background: white; border-radius: 12px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06); overflow: hidden; }}
                    .header {{ background: #fafafa; padding: 20px; border-bottom: 1px solid #e4e4e7; text-align: center; }}
                    .logo {{ font-size: 24px; margin-bottom: 8px; display: block; }}
                    .title {{ font-weight: 600; font-size: 18px; margin: 0; color: #18181b; }}
                    .content {{ padding: 24px; }}
                    .footer {{ padding: 16px; text-align: center; background: #fafafa; border-top: 1px solid #e4e4e7; }}
                    .btn {{ display: inline-block; background: #2563eb; color: white; text-decoration: none; padding: 10px 20px; border-radius: 6px; font-weight: 500; font-size: 14px; transition: background 0.2s; }}
                    .btn:hover {{ background: #1d4ed8; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <span class="logo">⚙️</span>
                        <h1 class="title">Current Settings</h1>
                    </div>
                    <div class="content">
                        {html_list}
                    </div>
                    <div class="footer">
                        <a href="/history" class="btn">Go to Dashboard</a>
                    </div>
                </div>
            </body>
         </html>
         """

    if success:
        return f"""
         <html>
            <body style="font-family: sans-serif; text-align: center; padding: 50px;">
                <div style="font-size: 50px;">{message.split()[0]}</div>
                <h1>Action Confirmed</h1>
                <p style="font-size: 18px; color: #555;">{message}</p>
                <p><a href="/history">Go to Dashboard</a></p>
            </body>
         </html>
         """

    return """
     <html>
        <body style="font-family: sans-serif; text-align: center; padding: 50px;">
            <div style="font-size: 50px;">❓</div>
            <h1>Unknown Command</h1>
            <p style="font-size: 18px; color: #555;">The requested action is not recognized.</p>
            <p><a href="/history">Go to Dashboard</a></p>
        </body>
     </html>
     """


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

    prefs = session.exec(
        select(Preference).where(
            col(Preference.type).in_(["Blocked Sender", "Always Forward"])
        )
    ).all()
    return {
        "success": True,
        "email": email,
        "blocked": [p.item for p in prefs if p.type == "Blocked Sender"],
        "allowed": [p.item for p in prefs if p.type == "Always Forward"],
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
