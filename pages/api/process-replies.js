// pages/api/process-replies.js
import { GmailClient } from "../../lib/email-clients.js";
import { ReplyParser } from "../../lib/reply-parser.js";
import { PreferenceManager } from "../../lib/preferences.js";
import { NotionDashboard } from "../../lib/notion-client.js";

export default async function handler(req, res) {
  if (req.method !== "GET") {
    return res.status(405).json({ error: "Method not allowed" });
  }

  try {
    const gmailClient = new GmailClient();
    const notion = new NotionDashboard();

    // Get recent emails from wife's replies
    const replyEmails = await gmailClient.getRecentEmails().catch((err) => {
      console.error("Gmail reply check error:", err);
      return [];
    });

    const processedReplies = await PreferenceManager.getProcessedEmails(
      "replies"
    );

    let newRepliesCount = 0;

    for (const email of replyEmails) {
      // Skip if not from wife or already processed
      if (
        !email.from.includes(process.env.WIFE_EMAIL) ||
        processedReplies.includes(email.id)
      )
        continue;

      // Only process replies to forwarded receipts
      if (!email.subject.includes("Re: 📧 Receipt Forward")) continue;

      const commands = ReplyParser.parseReply(email.body);
      let actionTaken = "No action taken";

      for (const command of commands) {
        if (command.action === "block") {
          await PreferenceManager.addToBlocklist(command.type, command.value);
          actionTaken = `Blocked ${command.type}: ${command.value}`;
          console.log(`Blocked ${command.type}: ${command.value}`);
        } else if (command.action === "unblock") {
          await PreferenceManager.removeFromBlocklist(
            command.type,
            command.value
          );
          actionTaken = `Unblocked ${command.type}: ${command.value}`;
          console.log(`Unblocked ${command.type}: ${command.value}`);
        } else if (command.action === "whitelist") {
          await PreferenceManager.addToWhitelist(command.value);
          actionTaken = `Added to always-forward: ${command.value}`;
          console.log(`Added to whitelist: ${command.value}`);
        }
      }

      if (commands.length > 0) {
        await notion.logReply(
          email.subject.replace("Re: 📧 Receipt Forward: ", ""),
          email.body.trim().substring(0, 200),
          actionTaken
        );
        newRepliesCount++;

        // Update preferences in Notion immediately
        const currentPrefs = await PreferenceManager.getBlocklist();
        await notion.updatePreferences(currentPrefs);
      }

      // Mark as processed
      await PreferenceManager.markAsProcessed(email.id, "replies");
    }

    res.status(200).json({
      success: true,
      processedReplies: newRepliesCount,
      timestamp: new Date().toISOString(),
    });
  } catch (error) {
    console.error("Reply processing error:", error);
    res
      .status(500)
      .json({ error: "Internal server error", details: error.message });
  }
}
