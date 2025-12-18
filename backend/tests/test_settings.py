import pytest
from backend.main import app
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
