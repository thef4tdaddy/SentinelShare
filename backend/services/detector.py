import fnmatch
import os
import re
from typing import Any, Dict, Optional

from sqlmodel import select

from ..models import ManualRule, Preference
from .email_service import EmailService


class ReceiptDetector:
    @staticmethod
    def is_receipt(email: Any, session: Any = None) -> bool:
        """
        Determines if an email is a receipt based on subject, body, and sender.
        Optional 'session' allows checking against database ManualRule and Preference.
        """
        subject = (
            getattr(email, "subject", None) or email.get("subject", "") or ""
        ).lower()
        body = (getattr(email, "body", None) or email.get("body", "") or "").lower()
        sender = (
            getattr(email, "sender", None)
            or getattr(email, "from", None)
            or email.get("sender", "")
            or email.get("from", "")
            or ""
        ).lower()

        # STEP -1: Check for Database Overrides (Manual Rules & Preferences)
        if session:
            try:

                # 1. Manual Rules (Priority ordering)
                matched_rule = ReceiptDetector._check_manual_rules(
                    subject, sender, session
                )
                if matched_rule:
                    print(
                        f"✅ Manual rule match: {matched_rule.purpose or 'No purpose'}"
                    )
                    return True

                # 2. Preferences (Always Forward)
                always_forward = session.exec(
                    select(Preference).where(Preference.type == "Always Forward")
                ).all()
                for pref in always_forward:
                    p_item = pref.item.lower()
                    if p_item in sender or p_item in subject:
                        print(f"✅ Preference match (Always Forward): {pref.item}")
                        return True

                # 3. Preferences (Blocked Sender / Category)
                blocked = session.exec(
                    select(Preference).where(
                        Preference.type.in_(["Blocked Sender", "Blocked Category"])  # type: ignore
                    )
                ).all()
                for pref in blocked:
                    p_item = pref.item.lower()
                    if p_item in sender or p_item in subject:
                        print(f"🚫 Preference match (Blocked): {pref.item}")
                        return False
            except Exception as e:
                print(f"⚠️ Error checking database rules: {type(e).__name__}")

        # STEP 0: EXCLUDE reply emails and forwards first
        if ReceiptDetector.is_reply_or_forward(subject, sender):
            print(f"🚫 Excluded reply/forward email: {subject}")
            return False

        # STEP 0.5: Check for strong receipt indicators (OVERRIDES promotional filter)
        if ReceiptDetector.has_strong_receipt_indicators(subject, body):
            print(f"✅ Strong receipt indicators found: {subject}")
            return True

        # STEP 1: HARD EXCLUDE spam/promotional emails
        if ReceiptDetector.is_promotional_email(subject, body, sender):
            print(f"🚫 Excluded promotional email: {subject}")
            return False

        # STEP 1.5: EXCLUDE shipping notifications (not receipts)
        if ReceiptDetector.is_shipping_notification(subject, body, sender):
            print(f"🚫 Excluded shipping notification: {subject}")
            return False

        # STEP 3: Check for transactional patterns (order + amount + confirmation)
        transactional_score = ReceiptDetector.calculate_transactional_score(
            subject, body, sender
        )
        if transactional_score >= 3:
            print(f"✅ High transactional score ({transactional_score}): {subject}")
            return True

        # STEP 4: Known receipt senders with transaction confirmation
        if ReceiptDetector.is_known_receipt_sender(
            sender
        ) and ReceiptDetector.has_transaction_confirmation(subject, body):
            print(f"✅ Known sender with transaction: {subject}")
            return True

        print(f"❌ Not a receipt: {subject}")
        return False

    @staticmethod
    def debug_is_receipt(email: Any, session: Any = None) -> Dict[str, Any]:
        """
        Detailed trace of the logic for debugging or history analysis.
        """
        subject = (
            getattr(email, "subject", None) or email.get("subject", "") or ""
        ).lower()
        (getattr(email, "body", None) or email.get("body", "") or "").lower()
        sender = (
            getattr(email, "sender", None)
            or email.get("from", None)
            or email.get("sender", "")
            or ""
        ).lower()

        trace: Dict[str, Any] = {
            "subject": subject,
            "sender": sender,
            "steps": [],
            "final_decision": False,
            "matched_by": None,
        }

        # Check Manual Rules
        matched_rule = ReceiptDetector._check_manual_rules(subject, sender, session)
        if matched_rule:
            trace["steps"].append(
                {
                    "step": "Manual Rule",
                    "result": True,
                    "detail": f"Matched rule: {matched_rule.purpose}",
                }
            )
            trace["final_decision"] = True
            trace["matched_by"] = "Manual Rule"
            return trace

        # ... (rest of trace logic would follow same structure as is_receipt)
        # Simplified for now, will expand as needed.
        decision = ReceiptDetector.is_receipt(email, session)
        trace["final_decision"] = decision
        return trace

    @staticmethod
    def _check_manual_rules(
        subject: str, sender: str, session: Any
    ) -> Optional[ManualRule]:
        """Helper to check if any manual rule matches."""
        if not session:
            return None
        rules = session.exec(
            select(ManualRule).order_by(ManualRule.priority.desc())  # type: ignore
        ).all()
        for rule in rules:
            matches = True
            if rule.email_pattern:
                if not fnmatch.fnmatch(sender, rule.email_pattern.lower()):
                    matches = False
            if matches and rule.subject_pattern:
                if not fnmatch.fnmatch(subject, rule.subject_pattern.lower()):
                    matches = False
            if matches:
                return rule
        return None

    @staticmethod
    def is_reply_or_forward(subject: str, sender: str) -> bool:
        reply_patterns = [
            r"re:\s*",  # "Re: "
            r"fwd?:\s*",  # "Fwd: " or "Fw: "
            r"fw:\s*",  # "Fw: "
            r"forward:\s*",  # "Forward: "
            r"\[fwd\]",  # "[FWD]"
            r"\(fwd\)",  # "(FWD)"
        ]

        # Use re.IGNORECASE for all patterns
        if any(re.match(pattern, subject, re.IGNORECASE) for pattern in reply_patterns):
            return True

        # Check if from wife's email
        wife_email = (os.environ.get("WIFE_EMAIL") or "your-wife@email.com").lower()
        if wife_email in sender:
            return True

        # Check if from your own email addresses
        your_emails = [
            e.lower()
            for e in [
                os.environ.get("GMAIL_EMAIL"),
                os.environ.get("ICLOUD_EMAIL"),
                os.environ.get("SENDER_EMAIL"),
            ]
            if e
        ]

        # Add emails from centralized account logic
        accounts = EmailService.get_all_accounts()
        for acc in accounts:
            if acc.get("email"):
                your_emails.append(acc.get("email").lower())

        if any(email in sender for email in your_emails):
            return True

        return False

    @staticmethod
    def is_shipping_notification(subject: str, body: str, sender: str) -> bool:
        shipping_email_patterns = [
            r"shipment-tracking@amazon\.com",
            r"ship-confirm@amazon\.com",
            r"shipping@amazon\.com",
            r"delivery@amazon\.com",
            r"tracking@amazon\.com",
            r"shipment@amazon\.com",
            r"logistics@amazon\.com",
            r"fulfillment@amazon\.com",
            r"shipping-",
            r"delivery-",
            r"tracking-",
            r"shipment-",
            # Other carriers
            r"tracking@ups\.com",
            r"delivery@fedex\.com",
            r"tracking@usps\.com",
            r"shipment@dhl\.com",
        ]

        if any(
            re.search(pattern, sender, re.IGNORECASE)
            for pattern in shipping_email_patterns
        ):
            return True

        shipping_patterns = [
            # Amazon shipping patterns
            r"your\s+.*\s+(has\s+)?shipped",
            r"shipped\s+today",
            r"out\s+for\s+delivery",
            r"delivered",
            r"delivery\s+update",
            r"package\s+delivered",
            r"package\s+update",
            r"shipment\s+notification",
            r"tracking\s+information",
            r"track\s+your\s+package",
            r"delivery\s+notification",
            r"shipment\s+delivered",
            r"order.*shipped",
            r"item.*shipped",
            r"package.*shipped",
            # Delivery status updates
            r"delivery\s+attempt",
            r"delivery\s+rescheduled",
            r"delivery\s+delayed",
            r"package\s+is\s+on\s+the\s+way",
            r"arriving\s+today",
            r"arriving\s+tomorrow",
            r"expected\s+delivery",
            r"estimated\s+delivery",
            # Carrier notifications
            r"ups\s+delivery",
            r"fedex\s+delivery",
            r"usps\s+delivery",
            r"amazon\s+delivery",
            r"dhl\s+delivery",
            # Amazon-specific shipping language
            r"amazon.*shipment",
            r"preparing\s+to\s+ship",
            r"now\s+shipped",
            r"has\s+been\s+shipped",
            r"will\s+arrive",
        ]

        text = f"{subject} {body}".lower()

        has_shipping_pattern = any(
            re.search(pattern, text, re.IGNORECASE) for pattern in shipping_patterns
        )
        if not has_shipping_pattern:
            return False

        purchase_indicators = [
            r"order\s+confirmation",
            r"purchase\s+confirmation",
            r"payment\s+confirmation",
            r"receipt",
            r"invoice",
            r"charged",
            r"payment\s+received",
            r"total.*\$\d+",
            r"amount.*\$\d+",
            r"order\s+total",
            r"subtotal",
            r"tax.*\$\d+",
            r"order\s+placed",
            r"thank\s+you\s+for.*order",
        ]

        has_purchase_indicators = any(
            re.search(pattern, text, re.IGNORECASE) for pattern in purchase_indicators
        )

        return has_shipping_pattern and not has_purchase_indicators

    @staticmethod
    def is_promotional_email(subject: str, body: str, sender: str) -> bool:
        promotional_keywords = [
            "sale",
            "discount",
            "coupon",
            "deal",
            "deals",
            "offer",
            "promotion",
            "promo",
            "save",
            "savings",
            "off",
            "clearance",
            "limited time",
            "hurry",
            "newsletter",
            "weekly ad",
            "special offer",
            "flash sale",
            "free shipping",
            "member exclusive",
            "subscriber",
            "unsubscribe",
            "marketing",
            "browse",
            "shop now",
            "check out",
            "new arrivals",
            "trending",
            "bestseller",
            "featured",
            "recommended",
            "catalog",
            "circular",
            "black friday",
            "cyber monday",
            "holiday sale",
            "back to school",
            "rewards program",
            "loyalty",
            "points earned",
            "cashback earned",
            "gift card",
            "sweepstakes",
            "contest",
            "giveaway",
            "win",
            "personalized",
            "just for you",
            "based on your",
            "you might like",
            # Gaming/deals specific
            "weekly digest",
            "daily digest",
            "roundup",
            "this week",
            "new releases",
            "best deals",
            "top deals",
            "hot deals",
            "price drop",
            "discounted",
            "on sale",
            "reduced price",
            "lowest price",
            "price alert",
            "wishlist",
            "watch list",
            "compare prices",
            "deal alert",
            # Newsletter patterns
            "digest",
            "update",
            "news",
            "updates",
            "latest",
            "recent",
            "weekly",
            "monthly",
            "daily",
            "edition",
            "issue",
            "curated",
            "handpicked",
            "selected",
            "picks",
            # Marketing action words
            "discover",
            "explore",
            "find",
            "search",
            "browse",
            "view all",
            "see more",
            "learn more",
            "read more",
            "get started",
            "sign up",
            "join",
            "register",
            "download",
            "try",
            # Promotional urgency
            "expires",
            "ending",
            "last chance",
            "final",
            "closing",
            "while supplies last",
            "limited quantity",
            "almost gone",
        ]

        # Whitelist specific phrases that might look promotional but are receipts
        text = f"{subject} {body}".lower()
        if "subscribe & save" in text or "subscription order" in text:
            return False

        # Exempt government-related senders from being treated as promotional
        if any(gov in sender for gov in ["irs", "dmv", "gov"]):
            return False

        if any(keyword in subject for keyword in promotional_keywords):
            return True

        if any(keyword in body for keyword in promotional_keywords):
            return True

        marketing_patterns = [
            r"\d+%\s*off",
            r"save\s*\$\d+",
            r"free\s*shipping",
            r"limited\s*time",
            r"act\s*now",
            r"shop\s*now",
            r"don't\s*miss",
            r"hurry",
            r"ends\s*(soon|today)",
            r"check\s*this\s*week",
            r"new\s*discounts",
            r"best\s*deals",
            r"weekly\s*digest",
            r"\+\d+\s*this\s*week",
            r"deals?\s*weekly",
            r"price\s*drop",
            r"now\s*\$\d+",
        ]

        if any(
            re.search(pattern, subject, re.IGNORECASE)
            or re.search(pattern, body, re.IGNORECASE)
            for pattern in marketing_patterns
        ):
            return True

        tracking_patterns = [
            r"awstrack\.me",
            r"click\.",
            r"track\.",
            r"utm_",
            r"newsletter",
            r"unsubscribe",
        ]

        # JS used replace(/[\/\\]/g, "") before checking source, but in python we check string
        # JS: body.includes(pattern.source...) -> Replicated by checking regex simply
        if any(
            re.search(pattern, body, re.IGNORECASE) for pattern in tracking_patterns
        ):
            return True

        deals_patterns = [
            r"deals?\s*net",
            r"deals?\s*com",
            r"bargain",
            r"slickdeals",
            r"reddit.*deals",
            r"steam.*sale",
            r"game.*deals",
        ]

        if any(
            re.search(pattern, sender, re.IGNORECASE)
            or re.search(pattern, subject, re.IGNORECASE)
            or re.search(pattern, body, re.IGNORECASE)
            for pattern in deals_patterns
        ):
            return True

        return False

    @staticmethod
    def has_strong_receipt_indicators(subject: str, body: str) -> bool:
        strong_keywords = [
            "receipt",
            "invoice",
            "order confirmation",
            "payment confirmation",
            "purchase confirmation",
            "order complete",
            "payment received",
            "order summary",
            "order placed",
            "billing statement",
            "account statement",
            "thank you for your order",
            "order total",
            "amount charged",
            "subscribe & save",
            "subscription order",
            "ordered",
            "ordered:",
            "renewal",
            "license plate renewal",
        ]

        # Check literal keywords
        subject_lower = subject.lower()
        body_lower = body.lower()
        has_keyword = any(
            keyword in subject_lower or keyword in body_lower
            for keyword in strong_keywords
        )

        # Check regex patterns (handles interleaved text like "Order #123 Confirmation")
        strong_regex_patterns = [
            r"order.*confirmation",
            r"payment.*confirmation",
            r"purchase.*confirmation",
        ]

        text = f"{subject} {body}"
        has_regex = any(
            re.search(pattern, text, re.IGNORECASE) for pattern in strong_regex_patterns
        )

        if not (has_keyword or has_regex):
            return False

        supporting_evidence = [
            r"order\s*#?\s*[a-z0-9\-]{6,}",
            r"invoice\s*#?\s*[a-z0-9\-]{6,}",
            r"transaction\s*#?\s*[a-z0-9\-]{6,}",
            r"tracking\s*#?\s*[a-z0-9\-]{8,}",
            r"\$[0-9,]+\.[0-9]{2}",
            r"total:?\s*\$[0-9,]+\.[0-9]{2}",
            r"amount:?\s*\$[0-9,]+\.[0-9]{2}",
            r"paid:?\s*\$[0-9,]+\.[0-9]{2}",
            r"view your order",
            r"arriving (tomorrow|today|monday|tuesday|wednesday|thursday|friday|saturday|sunday)",
        ]

        text = f"{subject} {body}"
        return any(
            re.search(pattern, text, re.IGNORECASE) for pattern in supporting_evidence
        )

    @staticmethod
    def calculate_transactional_score(subject: str, body: str, sender: str) -> int:
        score = 0
        text = f"{subject} {body} {sender}"

        indicators = [
            (r"order\s*#?\s*[a-z0-9\-]{6,}", 2),
            (r"\$[0-9,]+\.[0-9]{2}", 2),
            (r"thank\s*you\s*for\s*(your\s*)?(order|purchase)", 2),
            (r"invoice\s*#?\s*[a-z0-9\-]{6,}", 2),
            (r"transaction", 1),
            (r"payment", 1),
            (r"billing", 1),
            (r"statement", 1),
            (r"account\s*balance", 1),
            (r"due\s*date", 1),
            (r"autopay", 1),
            (r"direct\s*debit", 1),
            (r"^ordered:", 2),
        ]

        for pattern, points in indicators:
            if re.search(pattern, text, re.IGNORECASE):
                score += points

        return score

    @staticmethod
    def is_known_receipt_sender(sender: str) -> bool:
        reliable_receipt_senders = [
            "amazon.com",
            "amazon.co",
            "amazonses.com",
            "auto-confirm@amazon.com",
            "order-update@amazon.com",
            "digital-no-reply@amazon.com",
            "payments-messages@amazon.com",
            "paypal.com",
            "paypal-communications.com",
            "stripe.com",
            "square.com",
            "apple.com",
            "itunes.com",
            "google.com",
            "googlepayments.com",
            "microsoft.com",
            "xbox.com",
            "uber.com",
            "lyft.com",
            "doordash.com",
            "grubhub.com",
            "instacart.com",
            "shipt.com",
        ]
        return any(s in sender for s in reliable_receipt_senders)

    @staticmethod
    def has_transaction_confirmation(subject: str, body: str) -> bool:
        confirmation_patterns = [
            r"confirmation",
            r"receipt",
            r"order\s*#",
            r"invoice",
            r"payment",
            r"charged",
            r"bill",
            r"statement",
            r"\$[0-9,]+\.[0-9]{2}",
        ]
        return any(
            re.search(pattern, subject, re.IGNORECASE)
            or re.search(pattern, body, re.IGNORECASE)
            for pattern in confirmation_patterns
        )

    @staticmethod
    def categorize_receipt(email: Any) -> str:
        sender = (
            getattr(email, "sender", None)
            or getattr(email, "from", None)
            or email.get("sender", "")
            or email.get("from", "")
            or ""
        ).lower()
        subject = (
            getattr(email, "subject", None) or email.get("subject", "") or ""
        ).lower()

        if "amazon" in sender or "aws" in sender:
            return "amazon"
        if "uber" in sender or "lyft" in sender:
            return "transportation"
        if any(s in sender for s in ["doordash", "grubhub", "ubereats"]):
            return "food-delivery"
        if any(s in sender for s in ["starbucks", "mcdonalds", "subway"]):
            return "restaurants"
        if any(s in sender for s in ["walmart", "target", "costco"]):
            return "retail"
        if any(s in sender for s in ["netflix", "spotify", "adobe"]):
            return "subscriptions"
        if any(s in sender for s in ["paypal", "venmo", "square"]):
            return "payments"

        if any(
            s in sender for s in ["att", "verizon", "comcast", "xfinity", "spectrum"]
        ):
            return "utilities"

        if (
            any(s in sender for s in ["cvs", "walgreens", "pharmacy"])
            or "prescription" in subject
            or "copay" in subject
        ):
            return "healthcare"

        if (
            any(s in sender for s in ["irs", "dmv", "gov"])
            or "tax" in subject
            or "license" in subject
        ):
            return "government"

        return "other"

    @staticmethod
    def get_detection_confidence(email: Any) -> int:
        subject = (
            getattr(email, "subject", None) or email.get("subject", "") or ""
        ).lower()
        body = (getattr(email, "body", None) or email.get("body", "") or "").lower()
        sender = (
            getattr(email, "sender", None)
            or getattr(email, "from", None)
            or email.get("sender", "")
            or email.get("from", "")
            or ""
        ).lower()

        if ReceiptDetector.is_promotional_email(subject, body, sender):
            return 0

        confidence = 0
        if ReceiptDetector.has_strong_receipt_indicators(subject, body):
            confidence += 40

        transaction_score = ReceiptDetector.calculate_transactional_score(
            subject, body, sender
        )
        confidence += transaction_score * 10

        if ReceiptDetector.is_known_receipt_sender(sender):
            confidence += 20

        if ReceiptDetector.has_transaction_confirmation(subject, body):
            confidence += 10

        return min(confidence, 100)
