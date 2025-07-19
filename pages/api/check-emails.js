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
  if (req.method !== "GET") {
    return res.status(405).json({ error: "Method not allowed" });
  }

  try {
    console.log("Starting email check...");

    const gmailClient = new GmailClient();
    const icloudClient = new ICloudClient();
    const emailSender = new EmailSender();
    const notion = new NotionDashboard();

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
            <div style="margin-top: 12px; padding-top: 12px; border-top: 1px solid #e5e7eb; font-size: 12px; color: #9ca3af;">
              📊 View detailed dashboard in Notion
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

    res.status(200).json({
      success: true,
      processed: allEmails.length,
      forwarded: forwardedCount,
      skipped: skippedCount,
      timestamp: new Date().toISOString(),
    });
  } catch (error) {
    console.error("Email check error:", error);
    const notion = new NotionDashboard();
    await notion.logActivity(
      { subject: "System Error", from: "system", source: "system" },
      "error",
      error.message
    );
    res
      .status(500)
      .json({ error: "Internal server error", details: error.message });
  }
}
