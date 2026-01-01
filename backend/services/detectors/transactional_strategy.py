"""Transactional email detection strategy."""

import os
import re
from typing import Any

from ..email_service import EmailService
from .base import DetectionResult, DetectionStrategy


class TransactionalStrategy(DetectionStrategy):
    """Detect transactional emails (receipts, invoices, orders)."""

    DEFINITIVE_PATTERNS = [
        r"payment\s+receipt",
        r"order\s+confirmation",
        r"purchase\s+confirmation",
        r"receipt\s+for\s+your\s+payment",
    ]

    STRONG_KEYWORDS = [
        "receipt",
        "invoice",
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

    STRONG_REGEX_PATTERNS = [
        r"order.*confirmation",
        r"payment.*confirmation",
        r"purchase.*confirmation",
    ]

    SUPPORTING_EVIDENCE = [
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

    TRANSACTION_INDICATORS = [
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

    KNOWN_RECEIPT_SENDERS = [
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

    CONFIRMATION_PATTERNS = [
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

    REPLY_PATTERNS = [
        r"re:\s*",
        r"fwd?:\s*",
        r"fw:\s*",
        r"forward:\s*",
        r"\[fwd\]",
        r"\(fwd\)",
    ]

    def detect(self, email: Any, session: Any = None) -> DetectionResult:
        """Detect if email is a transactional receipt."""
        subject, body, sender = self._extract_email_fields(email)

        # First check if it's a reply or forward (should be excluded)
        if self._is_reply_or_forward(subject, sender):
            return DetectionResult(
                is_match=False,
                confidence=100,
                reason="Reply or forward email",
                matched_by="Transactional Strategy",
            )

        # Check for strong receipt indicators (definitive + supporting evidence)
        if self._has_strong_receipt_indicators(subject, body):
            return DetectionResult(
                is_match=True,
                confidence=95,
                reason="Strong receipt indicators found",
                matched_by="Transactional Strategy",
            )

        # Calculate transactional score
        score = self._calculate_transactional_score(subject, body, sender)
        if score >= 3:
            return DetectionResult(
                is_match=True,
                confidence=min(score * 20, 100),
                reason=f"High transactional score ({score})",
                matched_by="Transactional Strategy",
            )

        # Known receipt sender with transaction confirmation
        if self._is_known_receipt_sender(sender) and self._has_transaction_confirmation(
            subject, body
        ):
            return DetectionResult(
                is_match=True,
                confidence=85,
                reason="Known sender with transaction confirmation",
                matched_by="Transactional Strategy",
            )

        return DetectionResult(is_match=False)

    def _is_reply_or_forward(self, subject: str, sender: str) -> bool:
        """Check if email is a reply or forward."""
        is_reply_pattern = any(
            re.match(pattern, subject, re.IGNORECASE) for pattern in self.REPLY_PATTERNS
        )
        if is_reply_pattern:
            return True

        # Check if from wife's email (if configured)
        wife_email = os.environ.get("WIFE_EMAIL")
        if wife_email and wife_email.lower() in sender:
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

    def _has_strong_receipt_indicators(self, subject: str, body: str) -> bool:
        """Check for definitive receipt patterns with supporting evidence."""
        # Check definitive patterns
        if any(re.search(p, subject, re.IGNORECASE) for p in self.DEFINITIVE_PATTERNS):
            return True

        # Check strong keywords
        has_keyword = any(
            keyword in subject or keyword in body for keyword in self.STRONG_KEYWORDS
        )

        # Check regex patterns
        text = f"{subject} {body}"
        has_regex = any(
            re.search(pattern, text, re.IGNORECASE)
            for pattern in self.STRONG_REGEX_PATTERNS
        )

        if not (has_keyword or has_regex):
            return False

        # Must have supporting evidence
        return any(
            re.search(pattern, text, re.IGNORECASE)
            for pattern in self.SUPPORTING_EVIDENCE
        )

    def _calculate_transactional_score(
        self, subject: str, body: str, sender: str
    ) -> int:
        """Calculate transactional score based on indicators."""
        score = 0
        text = f"{subject} {body} {sender}"

        for pattern, points in self.TRANSACTION_INDICATORS:
            if re.search(pattern, text, re.IGNORECASE):
                score += points

        return score

    def _is_known_receipt_sender(self, sender: str) -> bool:
        """Check if sender is a known receipt provider."""
        return any(s in sender for s in self.KNOWN_RECEIPT_SENDERS)

    def _has_transaction_confirmation(self, subject: str, body: str) -> bool:
        """Check for transaction confirmation patterns."""
        return any(
            re.search(pattern, subject, re.IGNORECASE)
            or re.search(pattern, body, re.IGNORECASE)
            for pattern in self.CONFIRMATION_PATTERNS
        )
