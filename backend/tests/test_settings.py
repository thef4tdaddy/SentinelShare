import pytest
from backend.models import ManualRule, Preference
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool


@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def test_get_rules_empty(session: Session):
    from backend.routers.settings import get_rules

    rules = get_rules(session=session)
    assert len(rules) == 0


def test_create_and_get_rule(session: Session):
    from backend.routers.settings import create_rule, get_rules

    rule_data = ManualRule(
        email_pattern="*@test.com", purpose="Test Rule", confidence=1.0
    )
    created = create_rule(rule_data, session=session)
    assert created.id is not None

    rules = get_rules(session=session)
    assert len(rules) == 1
    assert rules[0].email_pattern == "*@test.com"


def test_delete_rule(session: Session):
    from backend.routers.settings import create_rule, delete_rule, get_rules

    rule = ManualRule(email_pattern="*@delete.me", purpose="Delete", confidence=0.5)
    created = create_rule(rule, session=session)

    delete_rule(created.id, session=session)
    rules = get_rules(session=session)
    assert len(rules) == 0


def test_get_preferences_default(session: Session):
    from backend.routers.settings import get_preferences

    prefs = get_preferences(session=session)
    # Should have some default preferences if implemented, or empty list
    assert isinstance(prefs, list)


def test_update_preference(session: Session):
    from backend.routers.settings import create_preference, get_preferences

    # Create a preference first
    pref = Preference(item="amazon", type="Blocked Category")
    create_preference(pref, session=session)

    # Verify it exists
    prefs = get_preferences(session=session)
    assert len(prefs) == 1
    assert prefs[0].item == "amazon"


def test_email_template_endpoints(session: Session):
    from backend.routers.settings import (EmailTemplateUpdate,
                                          get_email_template,
                                          update_email_template)

    # Default template
    tpl = get_email_template(session=session)
    assert "template" in tpl

    # Update template
    update_email_template(
        EmailTemplateUpdate(template="New template content"), session=session
    )

    # Verify
    updated_tpl = get_email_template(session=session)
    assert updated_tpl["template"] == "New template content"


def test_connectivity_endpoint():
    from backend.routers.settings import test_connections

    result = test_connections()
    assert isinstance(result, list)
    if len(result) > 0:
        assert "account" in result[0]
        assert "success" in result[0]


def test_trigger_poll(session: Session):
    from unittest.mock import MagicMock

    from backend.routers.settings import trigger_poll

    bg_tasks = MagicMock()
    result = trigger_poll(bg_tasks, session=session)
    assert result["status"] == "triggered"
    bg_tasks.add_task.assert_called_once()


def test_delete_preference_success(session: Session):
    """Test successfully deleting a preference (lines 33-35)"""
    from backend.routers.settings import (create_preference, delete_preference,
                                          get_preferences)

    # Create a preference first
    pref = Preference(item="test_delete", type="Blocked Category")
    created = create_preference(pref, session=session)

    # Delete it
    result = delete_preference(created.id, session=session)
    assert result["ok"] is True

    # Verify it's gone
    prefs = get_preferences(session=session)
    assert len(prefs) == 0


def test_delete_preference_not_found(session: Session):
    """Test deleting a non-existent preference raises 404"""
    from backend.routers.settings import delete_preference
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc_info:
        delete_preference(999, session=session)
    assert exc_info.value.status_code == 404
    assert "Preference not found" in str(exc_info.value.detail)


def test_delete_rule_not_found(session: Session):
    """Test deleting a non-existent rule raises 404"""
    from backend.routers.settings import delete_rule
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc_info:
        delete_rule(999, session=session)
    assert exc_info.value.status_code == 404
    assert "Rule not found" in str(exc_info.value.detail)


def test_update_email_template_empty(session: Session):
    """Test updating email template with empty string raises 400"""
    from backend.routers.settings import (EmailTemplateUpdate,
                                          update_email_template)
    from fastapi import HTTPException

    # Test with empty string
    with pytest.raises(HTTPException) as exc_info:
        update_email_template(EmailTemplateUpdate(template=""), session=session)
    assert exc_info.value.status_code == 400
    assert "Template cannot be empty" in str(exc_info.value.detail)

    # Test with whitespace only
    with pytest.raises(HTTPException) as exc_info:
        update_email_template(EmailTemplateUpdate(template="   "), session=session)
    assert exc_info.value.status_code == 400
    assert "Template cannot be empty" in str(exc_info.value.detail)


def test_update_email_template_too_long(session: Session):
    """Test updating email template with too long content raises 400"""
    from backend.routers.settings import (EmailTemplateUpdate,
                                          update_email_template)
    from fastapi import HTTPException

    # Create a template longer than 10,000 characters
    long_template = "x" * 10001

    with pytest.raises(HTTPException) as exc_info:
        update_email_template(
            EmailTemplateUpdate(template=long_template), session=session
        )
    assert exc_info.value.status_code == 400
    assert "Template too long" in str(exc_info.value.detail)


def test_update_email_template_create_new(session: Session):
    """Test creating a new email template setting (lines 110-115)"""
    from backend.routers.settings import (EmailTemplateUpdate,
                                          update_email_template)

    # First time creating the template - should hit the else branch on lines 110-115
    result = update_email_template(
        EmailTemplateUpdate(template="Brand new template"), session=session
    )

    assert result["template"] == "Brand new template"
    assert "message" in result
    assert result["message"] == "Template updated successfully"


def test_update_email_template_existing(session: Session):
    """Test updating an existing email template setting (line 108)"""
    from backend.routers.settings import (EmailTemplateUpdate,
                                          get_email_template,
                                          update_email_template)

    # First, create a template
    update_email_template(
        EmailTemplateUpdate(template="Initial template"), session=session
    )

    # Now update it - should hit line 108 (setting.value = data.template)
    result = update_email_template(
        EmailTemplateUpdate(template="Updated template"), session=session
    )

    assert result["template"] == "Updated template"
    assert result["message"] == "Template updated successfully"

    # Verify it was actually updated
    current = get_email_template(session=session)
    assert current["template"] == "Updated template"


# Email Account Management Tests


def test_get_email_accounts_empty(session: Session):
    """Test getting email accounts when none exist"""
    from backend.routers.settings import get_email_accounts

    accounts = get_email_accounts(session=session)
    assert len(accounts) == 0


def test_create_email_account(session: Session, monkeypatch):
    """Test creating a new email account"""
    from backend.routers.settings import EmailAccountCreate, create_email_account

    monkeypatch.setenv("SECRET_KEY", "test-secret-key")

    account_data = EmailAccountCreate(
        email="test@example.com",
        host="imap.gmail.com",
        port=993,
        username="test@example.com",
        password="test-password-123",
    )

    result = create_email_account(account_data, session=session)

    assert result.email == "test@example.com"
    assert result.host == "imap.gmail.com"
    assert result.port == 993
    assert result.username == "test@example.com"
    assert result.is_active is True
    assert result.id is not None


def test_create_email_account_duplicate(session: Session, monkeypatch):
    """Test creating a duplicate email account raises 400"""
    from backend.routers.settings import (EmailAccountCreate,
                                          create_email_account)
    from fastapi import HTTPException

    monkeypatch.setenv("SECRET_KEY", "test-secret-key")

    account_data = EmailAccountCreate(
        email="duplicate@example.com",
        host="imap.gmail.com",
        port=993,
        username="duplicate@example.com",
        password="password1",
    )

    # Create first account
    create_email_account(account_data, session=session)

    # Try to create duplicate
    with pytest.raises(HTTPException) as exc_info:
        create_email_account(account_data, session=session)

    assert exc_info.value.status_code == 400
    assert "already exists" in str(exc_info.value.detail)


def test_delete_email_account(session: Session, monkeypatch):
    """Test deleting an email account"""
    from backend.routers.settings import (EmailAccountCreate,
                                          create_email_account,
                                          delete_email_account,
                                          get_email_accounts)

    monkeypatch.setenv("SECRET_KEY", "test-secret-key")

    # Create an account
    account_data = EmailAccountCreate(
        email="delete@example.com",
        username="delete@example.com",
        password="password",
    )
    created = create_email_account(account_data, session=session)

    # Delete it
    result = delete_email_account(created.id, session=session)
    assert result["ok"] is True

    # Verify it's gone
    accounts = get_email_accounts(session=session)
    assert len(accounts) == 0


def test_delete_email_account_not_found(session: Session):
    """Test deleting a non-existent email account raises 404"""
    from backend.routers.settings import delete_email_account
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc_info:
        delete_email_account(999, session=session)

    assert exc_info.value.status_code == 404
    assert "Account not found" in str(exc_info.value.detail)


def test_test_email_account(session: Session, monkeypatch):
    """Test the test connection endpoint for email account"""
    from unittest.mock import patch

    from backend.routers.settings import (EmailAccountCreate,
                                          create_email_account,
                                          test_email_account)

    monkeypatch.setenv("SECRET_KEY", "test-secret-key")

    # Create an account
    account_data = EmailAccountCreate(
        email="test@example.com",
        username="test@example.com",
        password="password",
    )
    created = create_email_account(account_data, session=session)

    # Mock the EmailService.test_connection
    with patch("backend.routers.settings.EmailService.test_connection") as mock_test:
        mock_test.return_value = {"success": True, "error": None}

        result = test_email_account(created.id, session=session)

        assert result["account"] == "test@example.com"
        assert result["success"] is True
        assert result["error"] is None

        mock_test.assert_called_once()


def test_test_email_account_not_found(session: Session):
    """Test testing a non-existent email account raises 404"""
    from backend.routers.settings import test_email_account
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc_info:
        test_email_account(999, session=session)

    assert exc_info.value.status_code == 404
    assert "Account not found" in str(exc_info.value.detail)
