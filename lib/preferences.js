// lib/preferences.js - No KV Dependencies
import { ReceiptDetector } from "./receipt-detector";

// Simple in-memory storage (resets on deployment, but Notion is our main storage)
const memoryStore = {
  data: {},
  get(key) {
    return this.data[key] || null;
  },
  set(key, value) {
    this.data[key] = value;
    return true;
  },
};

export class PreferenceManager {
  static async getBlocklist() {
    try {
      const blocklist = memoryStore.get("blocklist") || {
        senders: [],
        categories: [],
        keywords: [],
        whitelist: [],
      };
      return blocklist;
    } catch (error) {
      console.error("Error getting blocklist:", error);
      return {
        senders: [],
        categories: [],
        keywords: [],
        whitelist: [],
      };
    }
  }

  static async addToBlocklist(type, value) {
    try {
      const blocklist = await this.getBlocklist();
      const cleanValue = value.toLowerCase().trim();

      if (!blocklist[type]) {
        blocklist[type] = [];
      }

      if (!blocklist[type].includes(cleanValue)) {
        blocklist[type].push(cleanValue);
        memoryStore.set("blocklist", blocklist);
      }
    } catch (error) {
      console.error("Error adding to blocklist:", error);
    }
  }

  static async removeFromBlocklist(type, value) {
    try {
      const blocklist = await this.getBlocklist();
      const cleanValue = value.toLowerCase().trim();

      if (blocklist[type]) {
        blocklist[type] = blocklist[type].filter((item) => item !== cleanValue);
        memoryStore.set("blocklist", blocklist);
      }
    } catch (error) {
      console.error("Error removing from blocklist:", error);
    }
  }

  static async addToWhitelist(value) {
    try {
      const blocklist = await this.getBlocklist();
      const cleanValue = value.toLowerCase().trim();

      if (!blocklist.whitelist) {
        blocklist.whitelist = [];
      }

      if (!blocklist.whitelist.includes(cleanValue)) {
        blocklist.whitelist.push(cleanValue);
        memoryStore.set("blocklist", blocklist);
      }
    } catch (error) {
      console.error("Error adding to whitelist:", error);
    }
  }

  static async isBlocked(email) {
    try {
      const blocklist = await this.getBlocklist();
      return this.isBlockedWithPreferences(email, blocklist);
    } catch (error) {
      console.error("Error checking if blocked:", error);
      return false;
    }
  }

  static async isBlockedWithPreferences(email, preferences) {
    try {
      const from = (email.from || "").toLowerCase();
      const subject = (email.subject || "").toLowerCase();

      // Check temporary blocks first
      if (await this.isTemporarilyBlocked(from)) {
        return true;
      }

      // Check whitelist first (always forward these)
      if (
        preferences.whitelist &&
        preferences.whitelist.some((sender) => from.includes(sender))
      ) {
        return false;
      }

      // Check blocked senders
      if (
        preferences.senders &&
        preferences.senders.some((sender) => from.includes(sender))
      ) {
        return true;
      }

      // Check blocked categories
      const category = ReceiptDetector.categorizeReceipt(email);
      if (preferences.categories && preferences.categories.includes(category)) {
        return true;
      }

      // Check blocked keywords
      if (
        preferences.keywords &&
        preferences.keywords.some((keyword) => subject.includes(keyword))
      ) {
        return true;
      }

      return false;
    } catch (error) {
      console.error("Error checking blocked with preferences:", error);
      return false;
    }
  }

  static async getProcessedEmails(type = "emails") {
    try {
      // Try to get from Notion first (persistent)
      if (process.env.NOTION_TOKEN && process.env.NOTION_ACTIVITY_DB) {
        try {
          const { NotionDashboard } = await import('./notion-client');
          const notion = new NotionDashboard();
          const processedIds = await notion.getProcessedEmailIds(type);
          if (processedIds && processedIds.length > 0) {
            return processedIds;
          }
        } catch (notionError) {
          console.warn("Failed to get processed emails from Notion, using memory store:", notionError.message);
        }
      }
      
      // Fallback to memory store
      const key = type === "emails" ? "processed_emails" : "processed_replies";
      return memoryStore.get(key) || [];
    } catch (error) {
      console.error("Error getting processed emails:", error);
      return [];
    }
  }

  static async markAsProcessed(emailId, type = "emails") {
    try {
      const key = type === "emails" ? "processed_emails" : "processed_replies";
      const processed = await this.getProcessedEmails(type);

      if (!processed.includes(emailId)) {
        processed.push(emailId);

        // Keep only last 100 processed emails to prevent memory issues
        if (processed.length > 100) {
          processed.splice(0, processed.length - 100);
        }

        memoryStore.set(key, processed);
      }
    } catch (error) {
      console.error("Error marking as processed:", error);
    }
  }

  // Generate consistent ID for email matching
  static generateEmailId(email) {
    if (email.id && email.id.startsWith('gmail-') || email.id.startsWith('icloud-')) {
      // For generated IDs, create consistent ID from content
      return `${email.from}-${email.subject}`.replace(/[^a-zA-Z0-9]/g, '').toLowerCase();
    }
    return email.id; // Use messageId if available
  }

  static async clearProcessedEmails(type = "emails") {
    try {
      const key = type === "emails" ? "processed_emails" : "processed_replies";
      memoryStore.set(key, []);
    } catch (error) {
      console.error("Error clearing processed emails:", error);
    }
  }

  // Temporary blocking (24 hour blocks)
  static async addToTemporaryBlock(senderEmail, reason = "Generic STOP command") {
    try {
      const tempBlocks = memoryStore.get("temporary_blocks") || {};
      const expiresAt = new Date(Date.now() + 24 * 60 * 60 * 1000); // 24 hours
      
      tempBlocks[senderEmail.toLowerCase()] = {
        reason,
        expiresAt: expiresAt.toISOString(),
        createdAt: new Date().toISOString()
      };
      
      memoryStore.set("temporary_blocks", tempBlocks);
      console.log(`Temporarily blocked ${senderEmail} until ${expiresAt.toISOString()}`);
      return true;
    } catch (error) {
      console.error("Error adding temporary block:", error);
      return false;
    }
  }

  static async isTemporarilyBlocked(senderEmail) {
    try {
      const tempBlocks = memoryStore.get("temporary_blocks") || {};
      const block = tempBlocks[senderEmail.toLowerCase()];
      
      if (!block) return false;
      
      // Check if block has expired
      if (new Date() > new Date(block.expiresAt)) {
        // Remove expired block
        delete tempBlocks[senderEmail.toLowerCase()];
        memoryStore.set("temporary_blocks", tempBlocks);
        return false;
      }
      
      return true;
    } catch (error) {
      console.error("Error checking temporary block:", error);
      return false;
    }
  }

  static async getTemporaryBlocks() {
    try {
      const tempBlocks = memoryStore.get("temporary_blocks") || {};
      const now = new Date();
      const active = {};
      
      // Clean up expired blocks and return active ones
      for (const [email, block] of Object.entries(tempBlocks)) {
        if (new Date(block.expiresAt) > now) {
          active[email] = block;
        }
      }
      
      memoryStore.set("temporary_blocks", active);
      return active;
    } catch (error) {
      console.error("Error getting temporary blocks:", error);
      return {};
    }
  }

  static async removeTemporaryBlock(senderEmail) {
    try {
      const tempBlocks = memoryStore.get("temporary_blocks") || {};
      const email = senderEmail.toLowerCase();
      
      if (tempBlocks[email]) {
        delete tempBlocks[email];
        memoryStore.set("temporary_blocks", tempBlocks);
        console.log(`Removed temporary block for ${senderEmail}`);
        return true;
      }
      
      return false;
    } catch (error) {
      console.error("Error removing temporary block:", error);
      return false;
    }
  }

  static async getStats() {
    try {
      const blocklist = await this.getBlocklist();
      const processedEmails = await this.getProcessedEmails();
      const processedReplies = await this.getProcessedEmails("replies");

      return {
        totalBlockedSenders: blocklist.senders.length,
        totalBlockedCategories: blocklist.categories.length,
        totalWhitelisted: blocklist.whitelist.length,
        totalProcessedEmails: processedEmails.length,
        totalProcessedReplies: processedReplies.length,
      };
    } catch (error) {
      console.error("Error getting stats:", error);
      return {
        totalBlockedSenders: 0,
        totalBlockedCategories: 0,
        totalWhitelisted: 0,
        totalProcessedEmails: 0,
        totalProcessedReplies: 0,
      };
    }
  }
}
