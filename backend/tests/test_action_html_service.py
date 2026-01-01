"""Tests for ActionHtmlService."""

from backend.models import Preference
from backend.services.action_html_service import ActionHtmlService


class TestActionHtmlService:
    """Test suite for HTML rendering service."""

    def test_render_success(self):
        """Test success message rendering."""
        message = "Successfully blocked sender"
        emoji = "🚫"
        result = ActionHtmlService.render_success(message, emoji)

        assert "Action Confirmed" in result
        assert emoji in result
        assert message in result
        assert "/history" in result

    def test_render_success_escapes_html(self):
        """Test that HTML in success messages is properly escaped."""
        message = "<script>alert('xss')</script> Successfully blocked"
        emoji = "🚫"
        result = ActionHtmlService.render_success(message, emoji)

        # Should escape HTML tags
        assert "<script>" not in result
        assert "&lt;script&gt;" in result
        assert "Successfully blocked" in result

    def test_render_error(self):
        """Test error page rendering."""
        title = "Invalid Request"
        description = "The request could not be processed"
        result = ActionHtmlService.render_error(title, description)

        assert title in result
        assert description in result
        assert "❌" in result

    def test_render_error_custom_icon(self):
        """Test error page with custom icon."""
        icon = "⚠️"
        result = ActionHtmlService.render_error("Warning", "Test", icon=icon)

        assert icon in result

    def test_render_unknown_command(self):
        """Test unknown command page."""
        result = ActionHtmlService.render_unknown_command()

        assert "Unknown Command" in result
        assert "❓" in result
        assert "/history" in result

    def test_render_settings_view_with_preferences(self):
        """Test settings view with both blocked and allowed preferences."""
        prefs = [
            Preference(item="spam@example.com", type="Blocked Sender"),
            Preference(item="newsletter@company.com", type="Blocked Sender"),
            Preference(item="receipts@store.com", type="Always Forward"),
        ]

        result = ActionHtmlService.render_settings_view(prefs)

        assert "Current Settings" in result
        assert "Always Forwarding" in result
        assert "Blocked" in result
        assert "spam@example.com" in result
        assert "receipts@store.com" in result

    def test_render_settings_view_with_blocked_category(self):
        """Test settings view displays blocked categories correctly."""
        prefs = [
            Preference(item="spam@example.com", type="Blocked Sender"),
            Preference(item="restaurants", type="Blocked Category"),
            Preference(item="promotions", type="Blocked Category"),
            Preference(item="receipts@store.com", type="Always Forward"),
        ]

        result = ActionHtmlService.render_settings_view(prefs)

        assert "Current Settings" in result
        assert "Blocked" in result
        assert "spam@example.com" in result
        assert "restaurants" in result
        assert "promotions" in result
        assert "receipts@store.com" in result

    def test_render_settings_view_empty(self):
        """Test settings view with no preferences."""
        result = ActionHtmlService.render_settings_view([])

        assert "Current Settings" in result
        assert "No active preferences found yet" in result

    def test_render_settings_view_escapes_html(self):
        """Test that HTML in preference items is properly escaped."""
        prefs = [
            Preference(item="<script>alert('xss')</script>", type="Blocked Sender"),
        ]

        result = ActionHtmlService.render_settings_view(prefs)

        # Should escape HTML tags
        assert "<script>" not in result
        assert "&lt;script&gt;" in result
