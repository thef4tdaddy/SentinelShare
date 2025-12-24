import os
from unittest.mock import MagicMock, patch

import pytest
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from backend.models import ManualRule, Preference
from backend.services.detector import ReceiptDetector


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


def test_is_receipt_strong_indicators():
    email = MockEmail(
        subject="Your Order Confirmation",
        body="Thank you for your order. Order #123456. Total: $50.00",
        sender="orders@shop.com",
    )
    assert ReceiptDetector.is_receipt(email)


def test_is_promotional_email_spam():
    email = MockEmail(
        subject="Huge Sale! 50% Off Everything!",
        body="Don't miss out on these deals! Click here to shop now.",
        sender="marketing@shop.com",
    )
    assert not ReceiptDetector.is_receipt(email)
    assert ReceiptDetector.is_promotional_email(email.subject, email.body, email.sender)


def test_is_shipping_notification():
    email = MockEmail(
        subject="Your package has shipped",
        body="Your item is on the way. Track it here.",
        sender="shipping@amazon.com",
    )
    # Should be excluded even if it looks transactional-ish, because it's shipping
    assert ReceiptDetector.is_shipping_notification(
        email.subject, email.body, email.sender
    )
    assert not ReceiptDetector.is_receipt(email)


def test_shipping_with_receipt_indicators_should_pass_checks():
    # If a shipping email implies it's also a receipt (contains payment info), logic might be tricky.
    # The JS logic says: it's shipping IF matches shipping patterns AND NOT purchase indicators.
    # So if it HAS purchase indicators, it returns FALSE for is_shipping_notification.
    # Thus, it flows through to subsequent checks and might be marked as receipt.
    email = MockEmail(
        subject="Your package has shipped",
        body="Your item is on the way. Order Total: $25.99. Payment method: Visa.",
        sender="notifications@generic-store.com",
    )
    # is_shipping_notification should return False because it has purchase indicators
    assert not ReceiptDetector.is_shipping_notification(
        email.subject, email.body, email.sender
    )
    # So is_receipt should likely return True (as it's a receipt + shipping info)
    assert ReceiptDetector.is_receipt(email)


def test_parity_cases_amazon_order():
    email = MockEmail(
        subject="Your Amazon.com order #112-3492812-12345",
        body="Thank you for your order. Total: $12.99",
        sender="auto-confirm@amazon.com",
    )
    assert ReceiptDetector.is_receipt(email)
    assert ReceiptDetector.categorize_receipt(email) == "amazon"


def test_parity_cases_uber_trip():
    email = MockEmail(
        subject="Your Tuesday morning trip with Uber",
        body="Total: $15.42. Thanks for riding.",
        sender="receipts@uber.com",
    )
    assert ReceiptDetector.is_receipt(email)
    assert ReceiptDetector.categorize_receipt(email) == "transportation"


def test_reply_exclusion():
    email = MockEmail(
        subject="Re: Your Order", body="Hey, did you see this?", sender="me@gmail.com"
    )
    assert not ReceiptDetector.is_receipt(email)


def test_transactional_score_low_matches():
    # Email with weak signals
    email = MockEmail(
        subject="Meeting reminder",
        body="Don't forget the meeting.",
        sender="colleague@work.com",
    )
    assert (
        ReceiptDetector.calculate_transactional_score(
            email.subject, email.body, email.sender
        )
        == 0
    )
    assert not ReceiptDetector.is_receipt(email)


def test_transactional_score_high_matches():
    # Email with generic transactional terms but no 'receipt' keyword
    email = MockEmail(
        subject="Payment Notification",
        body="We received your payment of $100.00. Invoice #999.",
        sender="billing@service.com",
    )
    # Score:
    # $... -> 2
    # Invoice #... -> 2
    # Payment -> 1
    # Billing -> 1
    # Total > 3
    assert (
        ReceiptDetector.calculate_transactional_score(
            email.subject, email.body, email.sender
        )
        >= 3
    )
    assert ReceiptDetector.is_receipt(email)


def test_categorize_receipt_amazon():
    email = MockEmail(
        subject="Order Confirmation",
        body="Your order from Amazon",
        sender="auto-confirm@amazon.com",
    )
    assert ReceiptDetector.categorize_receipt(email) == "amazon"


def test_categorize_receipt_transportation():
    email = MockEmail(
        subject="Trip Receipt", body="Your Uber trip", sender="receipts@uber.com"
    )
    assert ReceiptDetector.categorize_receipt(email) == "transportation"

    email2 = MockEmail(
        subject="Ride Receipt", body="Thanks for riding", sender="noreply@lyft.com"
    )
    assert ReceiptDetector.categorize_receipt(email2) == "transportation"


def test_categorize_receipt_food_delivery():
    email = MockEmail(
        subject="Order Confirmation",
        body="Your DoorDash order",
        sender="no-reply@doordash.com",
    )
    assert ReceiptDetector.categorize_receipt(email) == "food-delivery"


def test_categorize_receipt_restaurants():
    email = MockEmail(
        subject="Order Receipt",
        body="Thank you for your order",
        sender="orders@starbucks.com",
    )
    assert ReceiptDetector.categorize_receipt(email) == "restaurants"


def test_categorize_receipt_retail():
    email = MockEmail(
        subject="Purchase Confirmation",
        body="Thank you for shopping",
        sender="orders@walmart.com",
    )
    assert ReceiptDetector.categorize_receipt(email) == "retail"


def test_categorize_receipt_subscriptions():
    email = MockEmail(
        subject="Subscription Receipt",
        body="Your monthly subscription",
        sender="billing@netflix.com",
    )
    assert ReceiptDetector.categorize_receipt(email) == "subscriptions"


def test_categorize_receipt_payments():
    email = MockEmail(
        subject="Payment Received", body="You've got money", sender="service@paypal.com"
    )
    assert ReceiptDetector.categorize_receipt(email) == "payments"


def test_categorize_receipt_utilities():
    email = MockEmail(
        subject="Bill Ready", body="Your monthly bill", sender="billing@att.com"
    )
    assert ReceiptDetector.categorize_receipt(email) == "utilities"


def test_categorize_receipt_healthcare():
    email = MockEmail(
        subject="Prescription Ready",
        body="Your prescription is ready",
        sender="pharmacy@cvs.com",
    )
    assert ReceiptDetector.categorize_receipt(email) == "healthcare"


def test_categorize_receipt_government():
    email = MockEmail(
        subject="Tax Notice", body="Tax payment received", sender="noreply@irs.gov"
    )
    assert ReceiptDetector.categorize_receipt(email) == "government"


def test_categorize_receipt_other():
    email = MockEmail(
        subject="Order Confirmation", body="Thank you", sender="info@randomshop.com"
    )
    assert ReceiptDetector.categorize_receipt(email) == "other"


def test_get_detection_confidence_promotional():
    email = MockEmail(
        subject="Sale! 50% off", body="Shop now and save", sender="marketing@shop.com"
    )
    # Promotional emails should have 0 confidence
    assert ReceiptDetector.get_detection_confidence(email) == 0


def test_get_detection_confidence_high():
    email = MockEmail(
        subject="Receipt for your order",
        body="Thank you for your order. Order #123456. Total: $50.00",
        sender="auto-confirm@amazon.com",
    )
    # Strong indicators (40) + transactional score (high) + known sender (20) + confirmation (10)
    confidence = ReceiptDetector.get_detection_confidence(email)
    assert confidence >= 70


def test_get_detection_confidence_medium():
    email = MockEmail(
        subject="Payment received",
        body="Your order #12345678 total: $20.00",
        sender="shop@example.com",
    )
    confidence = ReceiptDetector.get_detection_confidence(email)
    # This email has order # (2 pts) and amount (2 pts) * 10 = 40, should have moderate confidence
    assert confidence >= 40


def test_get_detection_confidence_low():
    email = MockEmail(
        subject="Hello", body="Just saying hi", sender="friend@example.com"
    )
    confidence = ReceiptDetector.get_detection_confidence(email)
    assert confidence == 0


def test_is_known_receipt_sender():
    assert ReceiptDetector.is_known_receipt_sender("auto-confirm@amazon.com")
    assert ReceiptDetector.is_known_receipt_sender("service@paypal.com")
    assert ReceiptDetector.is_known_receipt_sender("receipts@uber.com")
    assert not ReceiptDetector.is_known_receipt_sender("random@example.com")


def test_has_transaction_confirmation():
    assert ReceiptDetector.has_transaction_confirmation("Order Confirmation", "Receipt")
    assert ReceiptDetector.has_transaction_confirmation(
        "Invoice #123", "Payment received"
    )
    assert ReceiptDetector.has_transaction_confirmation(
        "Your order #456", "Total: $50.00"
    )
    assert not ReceiptDetector.has_transaction_confirmation("Hello", "Just a message")


def test_has_strong_receipt_indicators_with_evidence():
    # Strong keyword + supporting evidence
    assert ReceiptDetector.has_strong_receipt_indicators(
        "Your receipt is ready", "Order #123456 Total: $50.00"
    )


def test_has_strong_receipt_indicators_without_evidence():
    # Strong keyword but no supporting evidence
    assert (
        ReceiptDetector.has_strong_receipt_indicators(
            "Receipt", "Just a receipt mention"
        )
        is False
    )


def test_is_reply_or_forward_patterns():
    # Test various reply patterns
    assert ReceiptDetector.is_reply_or_forward(
        "Re: Order Confirmation", "sender@example.com"
    )
    assert ReceiptDetector.is_reply_or_forward("Fwd: Receipt", "sender@example.com")
    assert ReceiptDetector.is_reply_or_forward("FW: Your Order", "sender@example.com")
    assert ReceiptDetector.is_reply_or_forward(
        "Forward: Important", "sender@example.com"
    )
    assert ReceiptDetector.is_reply_or_forward("[FWD] Check this", "sender@example.com")
    assert ReceiptDetector.is_reply_or_forward("(fwd) See below", "sender@example.com")
    assert not ReceiptDetector.is_reply_or_forward("Your Order", "sender@example.com")


def test_email_dict_format():
    # Test that detector works with dict format emails
    email_dict = {
        "subject": "Order Confirmation",
        "body": "Thank you for your order. Order #123456. Total: $50.00",
        "sender": "orders@shop.com",
    }
    assert ReceiptDetector.is_receipt(email_dict)


def test_email_with_from_field():
    # Test email with 'from' field instead of 'sender'
    class EmailWithFrom:
        def __init__(self):
            self.subject = "Receipt"
            self.body = "Order #123456 Total: $50.00"
            setattr(self, "from", "orders@shop.com")

    email = EmailWithFrom()
    assert ReceiptDetector.is_receipt(email)


def test_promotional_patterns():
    # Test various promotional patterns
    assert ReceiptDetector.is_promotional_email(
        "20% off today!", "Shop now", "sales@shop.com"
    )
    assert ReceiptDetector.is_promotional_email(
        "Save $50", "Limited time", "marketing@shop.com"
    )
    assert ReceiptDetector.is_promotional_email(
        "Free shipping", "Check this week", "deals@shop.com"
    )
    assert ReceiptDetector.is_promotional_email(
        "Weekly deals", "Best deals this week", "digest@shop.com"
    )
    assert ReceiptDetector.is_promotional_email(
        "", "Check out unsubscribe here", "promo@shop.com"
    )
    assert ReceiptDetector.is_promotional_email(
        "", "Visit awstrack.me/link", "marketing@shop.com"
    )


# ============================================================================
# Database Override Tests (Manual Rules and Preferences) - Lines 33-67
# ============================================================================


def test_manual_rule_with_email_pattern(session):
    """Test manual rule matching with email pattern"""
    rule = ManualRule(
        email_pattern="*@shop.com",
        subject_pattern=None,
        priority=10,
        purpose="Test Shop Rule",
    )
    session.add(rule)
    session.commit()

    email = MockEmail(
        subject="Random Subject", body="Some content", sender="orders@shop.com"
    )
    assert ReceiptDetector.is_receipt(email, session) is True


def test_manual_rule_with_subject_pattern(session):
    """Test manual rule matching with subject pattern"""
    rule = ManualRule(
        email_pattern=None,
        subject_pattern="*order*",
        priority=10,
        purpose="Order Pattern Rule",
    )
    session.add(rule)
    session.commit()

    email = MockEmail(
        subject="Your order is ready", body="Content", sender="shop@example.com"
    )
    assert ReceiptDetector.is_receipt(email, session) is True


def test_manual_rule_with_both_patterns(session):
    """Test manual rule with both email and subject patterns"""
    rule = ManualRule(
        email_pattern="*@amazon.com",
        subject_pattern="*confirmation*",
        priority=20,
        purpose="Amazon Confirmation Rule",
    )
    session.add(rule)
    session.commit()

    # Both patterns match
    email1 = MockEmail(
        subject="Order Confirmation",
        body="Thank you",
        sender="orders@amazon.com",
    )
    assert ReceiptDetector.is_receipt(email1, session) is True

    # Only email matches - should not match
    email2 = MockEmail(
        subject="Random Subject", body="Content", sender="info@amazon.com"
    )
    assert ReceiptDetector.is_receipt(email2, session) is False


def test_manual_rule_priority_ordering(session):
    """Test that higher priority rules are checked first"""
    # Lower priority rule
    rule1 = ManualRule(
        email_pattern="*@test.com",
        subject_pattern=None,
        priority=5,
        purpose="Low Priority Rule",
    )
    # Higher priority rule
    rule2 = ManualRule(
        email_pattern="*@test.com",
        subject_pattern=None,
        priority=15,
        purpose="High Priority Rule",
    )
    session.add(rule1)
    session.add(rule2)
    session.commit()

    email = MockEmail(subject="Test", body="Content", sender="info@test.com")
    # Should match the higher priority rule
    assert ReceiptDetector.is_receipt(email, session) is True


def test_preference_always_forward_sender(session):
    """Test 'Always Forward' preference matching sender"""
    pref = Preference(item="paypal.com", type="Always Forward")
    session.add(pref)
    session.commit()

    email = MockEmail(
        subject="Random email", body="No receipt indicators", sender="service@paypal.com"
    )
    assert ReceiptDetector.is_receipt(email, session) is True


def test_preference_always_forward_subject(session):
    """Test 'Always Forward' preference matching subject"""
    pref = Preference(item="invoice", type="Always Forward")
    session.add(pref)
    session.commit()

    email = MockEmail(
        subject="Invoice for services",
        body="No other indicators",
        sender="billing@random.com",
    )
    assert ReceiptDetector.is_receipt(email, session) is True


def test_preference_blocked_sender(session):
    """Test 'Blocked Sender' preference"""
    pref = Preference(item="marketing", type="Blocked Sender")
    session.add(pref)
    session.commit()

    # Even with strong receipt indicators, should be blocked
    email = MockEmail(
        subject="Order Confirmation",
        body="Order #123456 Total: $50.00",
        sender="marketing@shop.com",
    )
    assert ReceiptDetector.is_receipt(email, session) is False


def test_preference_blocked_category(session):
    """Test 'Blocked Category' preference"""
    pref = Preference(item="newsletter", type="Blocked Category")
    session.add(pref)
    session.commit()

    email = MockEmail(
        subject="Monthly Newsletter with receipt info",
        body="Order #123456",
        sender="info@shop.com",
    )
    assert ReceiptDetector.is_receipt(email, session) is False


def test_database_exception_handling():
    """Test that exceptions in database checks are handled gracefully"""
    # Create a mock session that raises an exception
    mock_session = MagicMock()
    mock_session.exec.side_effect = Exception("Database error")

    email = MockEmail(
        subject="Order Confirmation", body="Order #123456", sender="shop@example.com"
    )
    # Should not raise exception and should fall back to normal detection
    result = ReceiptDetector.is_receipt(email, mock_session)
    # The email has strong indicators, so should still be detected
    assert result is True


# ============================================================================
# debug_is_receipt Method Tests - Lines 122-159
# ============================================================================


def test_debug_is_receipt_with_manual_rule(session):
    """Test debug_is_receipt returns trace with manual rule match"""
    rule = ManualRule(
        email_pattern="*@shop.com",
        subject_pattern=None,
        priority=10,
        purpose="Debug Test Rule",
    )
    session.add(rule)
    session.commit()

    email = MockEmail(subject="Test", body="Content", sender="orders@shop.com")
    trace = ReceiptDetector.debug_is_receipt(email, session)

    assert trace["final_decision"] is True
    assert trace["matched_by"] == "Manual Rule"
    assert len(trace["steps"]) > 0
    assert trace["steps"][0]["step"] == "Manual Rule"
    assert trace["steps"][0]["result"] is True


def test_debug_is_receipt_without_session():
    """Test debug_is_receipt without session"""
    email = MockEmail(
        subject="Receipt for your order",
        body="Order #123456 Total: $50.00",
        sender="shop@example.com",
    )
    trace = ReceiptDetector.debug_is_receipt(email, None)

    assert "subject" in trace
    assert "sender" in trace
    assert "steps" in trace
    assert "final_decision" in trace


# ============================================================================
# _check_manual_rules Helper Tests - Lines 166-181
# ============================================================================


def test_check_manual_rules_no_session():
    """Test _check_manual_rules returns None when no session provided"""
    result = ReceiptDetector._check_manual_rules("subject", "sender", None)
    assert result is None


def test_check_manual_rules_email_pattern_match(session):
    """Test _check_manual_rules with email pattern match"""
    rule = ManualRule(
        email_pattern="*@trusted.com",
        subject_pattern=None,
        priority=10,
        purpose="Trusted Sender",
    )
    session.add(rule)
    session.commit()

    result = ReceiptDetector._check_manual_rules(
        "any subject", "sender@trusted.com", session
    )
    assert result is not None
    assert result.purpose == "Trusted Sender"


def test_check_manual_rules_subject_pattern_match(session):
    """Test _check_manual_rules with subject pattern match"""
    rule = ManualRule(
        email_pattern=None,
        subject_pattern="*receipt*",
        priority=10,
        purpose="Receipt Keyword",
    )
    session.add(rule)
    session.commit()

    result = ReceiptDetector._check_manual_rules(
        "your receipt is ready", "any@sender.com", session
    )
    assert result is not None
    assert result.purpose == "Receipt Keyword"


def test_check_manual_rules_both_patterns_must_match(session):
    """Test _check_manual_rules requires both patterns to match when both are set"""
    rule = ManualRule(
        email_pattern="*@shop.com",
        subject_pattern="*order*",
        priority=10,
        purpose="Shop Orders",
    )
    session.add(rule)
    session.commit()

    # Only email matches
    result1 = ReceiptDetector._check_manual_rules(
        "random subject", "info@shop.com", session
    )
    assert result1 is None

    # Only subject matches
    result2 = ReceiptDetector._check_manual_rules(
        "your order", "info@other.com", session
    )
    assert result2 is None

    # Both match
    result3 = ReceiptDetector._check_manual_rules(
        "your order", "info@shop.com", session
    )
    assert result3 is not None
    assert result3.purpose == "Shop Orders"


def test_check_manual_rules_no_rules(session):
    """Test _check_manual_rules when no rules exist"""
    result = ReceiptDetector._check_manual_rules(
        "subject", "sender@example.com", session
    )
    assert result is None


# ============================================================================
# is_reply_or_forward Edge Cases - Lines 201, 221
# ============================================================================


def test_is_reply_or_forward_wife_email():
    """Test detection of wife's email"""
    with patch.dict(os.environ, {"WIFE_EMAIL": "spouse@example.com"}):
        assert ReceiptDetector.is_reply_or_forward(
            "Order Confirmation", "spouse@example.com"
        )


def test_is_reply_or_forward_personal_emails():
    """Test detection of personal email addresses from environment"""
    with patch.dict(
        os.environ,
        {
            "GMAIL_EMAIL": "personal@gmail.com",
            "ICLOUD_EMAIL": "personal@icloud.com",
            "SENDER_EMAIL": "personal@work.com",
        },
    ):
        # Gmail
        assert ReceiptDetector.is_reply_or_forward(
            "Order", "personal@gmail.com"
        )
        # iCloud
        assert ReceiptDetector.is_reply_or_forward(
            "Order", "personal@icloud.com"
        )
        # Sender email
        assert ReceiptDetector.is_reply_or_forward(
            "Order", "personal@work.com"
        )


@patch("backend.services.detector.EmailService.get_all_accounts")
def test_is_reply_or_forward_from_email_service_accounts(mock_get_accounts):
    """Test detection of emails from EmailService accounts"""
    mock_get_accounts.return_value = [
        {"email": "account1@example.com"},
        {"email": "account2@example.com"},
        {"email": None},  # Account without email
    ]

    assert ReceiptDetector.is_reply_or_forward(
        "Order", "account1@example.com"
    )
    assert ReceiptDetector.is_reply_or_forward(
        "Order", "account2@example.com"
    )
    # Account not in list should return False
    assert not ReceiptDetector.is_reply_or_forward(
        "Order", "other@example.com"
    )


# ============================================================================
# is_promotional_email Edge Cases - Lines 442, 446, 513
# ============================================================================


def test_promotional_subscribe_and_save_whitelist():
    """Test that 'subscribe & save' emails are not marked as promotional"""
    # Would normally be promotional due to keywords, but whitelisted
    result = ReceiptDetector.is_promotional_email(
        "Weekly deals and savings",
        "Your subscribe & save order has shipped",
        "shop@example.com",
    )
    assert result is False


def test_promotional_subscription_order_whitelist():
    """Test that 'subscription order' emails are not marked as promotional"""
    result = ReceiptDetector.is_promotional_email(
        "Special offer inside",
        "Your subscription order #12345",
        "subscriptions@example.com",
    )
    assert result is False


def test_promotional_government_sender_exemption():
    """Test that government senders are exempt from promotional filtering"""
    # Has promotional keywords but from government
    assert not ReceiptDetector.is_promotional_email(
        "Special notice about renewal",
        "Limited time to renew license",
        "notices@dmv.gov",
    )
    assert not ReceiptDetector.is_promotional_email(
        "Important update",
        "Sign up for alerts",
        "alerts@irs.gov",
    )
    assert not ReceiptDetector.is_promotional_email(
        "New service available",
        "Discover new features",
        "info@government.gov",
    )


def test_promotional_email_no_keywords():
    """Test that emails without promotional keywords return False"""
    result = ReceiptDetector.is_promotional_email(
        "Your order is ready", "Thank you for your purchase", "shop@example.com"
    )
    assert result is False


def test_promotional_email_deals_patterns():
    """Test promotional detection for deals-related patterns"""
    # dealsnet in sender
    assert ReceiptDetector.is_promotional_email(
        "Check this out", "Great offers", "info@dealsnet.com"
    )
    # slickdeals
    assert ReceiptDetector.is_promotional_email(
        "Hot deals", "Best prices", "alerts@slickdeals.net"
    )
    # reddit deals
    assert ReceiptDetector.is_promotional_email(
        "reddit deals alert", "Top deals today", "notify@reddit.com"
    )
    # game deals in body
    assert ReceiptDetector.is_promotional_email(
        "New notification", "Check out these game deals", "info@example.com"
    )
    # steam sale in subject
    assert ReceiptDetector.is_promotional_email(
        "Steam sale this weekend", "Don't miss out", "newsletter@gaming.com"
    )
    # Test "bargain" pattern which is ONLY in deals_patterns (not in earlier keyword lists)
    # This ensures we test the final deals_patterns check
    assert ReceiptDetector.is_promotional_email(
        "Weekly notification", "Check out this bargain", "info@shop.com"
    )


def test_transactional_score_triggers_receipt():
    """Test that high transactional score (>= 3) triggers receipt detection"""
    # Create email with high transactional score but NO strong receipt indicators
    # Avoid keywords like "receipt", "invoice", "order confirmation", etc.
    # Also avoid promotional keywords
    # But include transactional elements: order #, $amount, "transaction", "payment"
    email = MockEmail(
        subject="Transaction #ABC123456",
        body="Payment of $99.99 has been processed. Transaction reference #987654321.",
        sender="billing@service.com",
    )
    # Verify no strong indicators
    assert not ReceiptDetector.has_strong_receipt_indicators(email.subject, email.body)
    # Verify not promotional
    assert not ReceiptDetector.is_promotional_email(
        email.subject, email.body, email.sender
    )
    # Calculate score to verify it's >= 3
    # Transaction # (2) + $amount (2) + transaction keyword (1) + payment keyword (1) = 6
    score = ReceiptDetector.calculate_transactional_score(
        email.subject, email.body, email.sender
    )
    assert score >= 3, f"Expected score >= 3, got {score}"
    # This should be detected as receipt via transactional score path (lines 104-105)
    assert ReceiptDetector.is_receipt(email) is True
