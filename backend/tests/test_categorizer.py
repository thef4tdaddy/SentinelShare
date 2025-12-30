"""Tests for Smart Categorization Service"""

import pytest
from backend.models import CategoryRule
from backend.services.categorizer import Categorizer
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool


# Create in-memory SQLite database for testing
@pytest.fixture(name="session")
def session_fixture():
    """Create a test database session with proper table setup"""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


class MockEmail:
    def __init__(self, subject="", body="", sender=""):
        self.subject = subject
        self.body = body
        self.sender = sender


def test_predict_category_no_session():
    """Test that predict_category returns 'other' when no session is provided"""
    email = MockEmail(subject="Order from Uber", sender="receipts@uber.com")
    result = Categorizer.predict_category(email, session=None)
    assert result == "other"


def test_predict_category_no_rules(session):
    """Test that predict_category returns 'other' when no rules exist"""
    email = MockEmail(subject="Order Confirmation", sender="shop@example.com")
    result = Categorizer.predict_category(email, session)
    assert result == "other"


def test_predict_category_sender_match(session):
    """Test categorization with sender pattern match"""
    # Create a rule for Uber
    rule = CategoryRule(
        match_type="sender",
        pattern="*@uber.com",
        assigned_category="Travel",
        priority=10,
    )
    session.add(rule)
    session.commit()

    email = MockEmail(subject="Your Tuesday trip", sender="receipts@uber.com")
    result = Categorizer.predict_category(email, session)
    assert result == "Travel"


def test_predict_category_subject_match(session):
    """Test categorization with subject pattern match"""
    # Create a rule for AWS
    rule = CategoryRule(
        match_type="subject",
        pattern="*aws*invoice*",
        assigned_category="Cloud Services",
        priority=10,
    )
    session.add(rule)
    session.commit()

    email = MockEmail(
        subject="Your AWS Invoice for December", sender="billing@amazon.com"
    )
    result = Categorizer.predict_category(email, session)
    assert result == "Cloud Services"


def test_predict_category_priority_ordering(session):
    """Test that higher priority rules are matched first"""
    # Create lower priority rule
    rule1 = CategoryRule(
        match_type="sender",
        pattern="*@uber.com",
        assigned_category="Generic Transportation",
        priority=5,
    )
    # Create higher priority rule
    rule2 = CategoryRule(
        match_type="sender",
        pattern="*@uber.com",
        assigned_category="Rideshare",
        priority=15,
    )
    session.add(rule1)
    session.add(rule2)
    session.commit()

    email = MockEmail(subject="Your trip", sender="receipts@uber.com")
    result = Categorizer.predict_category(email, session)
    # Should match the higher priority rule
    assert result == "Rideshare"


def test_predict_category_multiple_rules(session):
    """Test that first matching rule wins"""
    rule1 = CategoryRule(
        match_type="sender", pattern="*@uber.com", assigned_category="Travel", priority=10
    )
    rule2 = CategoryRule(
        match_type="sender",
        pattern="*@doordash.com",
        assigned_category="Food",
        priority=10,
    )
    rule3 = CategoryRule(
        match_type="sender",
        pattern="*@amazon.com",
        assigned_category="Shopping",
        priority=10,
    )
    session.add_all([rule1, rule2, rule3])
    session.commit()

    # Test Uber match
    email1 = MockEmail(subject="Trip", sender="noreply@uber.com")
    assert Categorizer.predict_category(email1, session) == "Travel"

    # Test DoorDash match
    email2 = MockEmail(subject="Order", sender="support@doordash.com")
    assert Categorizer.predict_category(email2, session) == "Food"

    # Test Amazon match
    email3 = MockEmail(subject="Order", sender="auto-confirm@amazon.com")
    assert Categorizer.predict_category(email3, session) == "Shopping"


def test_predict_category_wildcard_patterns(session):
    """Test various wildcard patterns"""
    # Test exact match
    rule1 = CategoryRule(
        match_type="sender",
        pattern="receipts@uber.com",
        assigned_category="Uber Receipts",
        priority=10,
    )
    # Test wildcard at start
    rule2 = CategoryRule(
        match_type="sender",
        pattern="*@mcdonalds.com",
        assigned_category="Fast Food",
        priority=9,
    )
    # Test wildcard in middle
    rule3 = CategoryRule(
        match_type="subject",
        pattern="*order*confirmation*",
        assigned_category="Order Confirmed",
        priority=8,
    )
    session.add_all([rule1, rule2, rule3])
    session.commit()

    # Exact match
    email1 = MockEmail(subject="Receipt", sender="receipts@uber.com")
    assert Categorizer.predict_category(email1, session) == "Uber Receipts"

    # Wildcard at start
    email2 = MockEmail(subject="Receipt", sender="noreply@mcdonalds.com")
    assert Categorizer.predict_category(email2, session) == "Fast Food"

    # Wildcard in middle
    email3 = MockEmail(subject="Your order #123 confirmation", sender="shop@test.com")
    assert Categorizer.predict_category(email3, session) == "Order Confirmed"


def test_predict_category_case_insensitive(session):
    """Test that pattern matching is case-insensitive"""
    rule = CategoryRule(
        match_type="sender",
        pattern="*@UBER.COM",
        assigned_category="Travel",
        priority=10,
    )
    session.add(rule)
    session.commit()

    # Lowercase sender should match uppercase pattern
    email = MockEmail(subject="Trip", sender="receipts@uber.com")
    assert Categorizer.predict_category(email, session) == "Travel"


def test_predict_category_with_dict_email(session):
    """Test that predict_category works with dict-style email data"""
    rule = CategoryRule(
        match_type="sender",
        pattern="*@uber.com",
        assigned_category="Travel",
        priority=10,
    )
    session.add(rule)
    session.commit()

    email_dict = {"subject": "Your trip", "sender": "receipts@uber.com"}
    result = Categorizer.predict_category(email_dict, session)
    assert result == "Travel"


def test_predict_category_with_from_field(session):
    """Test that predict_category works with 'from' field instead of 'sender'"""
    rule = CategoryRule(
        match_type="sender",
        pattern="*@uber.com",
        assigned_category="Travel",
        priority=10,
    )
    session.add(rule)
    session.commit()

    class EmailWithFrom:
        def __init__(self):
            self.subject = "Your trip"
            setattr(self, "from", "receipts@uber.com")

    email = EmailWithFrom()
    result = Categorizer.predict_category(email, session)
    assert result == "Travel"


def test_get_fallback_category_uber():
    """Test fallback categorization for Uber"""
    email = MockEmail(subject="Your trip", sender="receipts@uber.com")
    assert Categorizer.get_fallback_category(email) == "transportation"


def test_get_fallback_category_amazon():
    """Test fallback categorization for Amazon"""
    email = MockEmail(subject="Order", sender="auto-confirm@amazon.com")
    assert Categorizer.get_fallback_category(email) == "amazon"


def test_get_fallback_category_aws():
    """Test fallback categorization for AWS"""
    email = MockEmail(subject="Invoice", sender="billing@aws.com")
    assert Categorizer.get_fallback_category(email) == "amazon"


def test_get_fallback_category_mcdonalds():
    """Test fallback categorization for McDonald's"""
    email = MockEmail(subject="Receipt", sender="orders@mcdonalds.com")
    assert Categorizer.get_fallback_category(email) == "restaurants"


def test_get_fallback_category_doordash():
    """Test fallback categorization for DoorDash"""
    email = MockEmail(subject="Order", sender="no-reply@doordash.com")
    assert Categorizer.get_fallback_category(email) == "food-delivery"


def test_get_fallback_category_walmart():
    """Test fallback categorization for Walmart"""
    email = MockEmail(subject="Order", sender="noreply@walmart.com")
    assert Categorizer.get_fallback_category(email) == "retail"


def test_get_fallback_category_netflix():
    """Test fallback categorization for Netflix"""
    email = MockEmail(subject="Billing", sender="info@netflix.com")
    assert Categorizer.get_fallback_category(email) == "subscriptions"


def test_get_fallback_category_paypal():
    """Test fallback categorization for PayPal"""
    email = MockEmail(subject="Payment", sender="service@paypal.com")
    assert Categorizer.get_fallback_category(email) == "payments"


def test_get_fallback_category_utilities():
    """Test fallback categorization for utilities"""
    email = MockEmail(subject="Bill", sender="billing@att.com")
    assert Categorizer.get_fallback_category(email) == "utilities"


def test_get_fallback_category_healthcare():
    """Test fallback categorization for healthcare"""
    email1 = MockEmail(subject="Prescription", sender="pharmacy@cvs.com")
    assert Categorizer.get_fallback_category(email1) == "healthcare"

    # Test subject-based match
    email2 = MockEmail(subject="Your prescription is ready", sender="store@local.com")
    assert Categorizer.get_fallback_category(email2) == "healthcare"


def test_get_fallback_category_government():
    """Test fallback categorization for government"""
    email1 = MockEmail(subject="Notice", sender="noreply@irs.gov")
    assert Categorizer.get_fallback_category(email1) == "government"

    # Test subject-based match
    email2 = MockEmail(subject="Tax payment received", sender="mail@local.gov")
    assert Categorizer.get_fallback_category(email2) == "government"


def test_get_fallback_category_unknown():
    """Test fallback categorization returns 'other' for unknown senders"""
    email = MockEmail(subject="Hello", sender="unknown@random.com")
    assert Categorizer.get_fallback_category(email) == "other"


def test_integration_rule_overrides_fallback(session):
    """Test that CategoryRule takes precedence over fallback logic"""
    # Create a rule that overrides the default "transportation" category for Uber
    rule = CategoryRule(
        match_type="sender",
        pattern="*@uber.com",
        assigned_category="Business Travel",
        priority=10,
    )
    session.add(rule)
    session.commit()

    email = MockEmail(subject="Trip", sender="receipts@uber.com")

    # With rules, should use the custom category
    assert Categorizer.predict_category(email, session) == "Business Travel"

    # Fallback would return "transportation"
    assert Categorizer.get_fallback_category(email) == "transportation"
