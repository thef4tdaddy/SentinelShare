import hashlib
import hmac
import os
from datetime import datetime, timezone

from backend.services.command_service import CommandService
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse

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
