// pages/api/process-replies.js
import { GmailClient, EmailSender } from "../../lib/email-clients.js";
import { ReplyParser } from "../../lib/reply-parser.js";
import { PreferenceManager } from "../../lib/preferences.js";
import { NotionDashboard } from "../../lib/notion-client.js";

async function handleGenericStop(command, replyEmail, originalSubject) {
  try {
    // Extract sender information from the original forwarded email
    const senderInfo = extractSenderFromForwardedEmail(replyEmail.body, originalSubject);
    
    if (senderInfo.email) {
      // Temporarily block the sender (24 hours)
      await PreferenceManager.addToTemporaryBlock(
        senderInfo.email, 
        "Generic STOP command - awaiting clarification"
      );
      
      // Send clarification email
      await sendClarificationEmail(senderInfo, originalSubject);
      
      console.log(`Temporarily blocked ${senderInfo.email} for 24 hours`);
    } else {
      console.log("Could not extract sender info from generic STOP command");
    }
  } catch (error) {
    console.error("Error handling generic stop:", error);
  }
}

function extractSenderFromForwardedEmail(replyBody, originalSubject) {
  // Try to extract sender email from the forwarded email content in the reply
  const emailRegex = /From:.*?([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})/i;
  const emailMatch = replyBody.match(emailRegex);
  
  let extractedEmail = null;
  
  if (emailMatch) {
    extractedEmail = emailMatch[1];
  }
  
  // Also try to extract from common email signature patterns
  const fromPatterns = [
    /from[:\s]+([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})/i,
    /sender[:\s]+([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})/i,
  ];
  
  for (const pattern of fromPatterns) {
    const match = replyBody.match(pattern);
    if (match) {
      extractedEmail = match[1];
      break;
    }
  }
  
  return {
    email: extractedEmail,
    subject: originalSubject
  };
}

async function sendClarificationEmail(senderInfo, originalSubject) {
  try {
    const emailSender = new EmailSender();
    const wifeEmail = process.env.WIFE_EMAIL;
    
    if (!wifeEmail) {
      console.error("WIFE_EMAIL not configured");
      return;
    }
    
    const subject = "🤔 Clarification Needed: Which emails should I stop forwarding?";
    
    const body = `
      <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif; max-width: 600px; margin: 0 auto; background: #ffffff;">
        <div style="background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); color: white; padding: 24px; border-radius: 12px 12px 0 0;">
          <h2 style="margin: 0; font-size: 20px; font-weight: 600;">🤔 I Need Clarification</h2>
          <p style="margin: 8px 0 0 0; opacity: 0.9; font-size: 14px;">You said "STOP" but I'm not sure what to stop</p>
        </div>
        
        <div style="padding: 24px; border: 1px solid #e1e5e9; border-top: none;">
          <div style="background: #fef3c7; padding: 16px; border-radius: 8px; border-left: 4px solid #f59e0b; margin-bottom: 20px;">
            <h4 style="margin: 0 0 8px 0; color: #92400e; font-size: 14px;">You replied "STOP" to:</h4>
            <p style="margin: 0; color: #78350f; font-size: 14px; font-weight: 500;">${originalSubject}</p>
            ${senderInfo.email ? `<p style="margin: 4px 0 0 0; color: #78350f; font-size: 13px;">From: ${senderInfo.email}</p>` : ''}
          </div>
          
          <p style="color: #374151; line-height: 1.6; margin-bottom: 20px;">
            I've <strong>temporarily stopped</strong> emails from this sender for 24 hours while you decide. 
            Please reply with one of these commands:
          </p>
          
          <div style="background: #f9fafb; padding: 16px; border-radius: 8px; margin-bottom: 20px;">
            <h4 style="margin: 0 0 12px 0; color: #374151; font-size: 14px;">📝 Reply with one of these:</h4>
            <div style="font-family: 'SF Mono', Monaco, 'Cascadia Code', monospace; font-size: 13px; line-height: 1.8;">
              ${senderInfo.email ? `• <strong>STOP ${senderInfo.email.split('@')[0]}</strong> - Block this specific sender<br/>` : ''}
              • <strong>STOP amazon</strong> - Block all Amazon emails<br/>
              • <strong>STOP restaurants</strong> - Block all restaurant receipts<br/>
              • <strong>MORE ${senderInfo.email ? senderInfo.email.split('@')[0] : 'sender'}</strong> - Always forward from this sender<br/>
              • <strong>NEVERMIND</strong> - Cancel the block, keep forwarding
            </div>
          </div>
          
          <div style="background: #fee2e2; padding: 16px; border-radius: 8px; border-left: 4px solid #ef4444;">
            <h5 style="margin: 0 0 8px 0; color: #dc2626; font-size: 14px;">⏰ Temporary Block Active</h5>
            <p style="margin: 0; color: #7f1d1d; font-size: 13px;">
              I won't forward emails from this sender for 24 hours. After that, 
              forwarding resumes unless you specify otherwise.
            </p>
          </div>
        </div>
        
        <div style="background: #f8fafc; padding: 20px; border: 1px solid #e1e5e9; border-top: none; border-radius: 0 0 12px 12px; text-align: center;">
          <p style="margin: 0; font-size: 12px; color: #6b7280;">
            🤖 <strong>Smart Receipt Forwarder</strong> - Learning from your preferences
          </p>
        </div>
      </div>
    `;
    
    await emailSender.sendEmail(wifeEmail, subject, body);
    console.log("Clarification email sent");
  } catch (error) {
    console.error("Error sending clarification email:", error);
  }
}

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

      // Extract original email info from subject line
      const originalSubject = email.subject.replace("Re: 📧 Receipt Forward: ", "");
      const commands = ReplyParser.parseReply(email.body, { subject: originalSubject });
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
        } else if (command.action === "generic_stop") {
          // Handle generic STOP - temporarily block and ask for clarification
          await handleGenericStop(command, email, originalSubject);
          actionTaken = "Temporarily blocked sender, clarification sent";
        } else if (command.action === "cancel_block") {
          // Handle NEVERMIND - cancel temporary blocks
          const senderInfo = extractSenderFromForwardedEmail(email.body, originalSubject);
          if (senderInfo.email) {
            await PreferenceManager.removeTemporaryBlock(senderInfo.email);
            actionTaken = `Cancelled temporary block for ${senderInfo.email}`;
          } else {
            actionTaken = "Could not identify sender to unblock";
          }
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
