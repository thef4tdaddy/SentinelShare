"""Tests for individual detection strategies."""

import pytest
from backend.services.detectors import (
    DetectionResult,
    ManualRuleStrategy,
    PromotionalStrategy,
    ShippingStrategy,
    TransactionalStrategy,
)
from backend.models import ManualRule, Preference
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool


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


class TestManualRuleStrategy:
    """Tests for ManualRuleStrategy."""

    def test_manual_rule_match(self, session):
        """Test that manual rules are detected correctly."""
        strategy = ManualRuleStrategy()

        # Add a manual rule
        rule = ManualRule(
            email_pattern="*@shop.com",
            subject_pattern="*order*",
            purpose="Test Shop Rule",
            priority=100,
        )
        session.add(rule)
        session.commit()

        email = {"subject": "Your order confirmation", "sender": "orders@shop.com"}
        result = strategy.detect(email, session)

        assert result.is_match is True
        assert result.confidence == 100
        assert result.matched_by == "Manual Rule"
        assert "Test Shop Rule" in result.reason

    def test_always_forward_preference(self, session):
        """Test that Always Forward preferences work."""
        strategy = ManualRuleStrategy()

        pref = Preference(type="Always Forward", item="important")
        session.add(pref)
        session.commit()

        email = {"subject": "important message", "sender": "test@example.com"}
        result = strategy.detect(email, session)

        assert result.is_match is True
        assert result.confidence == 100
        assert result.matched_by == "Always Forward Preference"

    def test_blocked_preference(self, session):
        """Test that blocked preferences are detected."""
        strategy = ManualRuleStrategy()

        pref = Preference(type="Blocked Sender", item="spam.com")
        session.add(pref)
        session.commit()

        email = {"subject": "test", "sender": "marketing@spam.com"}
        result = strategy.detect(email, session)

        assert result.is_match is False
        assert "Blocked" in result.reason

    def test_no_session_returns_no_match(self):
        """Test that no session returns no match."""
        strategy = ManualRuleStrategy()
        email = {"subject": "test", "sender": "test@example.com"}
        result = strategy.detect(email, None)

        assert result.is_match is False


class TestPromotionalStrategy:
    """Tests for PromotionalStrategy."""

    def test_promotional_keyword_in_subject(self):
        """Test detection of promotional keywords in subject."""
        strategy = PromotionalStrategy()
        email = {"subject": "Big Sale! 50% Off", "body": "", "sender": ""}
        result = strategy.detect(email)

        assert result.is_match is True
        assert result.confidence >= 80
        assert result.matched_by == "Promotional Strategy"

    def test_promotional_keyword_in_body(self):
        """Test detection of promotional keywords in body."""
        strategy = PromotionalStrategy()
        email = {
            "subject": "Newsletter",
            "body": "Check out our latest deals and discounts!",
            "sender": "",
        }
        result = strategy.detect(email)

        assert result.is_match is True
        assert result.matched_by == "Promotional Strategy"

    def test_promotional_with_allowlist(self):
        """Test that allowlisted promotional emails are not flagged."""
        strategy = PromotionalStrategy()
        email = {
            "subject": "Xbox Game Pass subscription renewal",
            "body": "Your subscription has been renewed.",
            "sender": "",
        }
        result = strategy.detect(email)

        assert result.is_match is False

    def test_subscribe_and_save_whitelist(self):
        """Test subscribe & save emails are not flagged as promotional."""
        strategy = PromotionalStrategy()
        email = {
            "subject": "Sale on items",
            "body": "Your Subscribe & Save order has shipped",
            "sender": "",
        }
        result = strategy.detect(email)

        assert result.is_match is False

    def test_government_sender_exemption(self):
        """Test government senders are exempt from promotional detection."""
        strategy = PromotionalStrategy()
        email = {
            "subject": "Save on your taxes",
            "body": "File today",
            "sender": "noreply@irs.gov",
        }
        result = strategy.detect(email)

        assert result.is_match is False

    def test_marketing_pattern_detection(self):
        """Test marketing patterns are detected."""
        strategy = PromotionalStrategy()
        email = {"subject": "Save $50 today!", "body": "", "sender": ""}
        result = strategy.detect(email)

        assert result.is_match is True

    def test_tracking_pattern_detection(self):
        """Test tracking URLs are detected."""
        strategy = PromotionalStrategy()
        email = {
            "subject": "Update",
            "body": "Click here: http://awstrack.me/tracking",
            "sender": "",
        }
        result = strategy.detect(email)

        assert result.is_match is True

    def test_deals_site_pattern(self):
        """Test deals site patterns are detected."""
        strategy = PromotionalStrategy()
        email = {"subject": "Test", "body": "", "sender": "alerts@slickdeals.net"}
        result = strategy.detect(email)

        assert result.is_match is True

    def test_non_promotional_email(self):
        """Test non-promotional email returns no match."""
        strategy = PromotionalStrategy()
        email = {
            "subject": "Your receipt",
            "body": "Thank you for your purchase",
            "sender": "orders@example.com",
        }
        result = strategy.detect(email)

        assert result.is_match is False


class TestShippingStrategy:
    """Tests for ShippingStrategy."""

    def test_shipping_sender_without_purchase(self):
        """Test shipping email from known carrier."""
        strategy = ShippingStrategy()
        email = {
            "subject": "Package shipped",
            "body": "Your package is on the way",
            "sender": "tracking@ups.com",
        }
        result = strategy.detect(email)

        assert result.is_match is True
        assert result.confidence >= 90

    def test_shipping_pattern_without_purchase(self):
        """Test shipping patterns without purchase indicators."""
        strategy = ShippingStrategy()
        email = {
            "subject": "Your package has been delivered",
            "body": "Package was left at your door",
            "sender": "delivery@example.com",
        }
        result = strategy.detect(email)

        assert result.is_match is True

    def test_shipping_with_purchase_indicators(self):
        """Test that shipping emails with purchase info are not flagged."""
        strategy = ShippingStrategy()
        email = {
            "subject": "Your order has shipped",
            "body": "Order total: $25.99. Your package is on the way.",
            "sender": "orders@store.com",
        }
        result = strategy.detect(email)

        assert result.is_match is False

    def test_non_shipping_email(self):
        """Test non-shipping email returns no match."""
        strategy = ShippingStrategy()
        email = {
            "subject": "Your receipt",
            "body": "Thank you for your order",
            "sender": "orders@store.com",
        }
        result = strategy.detect(email)

        assert result.is_match is False


class TestTransactionalStrategy:
    """Tests for TransactionalStrategy."""

    def test_strong_receipt_indicators(self):
        """Test strong receipt indicators are detected."""
        strategy = TransactionalStrategy()
        email = {
            "subject": "Order Confirmation",
            "body": "Order #123456, Total: $50.00",
            "sender": "orders@shop.com",
        }
        result = strategy.detect(email)

        assert result.is_match is True
        assert result.confidence >= 85

    def test_high_transactional_score(self):
        """Test high transactional score detection."""
        strategy = TransactionalStrategy()
        email = {
            "subject": "Invoice #ABC123",
            "body": "Amount: $100.00. Thank you for your purchase.",
            "sender": "billing@company.com",
        }
        result = strategy.detect(email)

        assert result.is_match is True

    def test_known_sender_with_confirmation(self):
        """Test known receipt sender with transaction confirmation."""
        strategy = TransactionalStrategy()
        email = {
            "subject": "Your receipt",
            "body": "Payment of $15.00",
            "sender": "receipts@uber.com",
        }
        result = strategy.detect(email)

        assert result.is_match is True

    def test_reply_email_excluded(self):
        """Test that reply emails are excluded."""
        strategy = TransactionalStrategy()
        email = {
            "subject": "Re: Order confirmation",
            "body": "Order #123",
            "sender": "customer@example.com",
        }
        result = strategy.detect(email)

        assert result.is_match is False
        assert "Reply or forward" in result.reason

    def test_forward_email_excluded(self):
        """Test that forwarded emails are excluded."""
        strategy = TransactionalStrategy()
        email = {
            "subject": "Fwd: Receipt",
            "body": "Order #123",
            "sender": "friend@example.com",
        }
        result = strategy.detect(email)

        assert result.is_match is False

    def test_definitive_receipt_pattern(self):
        """Test definitive receipt patterns."""
        strategy = TransactionalStrategy()
        email = {
            "subject": "Payment Receipt",
            "body": "Thank you",
            "sender": "billing@store.com",
        }
        result = strategy.detect(email)

        assert result.is_match is True

    def test_non_receipt_email(self):
        """Test non-receipt email returns no match."""
        strategy = TransactionalStrategy()
        email = {
            "subject": "Welcome to our service",
            "body": "Thank you for signing up",
            "sender": "welcome@service.com",
        }
        result = strategy.detect(email)

        assert result.is_match is False


class TestDetectionResult:
    """Tests for DetectionResult dataclass."""

    def test_detection_result_creation(self):
        """Test DetectionResult can be created with all fields."""
        result = DetectionResult(
            is_match=True,
            confidence=95,
            reason="Test reason",
            matched_by="Test Strategy",
        )

        assert result.is_match is True
        assert result.confidence == 95
        assert result.reason == "Test reason"
        assert result.matched_by == "Test Strategy"

    def test_detection_result_defaults(self):
        """Test DetectionResult has proper defaults."""
        result = DetectionResult(is_match=False)

        assert result.is_match is False
        assert result.confidence == 0
        assert result.reason is None
        assert result.matched_by is None
