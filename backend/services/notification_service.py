"""Service for sending notifications via webhooks (Discord, Slack, etc.)."""

import asyncio
import os
import threading
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import httpx


class NotificationService:
    """Service for sending notifications to webhooks (Discord, Slack, etc.)."""

    @staticmethod
    def _get_webhook_url() -> Optional[str]:
        """Get the configured webhook URL from environment."""
        return os.environ.get("DISCORD_WEBHOOK_URL")

    @staticmethod
    def _build_discord_embed(
        title: str,
        description: str,
        color: int,
        fields: Optional[list] = None,
        footer: Optional[str] = None,
        thumbnail_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Build a Discord-compatible embed object.

        Args:
            title: Embed title
            description: Embed description
            color: Embed color (integer, e.g., 0x00FF00 for green)
            fields: Optional list of field dictionaries with 'name' and 'value'
            footer: Optional footer text
            thumbnail_url: Optional thumbnail image URL

        Returns:
            Dictionary containing the embed structure
        """
        embed: Dict[str, Any] = {
            "title": title,
            "description": description,
            "color": color,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        if fields:
            embed["fields"] = fields

        if footer:
            embed["footer"] = {"text": footer}

        if thumbnail_url:
            embed["thumbnail"] = {"url": thumbnail_url}

        return embed

    @staticmethod
    async def _send_webhook_async(webhook_url: str, payload: Dict[str, Any]) -> bool:
        """
        Send a webhook notification asynchronously.

        Args:
            webhook_url: The webhook URL to send to
            payload: The JSON payload to send

        Returns:
            True if successful, False otherwise
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(webhook_url, json=payload)
                response.raise_for_status()
                return True
        except Exception as e:
            print(f"❌ Failed to send webhook notification: {type(e).__name__}")
            return False

    @staticmethod
    def send_receipt_notification(
        vendor: str,
        amount: Optional[float] = None,
        subject: Optional[str] = None,
        dashboard_url: Optional[str] = None,
    ) -> None:
        """
        Send a notification when a receipt is captured.

        Args:
            vendor: The vendor/sender name
            amount: Optional amount parsed from the receipt
            subject: Optional email subject
            dashboard_url: Optional link to the dashboard

        This method is non-blocking and runs the async send in the background.
        """
        webhook_url = NotificationService._get_webhook_url()
        if not webhook_url:
            return  # Silently skip if webhook not configured

        # Format the description
        amount_text = f" - ${amount:.2f}" if amount else ""
        description = f"Received receipt from **{vendor}**{amount_text}"

        fields = []
        if subject:
            fields.append({"name": "Subject", "value": subject, "inline": False})
        if dashboard_url:
            fields.append(
                {"name": "Dashboard", "value": f"[View Details]({dashboard_url})", "inline": False}
            )

        embed = NotificationService._build_discord_embed(
            title="✅ Receipt Captured",
            description=description,
            color=0x22C55E,  # Green
            fields=fields if fields else None,
            footer="SentinelShare",
        )

        payload = {"embeds": [embed]}

        # Run async send in background without blocking
        # Note: We intentionally don't await or store the task reference
        # as this is a fire-and-forget operation for notifications
        try:
            # Try to create task in current event loop
            loop = asyncio.get_running_loop()
            loop.create_task(
                NotificationService._send_webhook_async(webhook_url, payload)
            )
        except RuntimeError:
            # No event loop running - use thread pool to avoid blocking
            thread = threading.Thread(
                target=lambda: asyncio.run(
                    NotificationService._send_webhook_async(webhook_url, payload)
                )
            )
            thread.daemon = True
            thread.start()

    @staticmethod
    def send_error_notification(
        error_type: str,
        error_message: str,
        context: Optional[str] = None,
    ) -> None:
        """
        Send a notification when an error occurs during processing.

        Args:
            error_type: Type of error (e.g., "Processing Error", "SMTP Error")
            error_message: The error message
            context: Optional context (e.g., email subject or sender)

        This method is non-blocking and runs the async send in the background.
        """
        webhook_url = NotificationService._get_webhook_url()
        if not webhook_url:
            return  # Silently skip if webhook not configured

        description = f"**Error Type:** {error_type}\n**Message:** {error_message}"

        fields = []
        if context:
            fields.append({"name": "Context", "value": context, "inline": False})

        embed = NotificationService._build_discord_embed(
            title="❌ Processing Error",
            description=description,
            color=0xEF4444,  # Red
            fields=fields if fields else None,
            footer="SentinelShare",
        )

        payload = {"embeds": [embed]}

        # Run async send in background without blocking
        # Note: We intentionally don't await or store the task reference
        # as this is a fire-and-forget operation for notifications
        try:
            # Try to create task in current event loop
            loop = asyncio.get_running_loop()
            loop.create_task(
                NotificationService._send_webhook_async(webhook_url, payload)
            )
        except RuntimeError:
            # No event loop running - use thread pool to avoid blocking
            thread = threading.Thread(
                target=lambda: asyncio.run(
                    NotificationService._send_webhook_async(webhook_url, payload)
                )
            )
            thread.daemon = True
            thread.start()
