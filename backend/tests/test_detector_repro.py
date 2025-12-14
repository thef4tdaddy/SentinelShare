import pytest
from backend.services.detector import ReceiptDetector


class MockEmail:
    def __init__(self, subject="", body="", sender=""):
        self.subject = subject
        self.body = body
        self.sender = sender


def test_false_negative_receipt_with_promo_footer():
    """
    Simulate a real receipt that has a promotional footer.
    Current behavior: Fails (returns False) because of 'Save' or 'Offer'.
    Desired behavior: True, because it has STRONG receipt indicators.
    """
    email = MockEmail(
        subject="Your Order #888888 Confirmation",
        body="""
        Thank you for your purchase.
        
        Order Summary:
        Item A: $10.00
        Item B: $20.00
        Total: $30.00
        
        Payment Method: Visa ending in 1234.
        
        ----------------------------------------
        Check out our weekly ad! Save big on new arrivals!
        Don't miss our holiday sale. 50% off everything.
        Unsubscribe here.
        """,
        sender="orders@retail-giant.com",
    )

    # This currently fails because 'Save big', 'holiday sale', '50% off' trigger is_promotional_email
    is_receipt = ReceiptDetector.is_receipt(email)

    # We WANT this to be True
    assert is_receipt == True, "Failed to detect receipt with promo footer"


def test_false_negative_digital_subscription():
    """
    Simulate a subscription renewal that might look like a newsletter.
    """
    email = MockEmail(
        subject="Your annual subscription renewal",
        body="""
        We've successfully processed your payment of $99.99 for the Annual Plan.
        Transaction ID: ABC-123456-XYZ
        
        Explore our new features in the latest update!
        """,
        sender="billing@service.com",
    )
    assert (
        ReceiptDetector.is_receipt(email) == True
    ), "Failed to detect subscription renewal"


def test_false_negative_user_example_ordered_subject():
    """
    User reported: 'Ordered: "LEGO Minecraft The Swamp..." and 6 more items' was missed.
    Likely because "Ordered" is not a strong keyword and body might trigger promo filters.
    """
    email = MockEmail(
        subject='Ordered: "LEGO Minecraft The Swamp..." and 6 more items',
        body="""
        Arriving Tomorrow.
        View your order.
        
        Buy it again?
        Recommended for you: Lego Star Wars...
        """,
        sender="auto-confirm@amazon.com",
    )
    assert (
        ReceiptDetector.is_receipt(email) == True
    ), "Failed to detect 'Ordered:' subject"
