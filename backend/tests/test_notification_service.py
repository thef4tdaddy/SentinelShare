import os
from unittest.mock import patch

from backend.services.notification_service import NotificationService


class TestNotificationService:
    """Tests for NotificationService"""

    @patch.dict(os.environ, {}, clear=True)
    def test_get_webhook_url_not_configured(self):
        """Test that webhook URL returns None when not configured"""
        assert NotificationService._get_webhook_url() is None

    @patch.dict(
        os.environ, {"DISCORD_WEBHOOK_URL": "https://discord.com/api/webhooks/123/abc"}
    )
    def test_get_webhook_url_configured(self):
        """Test that webhook URL is retrieved from environment"""
        url = NotificationService._get_webhook_url()
        assert url == "https://discord.com/api/webhooks/123/abc"

    def test_build_discord_embed_basic(self):
        """Test building a basic Discord embed"""
        embed = NotificationService._build_discord_embed(
            title="Test Title", description="Test Description", color=0x00FF00
        )

        assert embed["title"] == "Test Title"
        assert embed["description"] == "Test Description"
        assert embed["color"] == 0x00FF00
        assert "timestamp" in embed

    def test_build_discord_embed_with_fields(self):
        """Test building a Discord embed with fields"""
        fields = [
            {"name": "Field 1", "value": "Value 1", "inline": False},
            {"name": "Field 2", "value": "Value 2", "inline": True},
        ]

        embed = NotificationService._build_discord_embed(
            title="Test", description="Test", color=0xFF0000, fields=fields
        )

        assert "fields" in embed
        assert len(embed["fields"]) == 2
        assert embed["fields"][0]["name"] == "Field 1"

    def test_build_discord_embed_with_footer(self):
        """Test building a Discord embed with footer"""
        embed = NotificationService._build_discord_embed(
            title="Test",
            description="Test",
            color=0x0000FF,
            footer="Test Footer",
        )

        assert "footer" in embed
        assert embed["footer"]["text"] == "Test Footer"

    def test_build_discord_embed_with_thumbnail(self):
        """Test building a Discord embed with thumbnail"""
        embed = NotificationService._build_discord_embed(
            title="Test",
            description="Test",
            color=0x0000FF,
            thumbnail_url="https://example.com/image.png",
        )

        assert "thumbnail" in embed
        assert embed["thumbnail"]["url"] == "https://example.com/image.png"

    @patch.dict(os.environ, {}, clear=True)
    @patch("backend.services.notification_service.NotificationService._send_webhook_async")
    def test_send_receipt_notification_no_webhook(self, mock_send):
        """Test that notification is skipped when webhook not configured"""
        NotificationService.send_receipt_notification(
            vendor="Amazon", amount=50.00, subject="Your Amazon Order"
        )

        # Should not attempt to send if webhook not configured
        mock_send.assert_not_called()

    @patch.dict(
        os.environ, {"DISCORD_WEBHOOK_URL": "https://discord.com/api/webhooks/123/abc"}
    )
    @patch("asyncio.get_running_loop")
    def test_send_receipt_notification_with_webhook(self, mock_get_loop):
        """Test sending receipt notification when webhook is configured"""
        mock_loop = patch("asyncio.AbstractEventLoop").start()
        mock_loop.create_task = patch("asyncio.AbstractEventLoop.create_task").start()
        mock_get_loop.return_value = mock_loop
        
        NotificationService.send_receipt_notification(
            vendor="Amazon",
            amount=50.00,
            subject="Your Amazon Order",
            dashboard_url="https://app.example.com/",
        )

        # Verify that loop.create_task was called
        mock_loop.create_task.assert_called_once()

    @patch.dict(
        os.environ, {"DISCORD_WEBHOOK_URL": "https://discord.com/api/webhooks/123/abc"}
    )
    @patch("asyncio.get_running_loop")
    def test_send_receipt_notification_no_amount(self, mock_get_loop):
        """Test sending receipt notification without amount"""
        mock_loop = patch("asyncio.AbstractEventLoop").start()
        mock_loop.create_task = patch("asyncio.AbstractEventLoop.create_task").start()
        mock_get_loop.return_value = mock_loop
        
        NotificationService.send_receipt_notification(
            vendor="Starbucks", subject="Receipt from Starbucks"
        )

        mock_loop.create_task.assert_called_once()

    @patch.dict(os.environ, {}, clear=True)
    @patch("backend.services.notification_service.NotificationService._send_webhook_async")
    def test_send_error_notification_no_webhook(self, mock_send):
        """Test that error notification is skipped when webhook not configured"""
        NotificationService.send_error_notification(
            error_type="SMTP Error",
            error_message="Failed to connect",
            context="test@example.com",
        )

        mock_send.assert_not_called()

    @patch.dict(
        os.environ, {"DISCORD_WEBHOOK_URL": "https://discord.com/api/webhooks/123/abc"}
    )
    @patch("asyncio.get_running_loop")
    def test_send_error_notification_with_webhook(self, mock_get_loop):
        """Test sending error notification when webhook is configured"""
        mock_loop = patch("asyncio.AbstractEventLoop").start()
        mock_loop.create_task = patch("asyncio.AbstractEventLoop.create_task").start()
        mock_get_loop.return_value = mock_loop
        
        NotificationService.send_error_notification(
            error_type="Processing Error",
            error_message="Failed to parse email",
            context="Subject: Test Email",
        )

        mock_loop.create_task.assert_called_once()

    @patch.dict(
        os.environ, {"DISCORD_WEBHOOK_URL": "https://discord.com/api/webhooks/123/abc"}
    )
    @patch("asyncio.get_running_loop")
    def test_send_error_notification_no_context(self, mock_get_loop):
        """Test sending error notification without context"""
        mock_loop = patch("asyncio.AbstractEventLoop").start()
        mock_loop.create_task = patch("asyncio.AbstractEventLoop.create_task").start()
        mock_get_loop.return_value = mock_loop
        
        NotificationService.send_error_notification(
            error_type="Database Error", error_message="Connection timeout"
        )

        mock_loop.create_task.assert_called_once()
