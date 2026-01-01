import os
import sys

# Add the project root to the path so we can import backend modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import update
from sqlmodel import Session, select

from backend.database import engine
from backend.models import ProcessedEmail
from backend.services.email_utils import normalize_sender

def cleanup_relay_addresses():
    """
    Scans the ProcessedEmail table for Apple Private Relay addresses
    and normalizes them in-place.
    """
    print("🚀 Starting Private Relay cleanup...")
    
    with Session(engine) as session:
        # Find all emails with relay addresses
        statement = select(ProcessedEmail).where(ProcessedEmail.sender.like("%@privaterelay.appleid.com%"))
        emails = session.exec(statement).all()
        
        if not emails:
            print("✅ No Private Relay addresses found in database.")
            return

        print(f"🔍 Found {len(emails)} records to process.")
        
        updated_count = 0
        for email in emails:
            original = email.sender
            normalized = normalize_sender(original)
            
            if normalized != original:
                email.sender = normalized
                session.add(email)
                updated_count += 1
                if updated_count % 10 == 0:
                    print(f"📦 Processed {updated_count} records...")

        session.commit()
        print(f"✨ Successfully normalized {updated_count} records!")

if __name__ == "__main__":
    cleanup_relay_addresses()
