"""Service for rendering HTML responses for quick action endpoints."""

import html
from typing import List

from backend.models import Preference


class ActionHtmlService:
    """Service for generating HTML responses for action links."""

    @staticmethod
    def render_success(message: str, emoji: str) -> str:
        """
        Render a success page for action confirmation.

        Args:
            message: The success message to display
            emoji: The emoji to show, already extracted by the caller (only the emoji character/string)

        Returns:
            HTML string
        """
        return f"""
         <html>
            <body style="font-family: sans-serif; text-align: center; padding: 50px;">
                <div style="font-size: 50px;">{html.escape(emoji)}</div>
                <h1>Action Confirmed</h1>
                <p style="font-size: 18px; color: #555;">{html.escape(message)}</p>
                <p><a href="/history">Go to Dashboard</a></p>
            </body>
         </html>
         """

    @staticmethod
    def render_error(title: str, description: str, icon: str = "❌") -> str:
        """
        Render an error page.

        Args:
            title: Error title
            description: Error description
            icon: Icon to display

        Returns:
            HTML string
        """
        return f"""
         <html>
            <body style="font-family: sans-serif; text-align: center; padding: 50px;">
                <div style="font-size: 50px;">{icon}</div>
                <h1>{html.escape(title)}</h1>
                <p style="font-size: 18px; color: #555;">{html.escape(description)}</p>
            </body>
         </html>
         """

    @staticmethod
    def render_unknown_command() -> str:
        """Render a page for unknown commands."""
        return """
         <html>
            <body style="font-family: sans-serif; text-align: center; padding: 50px;">
                <div style="font-size: 50px;">❓</div>
                <h1>Unknown Command</h1>
                <p style="font-size: 18px; color: #555;">The requested action is not recognized.</p>
                <p><a href="/history">Go to Dashboard</a></p>
            </body>
         </html>
         """

    @staticmethod
    def render_settings_view(preferences: List[Preference]) -> str:
        """
        Render the settings view showing current preferences.

        Args:
            preferences: List of all preferences

        Returns:
            HTML string with formatted settings view
        """
        blocked_types = {"Blocked Sender", "Blocked Category"}
        allowed_types = {"Always Forward Sender", "Always Forward Category"}
        blocked = [p for p in preferences if p.type in blocked_types]
        allowed = [p for p in preferences if p.type in allowed_types]

        html_list = ""

        if allowed:
            html_list += """
            <div style="margin-bottom: 24px;">
                <h3 style="color: #15803d; font-size: 14px; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 12px; display: flex; align-items: center; gap: 6px;">
                    ✅ Always Forwarding
                </h3>
                <div style="display: flex; flex-wrap: wrap; gap: 8px;">
            """
            for p in allowed:
                safe_item = html.escape(p.item)
                html_list += f"""
                <span style="background: #dcfce7; color: #166534; padding: 6px 12px; border-radius: 9999px; font-size: 13px; font-weight: 500; border: 1px solid #bbf7d0;">
                    {safe_item}
                </span>
                """
            html_list += "</div></div>"

        if blocked:
            html_list += """
            <div style="margin-bottom: 24px;">
                <h3 style="color: #b91c1c; font-size: 14px; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 12px; display: flex; align-items: center; gap: 6px;">
                    🚫 Blocked
                </h3>
                <div style="display: flex; flex-wrap: wrap; gap: 8px;">
            """
            for p in blocked:
                safe_item = html.escape(p.item)
                html_list += f"""
                <span style="background: #fee2e2; color: #991b1b; padding: 6px 12px; border-radius: 9999px; font-size: 13px; font-weight: 500; border: 1px solid #fecaca;">
                    {safe_item}
                </span>
                """
            html_list += "</div></div>"

        if not blocked and not allowed:
            html_list = """
            <div style="text-align: center; padding: 40px 20px; color: #71717a;">
                <p>No active preferences found yet.</p>
                <p style="font-size: 13px;">Use the action buttons in forwarded emails to build your list.</p>
            </div>
            """

        return f"""
         <!DOCTYPE html>
         <html>
            <head>
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <style>
                    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background-color: #f4f4f5; margin: 0; padding: 20px; color: #18181b; }}
                    .container {{ max-width: 500px; margin: 0 auto; background: white; border-radius: 12px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06); overflow: hidden; }}
                    .header {{ background: #fafafa; padding: 20px; border-bottom: 1px solid #e4e4e7; text-align: center; }}
                    .logo {{ font-size: 24px; margin-bottom: 8px; display: block; }}
                    .title {{ font-weight: 600; font-size: 18px; margin: 0; color: #18181b; }}
                    .content {{ padding: 24px; }}
                    .footer {{ padding: 16px; text-align: center; background: #fafafa; border-top: 1px solid #e4e4e7; }}
                    .btn {{ display: inline-block; background: #2563eb; color: white; text-decoration: none; padding: 10px 20px; border-radius: 6px; font-weight: 500; font-size: 14px; transition: background 0.2s; }}
                    .btn:hover {{ background: #1d4ed8; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <span class="logo">⚙️</span>
                        <h1 class="title">Current Settings</h1>
                    </div>
                    <div class="content">
                        {html_list}
                    </div>
                    <div class="footer">
                        <a href="/history" class="btn">Go to Dashboard</a>
                    </div>
                </div>
            </body>
         </html>
         """
