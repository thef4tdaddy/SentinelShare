import pytest
from backend.models import ManualRule, ProcessedEmail
from backend.services.learning_service import LearningService
from sqlmodel import Session, SQLModel, create_engine


@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def test_generate_rule_from_email():
    email = ProcessedEmail(
        sender="orders@amazon.com",
        subject="Your Amazon Order confirmation",
        email_id="msg1",
    )
    suggestion = LearningService.generate_rule_from_email(email)

    assert suggestion["email_pattern"] == "*@amazon.com"
    assert "amazon" in suggestion["purpose"]
    assert suggestion["confidence"] >= 0.7


def test_run_shadow_mode(session):
    # Setup a shadow rule
    rule = ManualRule(
        email_pattern="*@store.com", is_shadow_mode=True, confidence=0.5, match_count=0
    )
    session.add(rule)
    session.commit()

    # Simulate an email matching the shadow rule
    email_data = {"from": "support@store.com", "subject": "Thank you for visiting"}

    LearningService.run_shadow_mode(session, email_data)

    # Reload rule
    session.refresh(rule)
    assert rule.match_count == 1
    assert rule.confidence > 0.5


def test_auto_promotion(session):
    # Setup a rule ready for promotion
    rule = ManualRule(
        email_pattern="*@high-confidence.com",
        is_shadow_mode=True,
        confidence=0.95,
        match_count=5,
        purpose="Testing",
    )
    session.add(rule)
    session.commit()

    LearningService.auto_promote_rules(session)

    # Reload and check promotion
    session.refresh(rule)
    assert not rule.is_shadow_mode
    assert "(AUTO)" in rule.purpose


def test_run_shadow_mode_email_pattern_no_match(session):
    """Test that shadow rule doesn't match when email pattern doesn't match sender (line 83)."""
    # Setup a shadow rule with specific email pattern
    rule = ManualRule(
        email_pattern="*@store.com", is_shadow_mode=True, confidence=0.5, match_count=0
    )
    session.add(rule)
    session.commit()

    # Simulate an email that doesn't match the email pattern
    email_data = {"from": "support@different-store.com", "subject": "Thank you"}

    LearningService.run_shadow_mode(session, email_data)

    # Reload rule and verify it wasn't matched
    session.refresh(rule)
    assert rule.match_count == 0  # Should not increment
    assert rule.confidence == 0.5  # Should not change


def test_run_shadow_mode_subject_pattern_no_match(session):
    """Test that shadow rule doesn't match when subject pattern doesn't match (line 89)."""
    # Setup a shadow rule with both email and subject patterns
    rule = ManualRule(
        email_pattern="*@store.com",
        subject_pattern="*order*",
        is_shadow_mode=True,
        confidence=0.5,
        match_count=0,
    )
    session.add(rule)
    session.commit()

    # Simulate an email where email pattern matches but subject pattern doesn't
    email_data = {"from": "support@store.com", "subject": "Just a greeting"}

    LearningService.run_shadow_mode(session, email_data)

    # Reload rule and verify it wasn't matched
    session.refresh(rule)
    assert rule.match_count == 0  # Should not increment
    assert rule.confidence == 0.5  # Should not change
