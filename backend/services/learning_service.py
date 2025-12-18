import fnmatch
import os
import re
from typing import Any, Dict, Optional

from backend.models import ManualRule, ProcessedEmail
from sqlmodel import Session, select


class LearningService:
    """
    Analyzes historical 'blocked' or 'ignored' emails that the user marked as 'should have been a receipt'.
    Generates new ManualRule suggestions based on common patterns.
    """

    @staticmethod
    def generate_rule_from_email(email: ProcessedEmail) -> Optional[Dict[str, Any]]:
        """
        Creates a suggested ManualRule based on a single email's properties.
        Focuses on domain-level and subject keyword patterns.
        """
        sender = email.sender.lower()
        subject = email.subject.lower()

        # 1. Extract domain
        domain_match = re.search(r"@([\w.-]+)", sender)
        domain = domain_match.group(1) if domain_match else sender

        # 2. Extract common keywords from subject (excluding common noise)
        noise = {
            "re:",
            "fwd:",
            "the",
            "and",
            "your",
            "order",
            "confirmation",
            "receipt",
        }
        keywords = [
            word
            for word in re.findall(r"\w+", subject)
            if word not in noise and len(word) > 3
        ]

        # 3. Suggest a rule
        # If it's a clear store domain, suggest an email pattern
        suggested_rule = {
            "email_pattern": f"*@{domain}",
            "subject_pattern": None,
            "purpose": f"Learned from {email.sender}",
            "confidence": 0.7,  # Initial confidence
        }

        # If the subject has very specific keywords, suggest a subject pattern too
        if keywords:
            # Take the most unique keyword or first two
            suggested_rule["subject_pattern"] = f"*{keywords[0]}*"
            suggested_rule["confidence"] += 0.1

        return suggested_rule

    @staticmethod
    def run_shadow_mode(session: Session, email_data: Dict[str, Any]):
        """
        Tests 'shadow mode' rules against an email.
        If a rule matches, increment its match_count and confidence.
        """
        subject = email_data.get("subject", "").lower()
        sender = email_data.get("from", "").lower()

        shadow_rules = session.exec(
            select(ManualRule).where(ManualRule.is_shadow_mode == True)
        ).all()

        for rule in shadow_rules:
            matches = True
            if rule.email_pattern and not fnmatch.fnmatch(
                sender, rule.email_pattern.lower()
            ):
                matches = False
            if (
                matches
                and rule.subject_pattern
                and not fnmatch.fnmatch(subject, rule.subject_pattern.lower())
            ):
                matches = False

            if matches:
                rule.match_count += 1
                # Slowly increase confidence with each successful match
                rule.confidence = min(1.0, rule.confidence + 0.05)
                session.add(rule)

        session.commit()

    @staticmethod
    def auto_promote_rules(session: Session):
        """
        Promote shadow rules to active ManualRule status if they hit 0.9 confidence and 3 matches.
        """
        auto_promote_confidence = float(
            os.getenv("AUTO_PROMOTE_CONFIDENCE_THRESHOLD", "0.9")
        )
        auto_promote_matches = int(os.getenv("AUTO_PROMOTE_MATCH_COUNT_THRESHOLD", "3"))

        candidates = session.exec(
            select(ManualRule)
            .where(ManualRule.is_shadow_mode == True)
            .where(ManualRule.confidence >= auto_promote_confidence)
            .where(ManualRule.match_count >= auto_promote_matches)
        ).all()

        for rule in candidates:
            rule.is_shadow_mode = False
            rule.purpose = f"(AUTO) {rule.purpose}"
            session.add(rule)
            print(
                f"🚀 Auto-promoted rule: {rule.email_pattern} | {rule.subject_pattern}"
            )

        session.commit()
