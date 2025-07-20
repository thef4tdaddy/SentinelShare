// pages/api/check-emails.js
import {
  GmailClient,
  ICloudClient,
  EmailSender,
} from "../../lib/email-clients";
import { ReceiptDetector } from "../../lib/receipt-detector";
import { PreferenceManager } from "../../lib/preferences";
import { NotionDashboard } from "../../lib/notion-client";
import { CONFIG } from "../../lib/config";

export default async function handler(req, res) {
  // Set headers to prevent redirects and ensure JSON response
  res.setHeader('Content-Type', 'application/json');
  res.setHeader('Cache-Control', 'no-cache, no-store, must-revalidate');
  
  if (req.method !== "GET") {
    return res.status(405).json({ 
      success: false,
      error: "Method not allowed",
      timestamp: new Date().toISOString()
    });
  }

  // Set up timeout to prevent hanging requests
  const timeoutPromise = new Promise((_, reject) => {
    setTimeout(() => reject(new Error('Request timeout after 25 seconds')), 25000);
  });

  try {
    console.log("Starting email check at", new Date().toISOString());

    const gmailClient = new GmailClient();
    const icloudClient = new ICloudClient();
    const emailSender = new EmailSender();
    const notion = new NotionDashboard();

    // Wrap main logic in timeout handler
    const mainLogic = async () => {
      // Get recent emails from both accounts
    const [gmailEmails, icloudEmails] = await Promise.all([
      gmailClient.getRecentEmails().catch((err) => {
        console.error("Gmail error:", err);
        return [];
      }),
      icloudClient.getRecentEmails().catch((err) => {
        console.error("iCloud error:", err);
        return [];
      }),
    ]);

    const allEmails = [...gmailEmails, ...icloudEmails];

    // Get preferences from both KV store and Notion (Notion can override)
    const [kvPreferences, notionPreferences] = await Promise.all([
      PreferenceManager.getBlocklist(),
      notion.getPreferencesFromNotion(),
    ]);

    // Merge preferences (Notion takes priority for manual overrides)
    const preferences = {
      senders: [
        ...new Set([...kvPreferences.senders, ...notionPreferences.senders]),
      ],
      categories: [
        ...new Set([
          ...kvPreferences.categories,
          ...notionPreferences.categories,
        ]),
      ],
      whitelist: [
        ...new Set([
          ...kvPreferences.whitelist,
          ...notionPreferences.whitelist,
        ]),
      ],
    };

    const processedEmails = await PreferenceManager.getProcessedEmails();

    let forwardedCount = 0;
    let skippedCount = 0;

    for (const email of allEmails) {
      // Skip if already processed
      if (processedEmails.includes(email.id)) continue;

      // Check if it's a receipt
      if (!ReceiptDetector.isReceipt(email)) {
        await notion.logActivity(email, "processed", "Not a receipt");
        await PreferenceManager.markAsProcessed(email.id);
        continue;
      }

      // Check if blocked (using merged preferences)
      if (
        await PreferenceManager.isBlockedWithPreferences(email, preferences)
      ) {
        console.log(`Skipping blocked email: ${email.subject}`);
        await notion.logActivity(email, "blocked", "Matches block rule");
        skippedCount++;
        await PreferenceManager.markAsProcessed(email.id);
        continue;
      }

      // Forward the email
      const forwardSubject = CONFIG.FORWARD_TEMPLATE.subject.replace(
        "{originalSubject}",
        email.subject
      );
      const amount = notion.extractAmount(email.body || email.subject);
      const category = notion.categorizeEmail(email);

      const forwardBody = `
        <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif; max-width: 600px; margin: 0 auto; background: #ffffff;">
          <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 24px; border-radius: 12px 12px 0 0;">
            <h2 style="margin: 0; font-size: 20px; font-weight: 600;">📧 Receipt Forwarded</h2>
            <p style="margin: 8px 0 0 0; opacity: 0.9; font-size: 14px;">Automatically detected and forwarded</p>
          </div>
          
          <div style="padding: 24px; border: 1px solid #e1e5e9; border-top: none;">
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 20px; font-size: 14px;">
              <div>
                <strong style="color: #37352f;">From:</strong><br>
                <span style="color: #6b7280;">${email.from}</span>
              </div>
              <div>
                <strong style="color: #37352f;">Date:</strong><br>
                <span style="color: #6b7280;">${email.date.toLocaleDateString()}</span>
              </div>
              <div>
                <strong style="color: #37352f;">Category:</strong><br>
                <span style="background: #f3f4f6; padding: 2px 8px; border-radius: 4px; color: #374151; font-size: 12px;">${category}</span>
              </div>
              <div>
                <strong style="color: #37352f;">Amount:</strong><br>
                <span style="color: ${
                  amount ? "#059669" : "#6b7280"
                }; font-weight: ${amount ? "600" : "normal"};">${
        amount ? "$" + amount.toFixed(2) : "Not detected"
      }</span>
              </div>
            </div>
            
            <div style="background: #f9fafb; padding: 16px; border-radius: 8px; border-left: 4px solid #667eea; margin-bottom: 20px;">
              <h4 style="margin: 0 0 8px 0; color: #37352f; font-size: 14px;">Original Subject:</h4>
              <p style="margin: 0; color: #6b7280; font-size: 14px;">${
                email.subject
              }</p>
            </div>
            
            <div style="background: #ffffff; border: 1px solid #e5e7eb; border-radius: 8px; padding: 16px; max-height: 200px; overflow-y: auto; font-family: 'SF Mono', Monaco, 'Cascadia Code', monospace; font-size: 13px; line-height: 1.5;">
              ${email.body.substring(0, 1000)}${
        email.body.length > 1000 ? "..." : ""
      }
            </div>
          </div>
          
          <div style="background: #f8fafc; padding: 20px; border: 1px solid #e1e5e9; border-top: none; border-radius: 0 0 12px 12px;">
            <h4 style="margin: 0 0 12px 0; color: #37352f; font-size: 14px;">🎛️ Quick Commands</h4>
            <div style="font-size: 13px; color: #6b7280; line-height: 1.6;">
              Reply with any of these commands:<br>
              • <code style="background: #e5e7eb; padding: 2px 4px; border-radius: 3px;">STOP ${
                email.from.split("@")[0]
              }</code> - Block this sender<br>
              • <code style="background: #e5e7eb; padding: 2px 4px; border-radius: 3px;">STOP ${category.toLowerCase()}</code> - Block this category<br>
              • <code style="background: #e5e7eb; padding: 2px 4px; border-radius: 3px;">MORE ${
                email.from.split("@")[0]
              }</code> - Always forward from this sender<br>
              • <code style="background: #e5e7eb; padding: 2px 4px; border-radius: 3px;">SETTINGS</code> - View your preferences
            </div>
            
            <div style="margin-top: 20px; padding: 16px; background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%); border-radius: 8px; border-left: 4px solid #0ea5e9;">
              <div style="display: flex; align-items: center; margin-bottom: 8px;">
                <span style="font-size: 16px; margin-right: 8px;">🤖</span>
                <h5 style="margin: 0; color: #0c4a6e; font-size: 14px; font-weight: 600;">Smart Receipt Forwarder</h5>
              </div>
              <p style="margin: 0; font-size: 12px; color: #075985; line-height: 1.4;">
                This email was automatically detected as a receipt and forwarded to you by your personal receipt management system. 
                The system learns from your replies and uses Notion for smart filtering and analytics.
              </p>
              <div style="margin-top: 8px; font-size: 11px; color: #0284c7;">
                ✨ <strong>How it works:</strong> Monitors Gmail & iCloud → Detects receipts → Smart filtering → Forwards to you → Learns from your replies
              </div>
            </div>
            
            <div style="margin-top: 12px; padding-top: 12px; border-top: 1px solid #e5e7eb; font-size: 12px; color: #9ca3af; text-align: center;">
              📊 View detailed dashboard in Notion • 🛠️ Fully automated with smart learning
            </div>
          </div>
        </div>
      `;

      const success = await emailSender.sendEmail(
        process.env.WIFE_EMAIL,
        forwardSubject,
        forwardBody
      );

      if (success) {
        forwardedCount++;
        await notion.logActivity(
          email,
          "forwarded",
          `Category: ${category}${
            amount ? `, Amount: ${amount.toFixed(2)}` : ""
          }`
        );
        console.log(`Forwarded: ${email.subject}`);
      } else {
        await notion.logActivity(email, "failed", "Send failed");
        console.error(`Failed to forward: ${email.subject}`);
      }

      await PreferenceManager.markAsProcessed(email.id);
    }

    // Update stats in Notion
    await notion.updateStats({
      processed: allEmails.length,
      forwarded: forwardedCount,
      skipped: skippedCount,
      gmailConnected: gmailEmails.length >= 0,
      icloudConnected: icloudEmails.length >= 0,
    });

    // Sync current preferences to Notion
    await notion.updatePreferences(preferences);

    return {
      success: true,
      processed: allEmails.length,
      forwarded: forwardedCount,
      skipped: skippedCount,
      timestamp: new Date().toISOString(),
    };
  };

  // Execute with timeout
  const result = await Promise.race([mainLogic(), timeoutPromise]);
  res.status(200).json(result);
  } catch (error) {
    console.error("Email check error:", error);
    
    // Try to log to Notion but don't let it fail the response
    try {
      const notion = new NotionDashboard();
      await Promise.race([
        notion.logActivity(
          { subject: "System Error", from: "system", source: "system" },
          "error",
          error.message
        ),
        new Promise((_, reject) => setTimeout(() => reject(new Error('Notion logging timeout')), 5000))
      ]);
    } catch (notionError) {
      console.error("Failed to log to Notion:", notionError.message);
    }

    res.status(500).json({ 
      success: false,
      error: "Internal server error", 
      details: error.message,
      timestamp: new Date().toISOString(),
      processed: 0,
      forwarded: 0,
      skipped: 0
    });
  }
}
