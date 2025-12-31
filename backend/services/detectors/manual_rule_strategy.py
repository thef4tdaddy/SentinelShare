"""Manual rule-based detection strategy."""

import fnmatch
from typing import Any, Optional

from sqlmodel import col, select

from ...models import ManualRule, Preference
from .base import DetectionResult, DetectionStrategy


class ManualRuleStrategy(DetectionStrategy):
    """Check database manual rules and preferences."""

    def detect(self, email: Any, session: Any = None) -> DetectionResult:
        """Check manual rules and preferences against the email."""
        if not session:
            return DetectionResult(is_match=False)

        subject, _, sender = self._extract_email_fields(email)

        try:
            # 1. Manual Rules (Priority ordering)
            matched_rule = self._check_manual_rules(subject, sender, session)
            if matched_rule:
                return DetectionResult(
                    is_match=True,
                    confidence=100,
                    reason=f"Manual rule match: {matched_rule.purpose or 'No purpose'}",
                    matched_by="Manual Rule",
                )

            # 2. Preferences (Always Forward)
            always_forward = session.exec(
                select(Preference).where(Preference.type == "Always Forward")
            ).all()
            for pref in always_forward:
                p_item = pref.item.lower()
                if p_item in sender or p_item in subject:
                    masked = self._mask_text(pref.item)
                    return DetectionResult(
                        is_match=True,
                        confidence=100,
                        reason=f"Preference match (Always Forward): {masked}",
                        matched_by="Always Forward Preference",
                    )

            # 3. Preferences (Blocked Sender / Category)
            blocked = session.exec(
                select(Preference).where(
                    col(Preference.type).in_(["Blocked Sender", "Blocked Category"])
                )
            ).all()
            for pref in blocked:
                p_item = pref.item.lower()
                if p_item in sender or p_item in subject:
                    masked = self._mask_text(pref.item)
                    return DetectionResult(
                        is_match=False,
                        confidence=100,
                        reason=f"Preference match (Blocked): {masked}",
                        matched_by="Blocked Preference",
                    )

        except Exception as e:
            print(f"⚠️ Error checking database rules: {type(e).__name__}")

        return DetectionResult(is_match=False)

    def _check_manual_rules(
        self, subject: str, sender: str, session: Any
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
