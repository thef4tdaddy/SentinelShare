// pages/api/manual-check.js
import { GmailClient, ICloudClient } from "../../lib/email-clients.js";
import { ReceiptDetector } from "../../lib/receipt-detector.js";
import { NotionDashboard } from "../../lib/notion-client.js";

export default async function handler(req, res) {
  if (req.method !== "POST") {
    return res.status(405).json({ error: "Method not allowed" });
  }

  try {
    // Force check all emails from last 7 days instead of just unread
    const since = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000);

    const gmailClient = new GmailClient();
    const icloudClient = new ICloudClient();
    const notion = new NotionDashboard();

    const [gmailEmails, icloudEmails] = await Promise.all([
      gmailClient.getRecentEmails(since).catch((err) => {
        console.error("Gmail error:", err);
        return [];
      }),
      icloudClient.getRecentEmails(since).catch((err) => {
        console.error("iCloud error:", err);
        return [];
      }),
    ]);

    const allEmails = [...gmailEmails, ...icloudEmails];
    const receipts = allEmails.filter((email) =>
      ReceiptDetector.isReceipt(email)
    );

    await notion.logActivity(
      { subject: "Manual Check", from: "system", source: "system" },
      "processed",
      `Found ${receipts.length} receipts out of ${allEmails.length} emails`
    );

    res.status(200).json({
      success: true,
      totalEmails: allEmails.length,
      receiptsFound: receipts.length,
      receipts: receipts.map((email) => ({
        subject: email.subject,
        from: email.from,
        date: email.date,
        category: notion.categorizeEmail(email),
      })),
    });
  } catch (error) {
    console.error("Manual check error:", error);
    res
      .status(500)
      .json({ error: "Manual check failed", details: error.message });
  }
}
