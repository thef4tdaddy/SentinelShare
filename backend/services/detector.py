import re
import os

class ReceiptDetector:
    @staticmethod
    def is_receipt(email_data: dict) -> bool:
        subject = (email_data.get("subject") or "").lower()
        body = (email_data.get("body") or "").lower()
        sender = (email_data.get("from") or "").lower()

        # STEP 0: EXCLUDE reply emails and forwards first
        if ReceiptDetector.is_reply_or_forward(subject, sender):
            print(f"🚫 Excluded reply/forward email: {subject}")
            return False

        # STEP 1: HARD EXCLUDE spam/promotional emails
        if ReceiptDetector.is_promotional_email(subject, body, sender):
            print(f"🚫 Excluded promotional email: {subject}")
            return False

        # STEP 1.5: EXCLUDE shipping notifications (not receipts)
        if ReceiptDetector.is_shipping_notification(subject, body, sender):
            print(f"🚫 Excluded shipping notification: {subject}")
            return False

        # STEP 2: Check for strong receipt indicators
        if ReceiptDetector.has_strong_receipt_indicators(subject, body):
            print(f"✅ Strong receipt indicators found: {subject}")
            return True

        # STEP 3: Check for transactional patterns
        transactional_score = ReceiptDetector.calculate_transactional_score(subject, body, sender)
        if transactional_score >= 3:
            print(f"✅ High transactional score ({transactional_score}): {subject}")
            return True

        # STEP 4: Known receipt senders with transaction confirmation
        if ReceiptDetector.is_known_receipt_sender(sender) and ReceiptDetector.has_transaction_confirmation(subject, body):
            print(f"✅ Known sender with transaction: {subject}")
            return True

        print(f"❌ Not a receipt: {subject}")
        return False

    @staticmethod
    def is_reply_or_forward(subject: str, sender: str) -> bool:
        reply_patterns = [
            r"^re:\s*",  # "Re: "
            r"^fwd?:\s*",  # "Fwd: " or "Fw: "
            r"^fw:\s*",  # "Fw: "
            r"^forward:\s*",  # "Forward: "
            r"\[fwd\]",  # "[FWD]"
            r"\(fwd\)",  # "(FWD)"
        ]

        has_reply_subject = any(re.search(pattern, subject, re.IGNORECASE) for pattern in reply_patterns)

        # Check if from wife or self
        wife_email = (os.environ.get("WIFE_EMAIL") or "your-wife@email.com").lower()
        is_from_wife = wife_email in sender

        your_emails = [
            os.environ.get("GMAIL_EMAIL"),
            os.environ.get("ICLOUD_EMAIL"),
            os.environ.get("SENDER_EMAIL"),
        ]
        is_from_you = any(email and email.lower() in sender for email in your_emails if email)

        return has_reply_subject or is_from_wife or is_from_you

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
            r"tracking@ups\.com",
            r"delivery@fedex\.com",
            r"tracking@usps\.com",
            r"shipment@dhl\.com",
        ]

        if any(re.search(pattern, sender, re.IGNORECASE) for pattern in shipping_email_patterns):
            return True

        shipping_patterns = [
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
            r"delivery\s+attempt",
            r"delivery\s+rescheduled",
            r"delivery\s+delayed",
            r"package\s+is\s+on\s+the\s+way",
            r"arriving\s+today",
            r"arriving\s+tomorrow",
            r"expected\s+delivery",
            r"estimated\s+delivery",
            r"ups\s+delivery",
            r"fedex\s+delivery",
            r"usps\s+delivery",
            r"amazon\s+delivery",
            r"dhl\s+delivery",
            r"your\s+amazon.*order",
            r"amazon.*shipment",
            r"preparing\s+to\s+ship",
            r"now\s+shipped",
            r"has\s+been\s+shipped",
            r"will\s+arrive",
        ]

        text = f"{subject} {body}".lower()
        has_shipping_pattern = any(re.search(pattern, text, re.IGNORECASE) for pattern in shipping_patterns)

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

        has_purchase_indicators = any(re.search(pattern, text, re.IGNORECASE) for pattern in purchase_indicators)
        return has_shipping_pattern and not has_purchase_indicators

    @staticmethod
    def is_promotional_email(subject: str, body: str, sender: str) -> bool:
        promotional_keywords = [
            "sale", "discount", "coupon", "deal", "deals", "offer", "promotion", "promo",
            "save", "savings", "off", "clearance", "limited time", "hurry", "newsletter",
            "weekly ad", "special offer", "flash sale", "free shipping", "member exclusive",
            "subscriber", "unsubscribe", "marketing", "browse", "shop now", "check out",
            "new arrivals", "trending", "bestseller", "featured", "recommended", "catalog",
            "circular", "black friday", "cyber monday", "holiday sale", "back to school",
            "rewards program", "loyalty", "points earned", "cashback earned", "gift card",
            "sweepstakes", "contest", "giveaway", "win", "personalized", "just for you",
            "based on your", "you might like", "weekly digest", "daily digest", "roundup",
            "this week", "new releases", "best deals", "top deals", "hot deals", "price drop",
            "discounted", "on sale", "reduced price", "lowest price", "price alert", "wishlist",
            "watch list", "compare prices", "deal alert", "digest", "update", "news", "updates",
            "latest", "recent", "weekly", "monthly", "daily", "edition", "issue", "curated",
            "handpicked", "selected", "picks", "discover", "explore", "find", "search",
            "browse", "view all", "see more", "learn more", "read more", "get started",
            "sign up", "join", "register", "download", "try", "expires", "ending", "last chance",
            "final", "closing", "while supplies last", "limited quantity", "almost gone",
        ]

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

        if any(re.search(pattern, subject, re.IGNORECASE) or re.search(pattern, body, re.IGNORECASE) for pattern in marketing_patterns):
            return True

        tracking_patterns = [
            r"awstrack\.me",
            r"click\.",
            r"track\.",
            r"utm_",
            r"newsletter",
            r"unsubscribe",
        ]
        
        # In JS this was body.includes(pattern.source.replace()...). Regex search is simpler.
        if any(re.search(pattern, body, re.IGNORECASE) for pattern in tracking_patterns):
            return True
            
        deals_patterns = [
            r"deals?\s*net", r"deals?\s*com", r"bargain", r"slickdeals",
            r"reddit.*deals", r"steam.*sale", r"game.*deals",
        ]
        
        if any(re.search(pattern, sender, re.IGNORECASE) or re.search(pattern, subject, re.IGNORECASE) or re.search(pattern, body, re.IGNORECASE) for pattern in deals_patterns):
            return True

        return False

    @staticmethod
    def has_strong_receipt_indicators(subject: str, body: str) -> bool:
        strong_keywords = [
            "receipt", "invoice", "order confirmation", "payment confirmation",
            "purchase confirmation", "order complete", "payment received", "order summary",
            "order placed", "billing statement", "account statement", "thank you for your order",
            "order total", "amount charged",
        ]

        if not any(keyword in subject or keyword in body for keyword in strong_keywords):
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
        ]

        text = f"{subject} {body}"
        return any(re.search(pattern, text, re.IGNORECASE) for pattern in supporting_evidence)

    @staticmethod
    def calculate_transactional_score(subject: str, body: str, sender: str) -> int:
        score = 0
        text = f"{subject} {body} {sender}".lower()

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
        ]

        for pattern, points in indicators:
            if re.search(pattern, text, re.IGNORECASE):
                score += points
        return score

    @staticmethod
    def is_known_receipt_sender(sender: str) -> bool:
        reliable_senders = [
            "amazon.com", "amazon.co", "amazonses.com", "auto-confirm@amazon.com",
            "order-update@amazon.com", "digital-no-reply@amazon.com", "payments-messages@amazon.com",
            "paypal.com", "paypal-communications.com", "stripe.com", "square.com", "apple.com",
            "itunes.com", "google.com", "googlepayments.com", "microsoft.com", "xbox.com",
            "uber.com", "lyft.com", "doordash.com", "grubhub.com", "instacart.com", "shipt.com",
        ]
        return any(s in sender for s in reliable_senders)

    @staticmethod
    def has_transaction_confirmation(subject: str, body: str) -> bool:
        patterns = [
            r"confirmation", r"receipt", r"order\s*#", r"invoice", r"payment",
            r"charged", r"bill", r"statement", r"\$[0-9,]+\.[0-9]{2}",
        ]
        return any(re.search(p, subject, re.IGNORECASE) or re.search(p, body, re.IGNORECASE) for p in patterns)

    @staticmethod
    def categorize_receipt(sender: str, subject: str) -> str:
        sender = sender.lower()
        subject = subject.lower()

        if "amazon" in sender or "aws" in sender: return "amazon"
        if "uber" in sender or "lyft" in sender: return "transportation"
        if "doordash" in sender or "grubhub" in sender or "ubereats" in sender: return "food-delivery"
        if "starbucks" in sender or "mcdonalds" in sender or "subway" in sender: return "restaurants"
        if "walmart" in sender or "target" in sender or "costco" in sender: return "retail"
        if "netflix" in sender or "spotify" in sender or "adobe" in sender: return "subscriptions"
        if "paypal" in sender or "venmo" in sender or "square" in sender: return "payments"
        
        if any(s in sender for s in ["att", "verizon", "comcast", "xfinity", "spectrum"]): return "utilities"
        if any(s in sender for s in ["cvs", "walgreens", "pharmacy"]) or "prescription" in subject or "copay" in subject: return "healthcare"
        if any(s in sender for s in ["irs", "dmv", "gov"]) or "tax" in subject or "license" in subject: return "government"
        
        return "other"
