from typing import Any, Dict, Optional


from ..models import ManualRule
from .detectors import (
    ManualRuleStrategy,
    PromotionalStrategy,
    ShippingStrategy,
    TransactionalStrategy,
)


class ReceiptDetector:
    """
    Receipt detection system using pluggable detection strategies.

    This class coordinates multiple detection strategies to determine if an email
    is a receipt. Strategies are evaluated in priority order.
    """

    # Singleton strategy instances
    _manual_rule_strategy = ManualRuleStrategy()
    _transactional_strategy = TransactionalStrategy()
    _promotional_strategy = PromotionalStrategy()
    _shipping_strategy = ShippingStrategy()

    @staticmethod
    def is_receipt(email: Any, session: Any = None) -> bool:
        """
        Determines if an email is a receipt based on subject, body, and sender.
        Optional 'session' allows checking against database ManualRule and Preference.

        This method uses a strategy-based system to evaluate emails against multiple
        detection strategies in priority order.
        """
        subject = (
            getattr(email, "subject", None) or email.get("subject", "") or ""
        ).lower()

        # Strategy 1: Manual Rules & Preferences (highest priority)
        manual_result = ReceiptDetector._manual_rule_strategy.detect(email, session)
        if manual_result.is_match:
            print(f"✅ {manual_result.reason}")
            return True
        elif manual_result.reason and "Blocked" in manual_result.reason:
            print(f"🚫 {manual_result.reason}")
            return False

        # Strategy 2: Transactional Detection (includes reply/forward exclusion)
        transactional_result = ReceiptDetector._transactional_strategy.detect(
            email, session
        )
        if transactional_result.is_match:
            masked = ReceiptDetector._mask_text(subject)
            print(f"✅ {transactional_result.reason}: {masked}")
            return True
        elif (
            transactional_result.reason
            and "Reply or forward" in transactional_result.reason
        ):
            masked = ReceiptDetector._mask_text(subject)
            print(f"🚫 {transactional_result.reason}: {masked}")
            return False

        # Strategy 3: Promotional Detection (exclusion)
        promotional_result = ReceiptDetector._promotional_strategy.detect(
            email, session
        )
        if promotional_result.is_match:
            masked = ReceiptDetector._mask_text(subject)
            print(f"🚫 Excluded promotional email: {masked}")
            return False

        # Strategy 4: Shipping Detection (exclusion)
        shipping_result = ReceiptDetector._shipping_strategy.detect(email, session)
        if shipping_result.is_match:
            masked = ReceiptDetector._mask_text(subject)
            print(f"🚫 Excluded shipping notification: {masked}")
            return False

        print(f"❌ Not a receipt: {ReceiptDetector._mask_text(subject)}")
        return False

    @staticmethod
    def debug_is_receipt(email: Any, session: Any = None) -> Dict[str, Any]:
        """
        Detailed trace of the logic for debugging or history analysis.
        """
        subject = (
            getattr(email, "subject", None) or email.get("subject", "") or ""
        ).lower()
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
    def _mask_text(text: str, max_chars: int = 20) -> str:
        """Helper to mask sensitive text for safe logging.

        This implementation deliberately avoids including any part of the original
        text in the log output to prevent leaking sensitive information. Only the
        length of the text is exposed.
        """
        if not text:
            return ""
        length = len(text)
        return f"*** (masked, {length} chars)"

    @staticmethod
    def _check_manual_rules(
        subject: str, sender: str, session: Any
    ) -> Optional[ManualRule]:
        """
        Helper to check if any manual rule matches.
        Delegates to ManualRuleStrategy for consistency.
        """
        # Reuse the singleton strategy instance to avoid redundant setup.
        strategy = ReceiptDetector._manual_rule_strategy
        # Directly delegate to the strategy's manual rule check, which returns
        # the matched ManualRule instance (or None) without duplicating work.
        return strategy._check_manual_rules(subject, sender, session)

    @staticmethod
    def is_reply_or_forward(subject: str, sender: str) -> bool:
        """
        Check if email is a reply or forward.
        Delegates to TransactionalStrategy for consistency.
        """
        strategy = ReceiptDetector._transactional_strategy
        return strategy._is_reply_or_forward(subject, sender)

    @staticmethod
    def is_shipping_notification(subject: str, body: str, sender: str) -> bool:
        """
        Check if email is a shipping notification.
        Delegates to ShippingStrategy for consistency.
        """
        strategy = ShippingStrategy()
        email = {"subject": subject, "body": body, "sender": sender}
        result = strategy.detect(email)
        return result.is_match

    @staticmethod
    def is_promotional_email(subject: str, body: str, sender: str) -> bool:
        """
        Check if email is promotional.
        Delegates to PromotionalStrategy for consistency.
        """
        strategy = PromotionalStrategy()
        email = {"subject": subject, "body": body, "sender": sender}
        result = strategy.detect(email)
        return result.is_match

    @staticmethod
    def has_strong_receipt_indicators(subject: str, body: str) -> bool:
        """
        Check for strong receipt indicators.
        Delegates to TransactionalStrategy for consistency.
        """
        strategy = TransactionalStrategy()
        return strategy._has_strong_receipt_indicators(subject, body)

    @staticmethod
    def calculate_transactional_score(subject: str, body: str, sender: str) -> int:
        """
        Calculate transactional score.
        Delegates to TransactionalStrategy for consistency.
        """
        strategy = TransactionalStrategy()
        return strategy._calculate_transactional_score(subject, body, sender)

    @staticmethod
    def is_known_receipt_sender(sender: str) -> bool:
        """
        Check if sender is a known receipt provider.
        Delegates to TransactionalStrategy for consistency.
        """
        strategy = TransactionalStrategy()
        return strategy._is_known_receipt_sender(sender)

    @staticmethod
    def has_transaction_confirmation(subject: str, body: str) -> bool:
        """
        Check for transaction confirmation patterns.
        Delegates to TransactionalStrategy for consistency.
        """
        strategy = TransactionalStrategy()
        return strategy._has_transaction_confirmation(subject, body)

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
