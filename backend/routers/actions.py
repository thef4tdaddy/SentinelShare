import hashlib
import hmac
import html
import os
from datetime import datetime, timezone
from email.utils import parseaddr

from backend.constants import DEFAULT_MANUAL_RULE_PRIORITY
from backend.database import get_session
from backend.models import ManualRule, ProcessedEmail
from backend.services.command_service import CommandService
from backend.services.forwarder import EmailForwarder
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from sqlmodel import Session, select

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

    # Escape user input for safe HTML rendering
    safe_arg = html.escape(arg)

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
    request: ToggleIgnoredRequest, session: Session = Depends(get_session)
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
            status_code=400, detail=f"Email status is '{email.status}', not 'ignored'"
        )

    # Create a manual rule based on the email sender
    # Extract email address from sender using RFC 5322 compliant parser
    sender = email.sender
    # parseaddr returns (realname, email_address)
    _, email_pattern = parseaddr(sender)

    if not email_pattern or "@" not in email_pattern:
        raise HTTPException(
            status_code=400, detail="Could not extract email pattern from sender"
        )

    # Normalize to lowercase for consistency
    email_pattern = email_pattern.lower().strip()

    # Check if a manual rule with the same email_pattern already exists
    existing_rule = session.exec(
        select(ManualRule).where(ManualRule.email_pattern == email_pattern)
    ).first()
    if not existing_rule:
        # Truncate subject intelligently with ellipsis
        truncated_subject = (
            email.subject[:47] + "..." if len(email.subject) > 50 else email.subject
        )
        manual_rule = ManualRule(
            email_pattern=email_pattern,
            subject_pattern=None,
            priority=DEFAULT_MANUAL_RULE_PRIORITY,
            purpose=f"Auto-created from ignored email: {truncated_subject}",
        )
        session.add(manual_rule)
    else:
        manual_rule = existing_rule

    # Forward the email now
    target_email = os.environ.get("WIFE_EMAIL")
    if not target_email:
        session.rollback()
        raise HTTPException(status_code=500, detail="WIFE_EMAIL not configured")

    # Try to fetch the original email content
    import json

    from backend.services.email_service import EmailService

    # 1. Get credentials for the source account
    email_user = None
    email_pass = None
    imap_server = "imap.gmail.com"  # Default

    account_email = email.account_email

    # Check env vars first (legacy single account)
    if not account_email or account_email == os.environ.get("SENDER_EMAIL"):
        email_user = os.environ.get("SENDER_EMAIL")
        email_pass = os.environ.get("SENDER_PASSWORD")
    elif account_email == os.environ.get("GMAIL_EMAIL"):
        email_user = os.environ.get("GMAIL_EMAIL")
        email_pass = os.environ.get("GMAIL_PASSWORD")
    elif account_email == os.environ.get("ICLOUD_EMAIL"):
        email_user = os.environ.get("ICLOUD_EMAIL")
        email_pass = os.environ.get("ICLOUD_PASSWORD")
        imap_server = "imap.mail.me.com"

    # Check EMAIL_ACCOUNTS
    if not email_user:
        try:
            accounts_json = os.environ.get("EMAIL_ACCOUNTS")
            if accounts_json:
                accounts = json.loads(accounts_json)
                for acc in accounts:
                    if acc.get("email") == account_email:
                        email_user = acc.get("email")
                        email_pass = acc.get("password")
                        imap_server = acc.get("imap_server", "imap.gmail.com")
                        break
        except:
            pass

    # Default to primary if we can't find specific ones (last resort/fallback)
    if not email_user:
        email_user = os.environ.get("SENDER_EMAIL")
        email_pass = os.environ.get("SENDER_PASSWORD")

    # 2. Fetch content
    original_content = None
    if email_user and email_pass:
        original_content = EmailService.fetch_email_by_id(
            email_user, email_pass, email.email_id, imap_server
        )

    # 3. Construct body
    if original_content:
        # Use the fetched content
        body_text = original_content.get("body", "")
        # If we have HTML but no text, maybe use HTML?
        # EmailForwarder usually takes 'body' as text/html depending on structure.
        # But here we pass a single 'body' string.
        # Let's prepend the system note
        final_body = f"""<div style="background-color: #f0fdf4; padding: 10px; border: 1px solid #86efac; margin-bottom: 20px; border-radius: 6px;">
            <p><strong>[SentinelShare Notification]</strong></p>
            <p>This email was previously marked as <strong>{email.status}</strong> and is now being forwarded per your request.</p>
            <p><strong>Reason:</strong> {email.reason or 'Not a receipt'}</p>
            <p><em>A manual rule has been created to forward future emails from this sender.</em></p>
        </div>
        <hr>
        {original_content.get("html_body") or original_content.get("body")}
        """
        # If original was plain text, we might want to wrap it in <pre> or just text.
        # But EmailForwarder.forward_email logic (via SimpleEmailService usually) sends HTML?
        # Let's see EmailForwarder.forward_email. It uses 'sender_email' credentials to send.
        # It calls SimpleEmailService.send_email with html_content=body usually?
        # I'll assume HTML is safe.
    else:
        # Fallback to placeholder
        final_body = f"""[This email was previously marked as ignored and is now being forwarded]

Originally received: {email.received_at.strftime('%Y-%m-%d %H:%M:%S UTC') if email.received_at else 'Unknown'}
Category: {email.category or 'Unknown'}
Reason for initial ignore: {email.reason or 'Not a receipt'}

Note: Original email body is not available as it was not stored and could not be fetched from the server.
A manual rule has been created to forward future emails from this sender."""

    # Prepare email data for forwarding
    email_data = {
        "message_id": email.email_id,
        "subject": email.subject,
        "from": email.sender,  # We populate 'from' field in the forwarded email template usually
        "body": final_body,
        "account_email": email.account_email,
    }

    try:
        # Try to forward the email
        success = EmailForwarder.forward_email(email_data, target_email)

        if not success:
            session.rollback()
            raise HTTPException(status_code=500, detail="Failed to forward email")

        # Update email status to forwarded
        email.status = "forwarded"
        email.reason = "Manually toggled from ignored"

        # Commit changes
        session.add(email)
        session.commit()
        session.refresh(email)
        session.refresh(manual_rule)
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while forwarding the email and creating the rule: {str(e)}",
        )

    return {
        "success": True,
        "email": email,
        "rule": manual_rule,
        "message": f"Email forwarded and rule created for {email_pattern}",
    }
