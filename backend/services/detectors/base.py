"""Base class for detection strategies."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class DetectionResult:
    """Result of a detection strategy."""

    is_match: bool
    confidence: int = 0  # 0-100
    reason: Optional[str] = None
    matched_by: Optional[str] = None


class DetectionStrategy(ABC):
    """Base class for email detection strategies."""

    @abstractmethod
    def detect(self, email: Any, session: Any = None) -> DetectionResult:
        """
        Analyze an email and return detection result.

        Args:
            email: Email object with subject, body, sender attributes
            session: Optional database session for rule checking

        Returns:
            DetectionResult with match status and metadata
        """
        pass

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
    def _extract_email_fields(email: Any) -> tuple[str, str, str]:
        """Extract subject, body, and sender from email object."""
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
        return subject, body, sender
