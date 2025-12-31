"""Shipping notification detection strategy."""

import re
from typing import Any

from .base import DetectionResult, DetectionStrategy


class ShippingStrategy(DetectionStrategy):
    """Detect shipping and delivery notifications."""

    SHIPPING_EMAIL_PATTERNS = [
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

    SHIPPING_PATTERNS = [
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

    PURCHASE_INDICATORS = [
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

    def detect(self, email: Any, session: Any = None) -> DetectionResult:
        """Detect if email is a shipping notification (not a receipt)."""
        subject, body, sender = self._extract_email_fields(email)

        # Check sender patterns
        if any(
            re.search(pattern, sender, re.IGNORECASE)
            for pattern in self.SHIPPING_EMAIL_PATTERNS
        ):
            text = f"{subject} {body}"
            # If it has purchase indicators, it's a receipt, not just shipping
            has_purchase = any(
                re.search(pattern, text, re.IGNORECASE)
                for pattern in self.PURCHASE_INDICATORS
            )
            if not has_purchase:
                return DetectionResult(
                    is_match=True,
                    confidence=95,
                    reason="Shipping sender without purchase indicators",
                    matched_by="Shipping Strategy",
                )

        # Check shipping patterns in content
        text = f"{subject} {body}"
        has_shipping_pattern = any(
            re.search(pattern, text, re.IGNORECASE) for pattern in self.SHIPPING_PATTERNS
        )

        if not has_shipping_pattern:
            return DetectionResult(is_match=False)

        # Check if it also has purchase indicators
        has_purchase_indicators = any(
            re.search(pattern, text, re.IGNORECASE) for pattern in self.PURCHASE_INDICATORS
        )

        # It's shipping only if it has shipping patterns but NOT purchase indicators
        if has_shipping_pattern and not has_purchase_indicators:
            return DetectionResult(
                is_match=True,
                confidence=90,
                reason="Shipping pattern without purchase indicators",
                matched_by="Shipping Strategy",
            )

        return DetectionResult(is_match=False)
