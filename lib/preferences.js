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

  static isBlockedWithPreferences(email, preferences) {
    try {
      const from = (email.from || "").toLowerCase();
      const subject = (email.subject || "").toLowerCase();

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

  static async clearProcessedEmails(type = "emails") {
    try {
      const key = type === "emails" ? "processed_emails" : "processed_replies";
      memoryStore.set(key, []);
    } catch (error) {
      console.error("Error clearing processed emails:", error);
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
