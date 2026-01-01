"""Service for managing user preferences (blocked/allowed senders and categories)."""

from typing import Dict, List

from sqlmodel import Session, col, select

from backend.models import Preference


class PreferenceService:
    """Service for handling preference operations."""

    @staticmethod
    def get_preferences_by_types(
        session: Session, types: List[str]
    ) -> List[Preference]:
        """
        Get preferences filtered by type.

        Args:
            session: Database session
            types: List of preference types to filter by

        Returns:
            List of matching preferences
        """
        return list(
            session.exec(
                select(Preference).where(col(Preference.type).in_(types))
            ).all()
        )

    @staticmethod
    def get_preferences_dict(session: Session) -> Dict[str, List[str]]:
        """
        Get preferences organized by category.

        Args:
            session: Database session

        Returns:
            Dictionary with 'blocked' and 'allowed' keys containing preference items
        """
        prefs = PreferenceService.get_preferences_by_types(
            session, ["Blocked Sender", "Always Forward"]
        )

        return {
            "blocked": [p.item for p in prefs if p.type == "Blocked Sender"],
            "allowed": [p.item for p in prefs if p.type == "Always Forward"],
        }

    @staticmethod
    def validate_preferences(
        blocked_senders: List[str], allowed_senders: List[str]
    ) -> None:
        """
        Validate preference inputs.

        Args:
            blocked_senders: List of senders to block
            allowed_senders: List of senders to allow

        Raises:
            ValueError: If validation fails
        """
        # Check for duplicates within each list
        if len(blocked_senders) != len(set(blocked_senders)):
            raise ValueError("Duplicate entries found in blocked senders")

        if len(allowed_senders) != len(set(allowed_senders)):
            raise ValueError("Duplicate entries found in allowed senders")

        # Check for overlap between blocked and allowed
        overlap = set(blocked_senders) & set(allowed_senders)
        if overlap:
            raise ValueError(
                f"Cannot have same item in both blocked and allowed: {overlap}"
            )
