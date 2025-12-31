"""Promotional email detection strategy."""

import re
from typing import Any

from .base import DetectionResult, DetectionStrategy


class PromotionalStrategy(DetectionStrategy):
    """Detect promotional and marketing emails."""

    # Promotional patterns
    PROMOTIONAL_KEYWORDS = [
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

    MARKETING_PATTERNS = [
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

    TRACKING_PATTERNS = [
        r"awstrack\.me",
        r"click\.",
        r"track\.",
        r"utm_",
        r"newsletter",
        r"unsubscribe",
    ]

    DEALS_PATTERNS = [
        r"deals?\s*net",
        r"deals?\s*com",
        r"bargain",
        r"slickdeals",
        r"reddit.*deals",
        r"steam.*sale",
        r"game.*deals",
    ]

    # Allowlist for receipt-like promotional emails
    PROMO_ALLOWLIST_PATTERNS = [
        "xbox",
        "game pass",
        "subscription renewal",
        "renewal receipt",
    ]

    def detect(self, email: Any, session: Any = None) -> DetectionResult:
        """Detect if email is promotional."""
        subject, body, sender = self._extract_email_fields(email)

        # Whitelist specific phrases that might look promotional but are receipts
        text = f"{subject} {body}"
        if "subscribe & save" in text or "subscription order" in text:
            return DetectionResult(is_match=False)

        # Exempt government-related senders
        if any(gov in sender for gov in ["irs", "dmv", "gov"]):
            return DetectionResult(is_match=False)

        # Check promotional keywords
        if any(keyword in subject for keyword in self.PROMOTIONAL_KEYWORDS):
            # Check if it's on the allowlist
            if any(
                pattern in subject or pattern in body or pattern in sender
                for pattern in self.PROMO_ALLOWLIST_PATTERNS
            ):
                return DetectionResult(is_match=False)
            return DetectionResult(
                is_match=True,
                confidence=90,
                reason="Promotional keyword in subject",
                matched_by="Promotional Strategy",
            )

        if any(keyword in body for keyword in self.PROMOTIONAL_KEYWORDS):
            if any(
                pattern in subject or pattern in body or pattern in sender
                for pattern in self.PROMO_ALLOWLIST_PATTERNS
            ):
                return DetectionResult(is_match=False)
            return DetectionResult(
                is_match=True,
                confidence=80,
                reason="Promotional keyword in body",
                matched_by="Promotional Strategy",
            )

        # Check marketing patterns
        if any(
            re.search(pattern, subject, re.IGNORECASE)
            or re.search(pattern, body, re.IGNORECASE)
            for pattern in self.MARKETING_PATTERNS
        ):
            if any(
                pattern in subject or pattern in body or pattern in sender
                for pattern in self.PROMO_ALLOWLIST_PATTERNS
            ):
                return DetectionResult(is_match=False)
            return DetectionResult(
                is_match=True,
                confidence=85,
                reason="Marketing pattern detected",
                matched_by="Promotional Strategy",
            )

        # Check tracking patterns
        if any(re.search(pattern, body, re.IGNORECASE) for pattern in self.TRACKING_PATTERNS):
            return DetectionResult(
                is_match=True,
                confidence=70,
                reason="Tracking pattern in body",
                matched_by="Promotional Strategy",
            )

        # Check deals patterns
        if any(
            re.search(pattern, sender, re.IGNORECASE)
            or re.search(pattern, subject, re.IGNORECASE)
            or re.search(pattern, body, re.IGNORECASE)
            for pattern in self.DEALS_PATTERNS
        ):
            return DetectionResult(
                is_match=True,
                confidence=90,
                reason="Deal site pattern detected",
                matched_by="Promotional Strategy",
            )

        return DetectionResult(is_match=False)
