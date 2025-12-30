"""
Smart Categorization Service

This module provides rule-based categorization for emails using the CategoryRule model.
It supports pattern matching on sender and subject fields with wildcard support.
"""

import fnmatch
from typing import Any, Optional

from sqlmodel import Session, select

from ..models import CategoryRule, ProcessedEmail


class Categorizer:
    @staticmethod
    def predict_category(
        email: Any, session: Optional[Session] = None
    ) -> str:
        """
        Predict the category for an email based on CategoryRule patterns.

        Args:
            email: Email data (can be dict or object with sender/subject attributes)
            session: Database session for querying CategoryRule table

        Returns:
            Category string (e.g., "Travel", "Food", "Shopping")
            Returns "other" if no rules match
        """
        if not session:
            return "other"

        # Extract email attributes (support both dict and object)
        subject = (
            getattr(email, "subject", None) or email.get("subject", "") or ""
        ).lower()
        sender = (
            getattr(email, "sender", None)
            or getattr(email, "from", None)
            or email.get("sender", "")
            or email.get("from", "")
            or ""
        ).lower()

        # Get all category rules ordered by priority (highest first)
        rules = session.exec(
            select(CategoryRule).order_by(CategoryRule.priority.desc())  # type: ignore
        ).all()

        # Apply first matching rule
        for rule in rules:
            matches = False

            if rule.match_type == "sender":
                # Match pattern against sender using fnmatch (supports wildcards)
                if fnmatch.fnmatch(sender, rule.pattern.lower()):
                    matches = True

            elif rule.match_type == "subject":
                # Match pattern against subject using fnmatch (supports wildcards)
                if fnmatch.fnmatch(subject, rule.pattern.lower()):
                    matches = True

            if matches:
                print(f"✅ Category rule matched: {rule.assigned_category} (pattern: {rule.pattern})")
                return rule.assigned_category

        # No rules matched, return default
        return "other"

    @staticmethod
    def get_fallback_category(email: Any) -> str:
        """
        Fallback categorization logic based on hardcoded sender patterns.
        This is used when no CategoryRule matches or as a default.

        Args:
            email: Email data (can be dict or object)

        Returns:
            Category string based on hardcoded patterns
        """
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

        # Transportation
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
