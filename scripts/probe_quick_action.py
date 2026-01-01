import sys
import os
import html
from datetime import datetime, timezone
import base64
import hashlib
import hmac

# Setup Environment
project_root = os.getcwd()
sys.path.append(project_root)

# Mock environment variables
os.environ["SECRET_KEY"] = "test-secret"
os.environ["DATABASE_URL"] = "sqlite:///local_dev.db"

from backend.routers.actions import verify_signature
from backend.services.command_service import CommandService
from sqlmodel import Session, select
from backend.database import engine
from backend.models import Preference

def generate_signature(cmd, arg, ts):
    secret = os.environ.get("SECRET_KEY", "test-secret")
    msg = f"{cmd}:{arg}:{ts}"
    return hmac.new(
        secret.encode(), msg.encode(), hashlib.sha256
    ).hexdigest()

def test_quick_action():
    cmd = "SETTINGS"
    arg = "none"
    ts = str(datetime.now(timezone.utc).timestamp())
    
    print(f"Testing {cmd} {arg} logic...")
    
    try:
        # Simulate the SETTINGS logic from actions.py
        with Session(engine) as session:
            print("Querying preferences...")
            prefs = session.exec(select(Preference)).all()
            print(f"Found {len(prefs)} preferences.")
            
            blocked = [p for p in prefs if "Blocked" in p.type]
            allowed = [p for p in prefs if "Forward" in p.type]
            print(f"Blocked: {len(blocked)}, Allowed: {len(allowed)}")
            
        print("✅ Success!")
    except Exception as e:
        print(f"❌ Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_quick_action()
