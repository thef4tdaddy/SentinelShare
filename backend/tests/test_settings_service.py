"""Unit tests for SettingsService."""

import pytest
from sqlmodel import Session, SQLModel, select

from backend.constants import DEFAULT_EMAIL_TEMPLATE
from backend.database import engine
from backend.models import CategoryRule, GlobalSettings
from backend.services.settings_service import SettingsService


@pytest.fixture(name="session")
def session_fixture():
    """Create an in-memory database session for testing."""
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    SQLModel.metadata.drop_all(engine)


class TestSettingsServiceEmailTemplate:
    """Test email template management."""

    def test_get_email_template_default(self, session):
        """Test getting default email template."""
        template = SettingsService.get_email_template(session)

        assert template == DEFAULT_EMAIL_TEMPLATE

    def test_get_email_template_custom(self, session):
        """Test getting custom email template."""
        custom_template = "<html><body>Custom template</body></html>"
        setting = GlobalSettings(
            key="email_template",
            value=custom_template,
            description="Custom template",
        )
        session.add(setting)
        session.commit()

        template = SettingsService.get_email_template(session)

        assert template == custom_template

    def test_update_email_template_new(self, session):
        """Test creating new email template."""
        new_template = "<html><body>New template</body></html>"

        result = SettingsService.update_email_template(new_template, session)

        assert result["template"] == new_template
        assert "updated successfully" in result["message"]

        # Verify stored in database
        setting = session.exec(
            select(GlobalSettings).where(GlobalSettings.key == "email_template")
        ).first()
        assert setting is not None
        assert setting.value == new_template

    def test_update_email_template_existing(self, session):
        """Test updating existing email template."""
        # Create existing template
        session.add(
            GlobalSettings(
                key="email_template",
                value="Old template",
                description="Template",
            )
        )
        session.commit()

        new_template = "Updated template"
        result = SettingsService.update_email_template(new_template, session)

        assert result["template"] == new_template

        # Verify only one template exists
        settings = session.exec(
            select(GlobalSettings).where(GlobalSettings.key == "email_template")
        ).all()
        assert len(settings) == 1

    def test_update_email_template_empty(self, session):
        """Test updating with empty template raises error."""
        with pytest.raises(ValueError, match="cannot be empty"):
            SettingsService.update_email_template("", session)

        with pytest.raises(ValueError, match="cannot be empty"):
            SettingsService.update_email_template("   ", session)

    def test_update_email_template_too_long(self, session):
        """Test updating with too long template raises error."""
        long_template = "x" * 10001

        with pytest.raises(ValueError, match="too long"):
            SettingsService.update_email_template(long_template, session)


class TestSettingsServiceCategoryRuleValidation:
    """Test category rule validation."""

    def test_validate_category_rule_valid(self):
        """Test validation with valid data."""
        # Should not raise exception
        SettingsService.validate_category_rule(
            match_type="sender",
            pattern="*@example.com",
            assigned_category="Shopping",
            priority=50,
        )

    def test_validate_category_rule_invalid_match_type(self):
        """Test validation with invalid match_type."""
        with pytest.raises(ValueError, match="must be either 'sender' or 'subject'"):
            SettingsService.validate_category_rule(
                match_type="invalid",
                pattern="*@example.com",
                assigned_category="Shopping",
                priority=50,
            )

    def test_validate_category_rule_empty_pattern(self):
        """Test validation with empty pattern."""
        with pytest.raises(ValueError, match="pattern cannot be empty"):
            SettingsService.validate_category_rule(
                match_type="sender",
                pattern="",
                assigned_category="Shopping",
                priority=50,
            )

        with pytest.raises(ValueError, match="pattern cannot be empty"):
            SettingsService.validate_category_rule(
                match_type="sender",
                pattern="   ",
                assigned_category="Shopping",
                priority=50,
            )

    def test_validate_category_rule_empty_category(self):
        """Test validation with empty category."""
        with pytest.raises(ValueError, match="assigned_category cannot be empty"):
            SettingsService.validate_category_rule(
                match_type="sender",
                pattern="*@example.com",
                assigned_category="",
                priority=50,
            )

    def test_validate_category_rule_invalid_priority(self):
        """Test validation with invalid priority."""
        with pytest.raises(ValueError, match="priority must be between 1 and 100"):
            SettingsService.validate_category_rule(
                match_type="sender",
                pattern="*@example.com",
                assigned_category="Shopping",
                priority=0,
            )

        with pytest.raises(ValueError, match="priority must be between 1 and 100"):
            SettingsService.validate_category_rule(
                match_type="sender",
                pattern="*@example.com",
                assigned_category="Shopping",
                priority=101,
            )


class TestSettingsServiceCreateCategoryRule:
    """Test category rule creation."""

    def test_create_category_rule_success(self, session):
        """Test successful category rule creation."""
        rule = SettingsService.create_category_rule(
            match_type="sender",
            pattern="*@amazon.com",
            assigned_category="Shopping",
            priority=80,
            session=session,
        )

        assert rule.id is not None
        assert rule.match_type == "sender"
        assert rule.pattern == "*@amazon.com"
        assert rule.assigned_category == "Shopping"
        assert rule.priority == 80

        # Verify stored in database
        db_rule = session.get(CategoryRule, rule.id)
        assert db_rule is not None

    def test_create_category_rule_with_validation_error(self, session):
        """Test creation with invalid data."""
        with pytest.raises(ValueError, match="must be either"):
            SettingsService.create_category_rule(
                match_type="invalid",
                pattern="*@example.com",
                assigned_category="Shopping",
                priority=50,
                session=session,
            )


class TestSettingsServiceUpdateCategoryRule:
    """Test category rule updates."""

    def test_update_category_rule_success(self, session):
        """Test successful category rule update."""
        # Create initial rule
        rule = CategoryRule(
            match_type="sender",
            pattern="*@old.com",
            assigned_category="Old Category",
            priority=50,
        )
        session.add(rule)
        session.commit()

        # Update rule
        updated_rule = SettingsService.update_category_rule(
            rule_id=rule.id,
            match_type="subject",
            pattern="*receipt*",
            assigned_category="New Category",
            priority=75,
            session=session,
        )

        assert updated_rule.match_type == "subject"
        assert updated_rule.pattern == "*receipt*"
        assert updated_rule.assigned_category == "New Category"
        assert updated_rule.priority == 75

        # Verify changes persisted
        session.refresh(rule)
        assert rule.match_type == "subject"

    def test_update_category_rule_not_found(self, session):
        """Test updating non-existent rule."""
        with pytest.raises(ValueError, match="Category rule not found"):
            SettingsService.update_category_rule(
                rule_id=999,
                match_type="sender",
                pattern="*@example.com",
                assigned_category="Shopping",
                priority=50,
                session=session,
            )

    def test_update_category_rule_with_validation_error(self, session):
        """Test update with invalid data."""
        # Create initial rule
        rule = CategoryRule(
            match_type="sender",
            pattern="*@example.com",
            assigned_category="Shopping",
            priority=50,
        )
        session.add(rule)
        session.commit()

        # Try to update with invalid priority
        with pytest.raises(ValueError, match="priority must be between"):
            SettingsService.update_category_rule(
                rule_id=rule.id,
                match_type="sender",
                pattern="*@example.com",
                assigned_category="Shopping",
                priority=150,
                session=session,
            )


class TestSettingsServiceIntegration:
    """Integration tests for settings service."""

    def test_multiple_templates_not_created(self, session):
        """Test that updating template doesn't create duplicates."""
        # Create first template
        SettingsService.update_email_template("Template 1", session)

        # Update to second template
        SettingsService.update_email_template("Template 2", session)

        # Update to third template
        SettingsService.update_email_template("Template 3", session)

        # Verify only one template exists
        templates = session.exec(
            select(GlobalSettings).where(GlobalSettings.key == "email_template")
        ).all()
        assert len(templates) == 1
        assert templates[0].value == "Template 3"

    def test_category_rule_lifecycle(self, session):
        """Test complete lifecycle of category rule."""
        # Create
        rule = SettingsService.create_category_rule(
            match_type="sender",
            pattern="*@store.com",
            assigned_category="Retail",
            priority=60,
            session=session,
        )

        # Update
        SettingsService.update_category_rule(
            rule_id=rule.id,
            match_type="sender",
            pattern="*@shop.com",
            assigned_category="Shopping",
            priority=70,
            session=session,
        )

        # Verify final state
        final_rule = session.get(CategoryRule, rule.id)
        assert final_rule is not None
        assert final_rule.pattern == "*@shop.com"
        assert final_rule.assigned_category == "Shopping"
        assert final_rule.priority == 70
