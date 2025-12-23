import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("python-dotenv not installed, assuming env vars are set")

from backend.services.email_service import EmailService
from backend.services.detector import ReceiptDetector

def mask_email(email_str):
    if not email_str:
        return "N/A"
    try:
        user_part, domain_part = email_str.split("@")
        if len(user_part) <= 2:
            return f"{user_part[0]}***@{domain_part}"
        return f"{user_part[0]}***{user_part[-1]}@{domain_part}"
    except Exception:
        return "***@***"

def debug_emails():
    print("🔍 Starting Debug Email Fetch...")
    
    # Ensure lookback is sufficient for the test
    os.environ["EMAIL_LOOKBACK_DAYS"] = "30"
    
    accounts = EmailService.get_all_accounts()
    print(f"👥 Found {len(accounts)} accounts configured.")

    if not accounts:
        print("❌ No accounts found. Check your .env file or EMAIL_ACCOUNTS variable.")
        return

    for i, acc in enumerate(accounts, 1):
        # Extract variables
        email_addr = acc.get("email")
        password = acc.get("password")
        server = acc.get("imap_server", "imap.gmail.com")

        # Log generic account info to avoid PII/sensitive data leaks
        print(f"\n📧 Processing Account #{i} (Server: {server})")

        if not password:
            print("   ❌ Password missing, skipping.")
            continue

        try:
            print("   🔌 Connecting to mail server...")
            emails = EmailService.fetch_recent_emails(username=email_addr, password=password, imap_server=server)
            print(f"   📬 Fetched {len(emails)} emails.")

            if not emails:
                print("   ⚠️ No emails found. Check lookback window or if emails are 'Read'.")

            for email in emails:
                subject = email.get("subject", "No Subject")
                sender = email.get("from", "No Sender")
                body = email.get("body", "")

                # Deliberately avoid logging full subject/sender to prevent leaking sensitive data
                is_promo = ReceiptDetector.is_promotional_email(subject, body, sender)
                is_receipt = ReceiptDetector.is_receipt(email)
                category = ReceiptDetector.categorize_receipt(email)

                print("\n   ---------------------------------------------------")
                print(f"   > Is Promotional? {is_promo}")
                print(f"   > Is Receipt?     {is_receipt}")
                print(f"   > Category:       {category}")

                if is_promo and not is_receipt:
                    print("   🔴 BLOCKED by Promotional Filter")
                elif is_receipt:
                    print("   🟢 ACCEPTED as Receipt")
                else:
                    print("   ⚪ IGNORED (Not a receipt)")

        except Exception as e:
            print(f"   ❌ Error scanning account: {e}")

if __name__ == "__main__":
    debug_emails()
