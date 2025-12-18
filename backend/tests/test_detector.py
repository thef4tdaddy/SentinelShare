from backend.services.detector import ReceiptDetector


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
