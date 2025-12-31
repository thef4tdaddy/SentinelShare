"""Service for managing application settings and configurations."""

from typing import Any, Dict

from sqlmodel import Session, select

from backend.constants import DEFAULT_EMAIL_TEMPLATE
from backend.models import CategoryRule, GlobalSettings


class SettingsService:
    """Service for managing application settings and configurations."""

    @staticmethod
    def get_email_template(session: Session) -> str:
        """Get the current email template."""
        setting = session.exec(
            select(GlobalSettings).where(GlobalSettings.key == "email_template")
        ).first()

        if setting:
            return setting.value
        else:
            # Return default template if not set
            return DEFAULT_EMAIL_TEMPLATE

    @staticmethod
    def update_email_template(template: str, session: Session) -> Dict[str, Any]:
        """Update the email template."""
        # Validate input
        if not template or not template.strip():
            raise ValueError("Template cannot be empty")
        if len(template) > 10000:
            raise ValueError("Template too long (max 10,000 characters)")

        setting = session.exec(
            select(GlobalSettings).where(GlobalSettings.key == "email_template")
        ).first()

        if setting:
            setting.value = template
        else:
            setting = GlobalSettings(
                key="email_template",
                value=template,
                description="Email template for forwarding receipts",
            )
            session.add(setting)

        session.commit()
        session.refresh(setting)
        return {"template": setting.value, "message": "Template updated successfully"}

    @staticmethod
    def validate_category_rule(
        match_type: str,
        pattern: str,
        assigned_category: str,
        priority: int,
    ) -> None:
        """Validate category rule parameters."""
        # Validate match_type
        if match_type not in ["sender", "subject"]:
            raise ValueError("match_type must be either 'sender' or 'subject'")

        # Validate pattern and category are not empty
        if not pattern or not pattern.strip():
            raise ValueError("pattern cannot be empty")

        if not assigned_category or not assigned_category.strip():
            raise ValueError("assigned_category cannot be empty")

        # Validate priority range
        if priority < 1 or priority > 100:
            raise ValueError("priority must be between 1 and 100")

    @staticmethod
    def create_category_rule(
        match_type: str,
        pattern: str,
        assigned_category: str,
        priority: int,
        session: Session,
    ) -> CategoryRule:
        """Create a new category rule."""
        # Validate inputs
        SettingsService.validate_category_rule(
            match_type, pattern, assigned_category, priority
        )

        rule = CategoryRule(
            match_type=match_type,
            pattern=pattern,
            assigned_category=assigned_category,
            priority=priority,
        )
        session.add(rule)
        session.commit()
        session.refresh(rule)
        return rule

    @staticmethod
    def update_category_rule(
        rule_id: int,
        match_type: str,
        pattern: str,
        assigned_category: str,
        priority: int,
        session: Session,
    ) -> CategoryRule:
        """Update an existing category rule."""
        rule = session.get(CategoryRule, rule_id)
        if not rule:
            raise ValueError("Category rule not found")

        # Validate inputs
        SettingsService.validate_category_rule(
            match_type, pattern, assigned_category, priority
        )

        rule.match_type = match_type
        rule.pattern = pattern
        rule.assigned_category = assigned_category
        rule.priority = priority

        session.add(rule)
        session.commit()
        session.refresh(rule)
        return rule
