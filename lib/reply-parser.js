// lib/reply-parser.js - Enhanced to handle different STOP commands
export class ReplyParser {
  static parseReply(replyText, originalEmail = null) {
    const text = replyText.toLowerCase().trim();
    const commands = [];

    // Handle just "STOP" without specifying what
    if (this.isGenericStop(text)) {
      commands.push({
        action: "generic_stop",
        message: "Generic stop command - needs clarification",
        originalEmail: originalEmail
      });
      return commands;
    }

    // Parse STOP with specific targets
    const stopMatches = text.match(/stop\s+(\w+)/g);
    if (stopMatches) {
      stopMatches.forEach((match) => {
        const target = match.replace("stop ", "").trim();
        commands.push({ action: "block", type: "senders", value: target });
      });
    }

    // Parse MORE commands (whitelist)
    const moreMatches = text.match(/more\s+(\w+)/g);
    if (moreMatches) {
      moreMatches.forEach((match) => {
        const target = match.replace("more ", "").trim();
        commands.push({ action: "whitelist", value: target });
      });
    }

    // Parse category blocks
    const categories = [
      "restaurants",
      "transportation",
      "retail",
      "subscriptions",
      "amazon",
      "food-delivery",
      "utilities",
      "healthcare",
    ];
    categories.forEach((category) => {
      if (text.includes(`stop ${category}`)) {
        commands.push({ action: "block", type: "categories", value: category });
      }
    });

    // Parse SETTINGS command
    if (text.includes("settings")) {
      commands.push({ action: "settings" });
    }

    // Parse HELP command
    if (text.includes("help") || text.includes("commands")) {
      commands.push({ action: "help" });
    }

    // Parse STOP ALL (nuclear option)
    if (text.includes("stop all") || text.includes("stop everything")) {
      commands.push({ action: "stop_all" });
    }

    // Parse NEVERMIND (cancel temporary blocks)
    if (text.includes("nevermind") || text.includes("never mind") || text.includes("cancel")) {
      commands.push({ action: "cancel_block", originalEmail: originalEmail });
    }

    return commands;
  }

  static isGenericStop(text) {
    // Check if it's just "stop" without any target
    const genericStopPatterns = [
      /^stop\.?$/, // Just "stop" or "stop."
      /^stop!?$/, // "stop" or "stop!"
      /^please stop$/, // "please stop"
      /^stop this$/, // "stop this"
      /^stop these$/, // "stop these"
      /^no more$/, // "no more"
      /^unsubscribe$/, // "unsubscribe"
    ];

    return genericStopPatterns.some((pattern) => pattern.test(text));
  }

  static getHelpMessage() {
    return `
📧 Receipt Forwarder Commands:

🚫 BLOCKING:
• "STOP amazon" - Block Amazon receipts
• "STOP restaurants" - Block restaurant category
• "STOP utilities" - Block utility bills
• "STOP ALL" - Block everything (emergency stop)

✅ ALLOWING:
• "MORE starbucks" - Always forward Starbucks
• "MORE amazon" - Always forward Amazon

ℹ️ INFO:
• "SETTINGS" - View your current preferences
• "HELP" - Show this message

Reply to any forwarded email with these commands!
    `.trim();
  }

  static getSuggestedActionsForSender(senderEmail) {
    // Extract the main part of the sender for suggestions
    const domain = senderEmail.split("@")[1]?.toLowerCase() || "";
    const username = senderEmail.split("@")[0]?.toLowerCase() || "";

    const suggestions = [];

    // Suggest blocking the specific sender
    suggestions.push(`STOP ${username}`);

    // Suggest category blocks based on common patterns
    if (domain.includes("amazon")) {
      suggestions.push("STOP amazon");
    } else if (domain.includes("uber") || domain.includes("lyft")) {
      suggestions.push("STOP transportation");
    } else if (domain.includes("netflix") || domain.includes("spotify")) {
      suggestions.push("STOP subscriptions");
    } else if (domain.includes("restaurant") || username.includes("food")) {
      suggestions.push("STOP restaurants");
    } else if (
      domain.includes("att") ||
      domain.includes("verizon") ||
      domain.includes("comcast")
    ) {
      suggestions.push("STOP utilities");
    }

    return suggestions;
  }
}
