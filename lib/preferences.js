

// lib/preferences.js
import { kv } from '@vercel/kv'

export class PreferenceManager {
  static async getBlocklist() {
    const blocklist = await kv.get('blocklist') || {
      senders: [],
      categories: [],
      keywords: [],
      whitelist: []
    }
    return blocklist
  }

  static async addToBlocklist(type, value) {
    const blocklist = await this.getBlocklist()
    const cleanValue = value.toLowerCase().trim()
    
    if (!blocklist[type].includes(cleanValue)) {
      blocklist[type].push(cleanValue)
      await kv.set('blocklist', blocklist)
    }
  }

  static async removeFromBlocklist(type, value) {
    const blocklist = await this.getBlocklist()
    const cleanValue = value.toLowerCase().trim()
    blocklist[type] = blocklist[type].filter(item => item !== cleanValue)
    await kv.set('blocklist', blocklist)
  }

  static async addToWhitelist(value) {
    const blocklist = await this.getBlocklist()
    const cleanValue = value.toLowerCase().trim()
    
    if (!blocklist.whitelist.includes(cleanValue)) {
      blocklist.whitelist.push(cleanValue)
      await kv.set('blocklist', blocklist)
    }
  }

  static async isBlocked(email) {
    const blocklist = await this.getBlocklist()
    return this.isBlockedWithPreferences(email, blocklist)
  }

  static async isBlockedWithPreferences(email, preferences) {
    const from = (email.from || '').toLowerCase()
    const subject = (email.subject || '').toLowerCase()
    
    // Check whitelist first (always forward these)
    if (preferences.whitelist && preferences.whitelist.some(sender => from.includes(sender))) {
      return false
    }
    
    // Check blocked senders
    if (preferences.senders && preferences.senders.some(sender => from.includes(sender))) return true
    
    // Check blocked categories
    const category = ReceiptDetector.categorizeReceipt(email)
    if (preferences.categories && preferences.categories.includes(category)) return true
    
    // Check blocked keywords
    if (preferences.keywords && preferences.keywords.some(keyword => subject.includes(keyword))) return true
    
    return false
  }

  static async getProcessedEmails(type = 'emails') {
    const key = type === 'emails' ? 'processed_emails' : 'processed_replies'
    return await kv.get(key) || []
  }

  static async markAsProcessed(emailId, type = 'emails') {
    const key = type === 'emails' ? 'processed_emails' : 'processed_replies'
    const processed = await this.getProcessedEmails(type)
    processed.push(emailId)
    
    // Keep only last 1000 processed emails
    if (processed.length > 1000) {
      processed.splice(0, processed.length - 1000)
    }
    
    await kv.set(key, processed)
  }
}