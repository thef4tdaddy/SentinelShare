"""Application constants"""

# Default email template for forwarding receipts
DEFAULT_EMAIL_TEMPLATE = """
<html>
    <body style="font-family: sans-serif; background-color: #f4f4f5; margin: 0; padding: 20px;">
        <div style="background-color: #f4f4f5; padding: 16px; border-radius: 8px; margin-bottom: 20px; border: 1px solid #e4e4e7;">
            <div style="font-weight: bold; color: #18181b; margin-bottom: 12px; font-size: 16px;">
                🛡️ SentinelAction: {simple_name}
            </div>
            <div style="display: flex; gap: 10px; flex-wrap: wrap;">
                <a href="{link_stop}" style="text-decoration: none; background-color: #ef4444; color: white; padding: 8px 16px; border-radius: 6px; font-size: 14px; font-weight: 500;">
                    🚫 Block {simple_name}
                </a>
                <a href="{link_more}" style="text-decoration: none; background-color: #22c55e; color: white; padding: 8px 16px; border-radius: 6px; font-size: 14px; font-weight: 500;">
                    ✅ Always Forward
                </a>
                <a href="{link_settings}" style="text-decoration: none; background-color: #71717a; color: white; padding: 8px 16px; border-radius: 6px; font-size: 14px; font-weight: 500;">
                    ⚙️ Settings
                </a>
            </div>
            <div style="font-size: 11px; color: #71717a; margin-top: 12px;">
                {action_type_text}
            </div>
        </div>
        <div style="font-size: 12px; color: #71717a; margin-bottom: 12px;">
            📅 Received: {received_date}
        </div>
        <hr style="border: 0; border-top: 1px solid #e5e7eb; margin: 20px 0;">
        <div style="font-family: sans-serif;">
            {body}
        </div>
    </body>
</html>
"""

# Manual rule priority for auto-created rules from ignored emails
DEFAULT_MANUAL_RULE_PRIORITY = 10
