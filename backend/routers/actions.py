import hashlib
import hmac
import os
from datetime import datetime, timezone

from backend.database import get_session
from backend.models import ManualRule, ProcessedEmail
from backend.services.command_service import CommandService
from backend.services.forwarder import EmailForwarder
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from sqlmodel import Session

router = APIRouter(prefix="/api/actions", tags=["actions"])

SECRET = os.environ.get("SECRET_KEY", "default-insecure-secret-please-change")


def verify_signature(cmd: str, arg: str, ts: str, sig: str) -> bool:
    # Simple HMAC verification
    msg = f"{cmd}:{arg}:{ts}"
    expected = hmac.new(SECRET.encode(), msg.encode(), hashlib.sha256).hexdigest()
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
            return "<h1>❌ Link Expired</h1><p>This action link is too old.</p>"
    except:
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
        from backend.database import engine
        from backend.models import Preference
        from sqlmodel import Session, select

        with Session(engine) as session:
            prefs = session.exec(select(Preference)).all()

        blocked = [p for p in prefs if "Blocked" in p.type]
        allowed = [p for p in prefs if "Forward" in p.type]  # "Always Forward"

        html_list = ""

        if allowed:
            html_list += "<h3 style='color: #22c55e;'>✅ Always Forwarding</h3><ul style='list-style: none; padding: 0;'>"
            for p in allowed:
                html_list += f"<li style='background: #dcfce7; color: #15803d; padding: 8px; margin: 4px 0; border-radius: 4px;'>{p.item}</li>"
            html_list += "</ul>"

        if blocked:
            html_list += "<h3 style='color: #ef4444;'>🚫 Blocked</h3><ul style='list-style: none; padding: 0;'>"
            for p in blocked:
                html_list += f"<li style='background: #fee2e2; color: #b91c1c; padding: 8px; margin: 4px 0; border-radius: 4px;'>{p.item}</li>"
            html_list += "</ul>"

        if not blocked and not allowed:
            html_list = "<p>No active preferences found.</p>"

        return f"""
         <html>
            <body style="font-family: sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                <h1 style="text-align: center; color: #333;">⚙️ Current Settings</h1>
                <div style="background: white; padding: 20px; border-radius: 8px; border: 1px solid #ddd;">
                    {html_list}
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
    else:
        return "<h1>❌ Unknown Command</h1>"


class ToggleIgnoredRequest(BaseModel):
    email_id: int


@router.post("/toggle-ignored")
def toggle_ignored_email(
    request: ToggleIgnoredRequest,
    session: Session = Depends(get_session)
):
    """
    Toggle an ignored email: create a manual rule and forward the email
    """
    # Get the email
    email = session.get(ProcessedEmail, request.email_id)
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    
    # Check if email is ignored
    if email.status != "ignored":
        raise HTTPException(
            status_code=400, 
            detail=f"Email status is '{email.status}', not 'ignored'"
        )
    
    # Create a manual rule based on the email sender
    # Extract domain or email pattern from sender
    sender = email.sender.lower()
    email_pattern = None
    
    # Try to extract email address from sender (format: "Name <email@domain.com>")
    if "<" in sender and ">" in sender:
        email_pattern = sender.split("<")[1].split(">")[0].strip()
    elif "@" in sender:
        # If it's just an email address
        email_pattern = sender.strip()
    
    if not email_pattern:
        raise HTTPException(
            status_code=400, 
            detail="Could not extract email pattern from sender"
        )
    
    # Create the manual rule
    manual_rule = ManualRule(
        email_pattern=email_pattern,
        subject_pattern=None,
        priority=10,
        purpose=f"Auto-created from ignored email: {email.subject[:50]}",
    )
    session.add(manual_rule)
    
    # Forward the email now
    target_email = os.environ.get("WIFE_EMAIL")
    if not target_email:
        session.rollback()
        raise HTTPException(
            status_code=500, 
            detail="WIFE_EMAIL not configured"
        )
    
    # Prepare email data for forwarding
    email_data = {
        "message_id": email.email_id,
        "subject": email.subject,
        "from": email.sender,
        "body": f"[Previously ignored email from {email.received_at}]\n\n",
        "account_email": email.account_email,
    }
    
    # Try to forward the email
    success = EmailForwarder.forward_email(email_data, target_email)
    
    if not success:
        session.rollback()
        raise HTTPException(
            status_code=500, 
            detail="Failed to forward email"
        )
    
    # Update email status to forwarded
    email.status = "forwarded"
    email.reason = "Manually toggled from ignored"
    
    # Commit changes
    session.add(email)
    session.commit()
    session.refresh(email)
    session.refresh(manual_rule)
    
    return {
        "success": True,
        "email": email,
        "rule": manual_rule,
        "message": f"Email forwarded and rule created for {email_pattern}"
    }
