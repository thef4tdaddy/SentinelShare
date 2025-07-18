
// lib/notion-client.js
import { Client } from '@notionhq/client'

export class NotionDashboard {
  constructor() {
    this.notion = new Client({
      auth: process.env.NOTION_TOKEN
    })
    this.databaseIds = {
      activity: process.env.NOTION_ACTIVITY_DB,
      preferences: process.env.NOTION_PREFERENCES_DB,
      replies: process.env.NOTION_REPLIES_DB,
      stats: process.env.NOTION_STATS_DB
    }
  }

  async logActivity(email, action, reason = null) {
    try {
      await this.notion.pages.create({
        parent: { database_id: this.databaseIds.activity },
        properties: {
          'Subject': {
            title: [{ text: { content: this.truncateText(email.subject || 'Unknown', 100) } }]
          },
          'From': {
            rich_text: [{ text: { content: this.truncateText(email.from || 'Unknown', 100) } }]
          },
          'Action': {
            select: { name: action }
          },
          'Source': {
            select: { name: email.source || 'unknown' }
          },
          'Category': {
            select: { name: this.categorizeEmail(email) }
          },
          'Reason': {
            rich_text: [{ text: { content: this.truncateText(reason || '', 100) } }]
          },
          'Date': {
            date: { start: new Date().toISOString() }
          },
          'Amount': {
            number: this.extractAmount(email.body || email.subject || '')
          }
        }
      })
    } catch (error) {
      console.error('Notion activity log error:', error)
    }
  }

  async logReply(originalSubject, command, actionTaken) {
    try {
      await this.notion.pages.create({
        parent: { database_id: this.databaseIds.replies },
        properties: {
          'Original Email': {
            title: [{ text: { content: this.truncateText(originalSubject, 100) } }]
          },
          'Command': {
            rich_text: [{ text: { content: this.truncateText(command, 200) } }]
          },
          'Action Taken': {
            rich_text: [{ text: { content: this.truncateText(actionTaken, 200) } }]
          },
          'Date': {
            date: { start: new Date().toISOString() }
          },
          'Command Type': {
            select: { name: this.parseCommandType(command) }
          }
        }
      })
    } catch (error) {
      console.error('Notion reply log error:', error)
    }
  }

  async updateStats(stats) {
    try {
      const today = new Date().toISOString().split('T')[0]
      
      // Try to find today's stats entry first
      const existing = await this.notion.databases.query({
        database_id: this.databaseIds.stats,
        filter: {
          property: 'Date',
          title: {
            equals: today
          }
        }
      })

      if (existing.results.length > 0) {
        // Update existing entry
        await this.notion.pages.update({
          page_id: existing.results[0].id,
          properties: {
            'Emails Checked': { number: stats.processed || 0 },
            'Forwarded': { number: stats.forwarded || 0 },
            'Blocked': { number: stats.skipped || 0 },
            'Gmail Status': { select: { name: stats.gmailConnected ? 'Connected' : 'Disconnected' } },
            'iCloud Status': { select: { name: stats.icloudConnected ? 'Connected' : 'Disconnected' } },
            'Last Check': { date: { start: new Date().toISOString() } }
          }
        })
      } else {
        // Create new entry
        await this.notion.pages.create({
          parent: { database_id: this.databaseIds.stats },
          properties: {
            'Date': {
              title: [{ text: { content: today } }]
            },
            'Emails Checked': { number: stats.processed || 0 },
            'Forwarded': { number: stats.forwarded || 0 },
            'Blocked': { number: stats.skipped || 0 },
            'Gmail Status': { select: { name: stats.gmailConnected ? 'Connected' : 'Disconnected' } },
            'iCloud Status': { select: { name: stats.icloudConnected ? 'Connected' : 'Disconnected' } },
            'Last Check': { date: { start: new Date().toISOString() } }
          }
        })
      }
    } catch (error) {
      console.error('Notion stats update error:', error)
    }
  }

  async getPreferencesFromNotion() {
    try {
      const response = await this.notion.databases.query({
        database_id: this.databaseIds.preferences,
        filter: {
          property: 'Status',
          select: {
            equals: 'Active'
          }
        }
      })

      const preferences = {
        senders: [],
        categories: [],
        whitelist: []
      }

      for (const page of response.results) {
        const item = page.properties.Item?.title?.[0]?.text?.content
        const type = page.properties.Type?.select?.name

        if (item && type) {
          if (type === 'Blocked Sender') {
            preferences.senders.push(item.toLowerCase())
          } else if (type === 'Blocked Category') {
            preferences.categories.push(item.toLowerCase())
          } else if (type === 'Always Forward') {
            preferences.whitelist.push(item.toLowerCase())
          }
        }
      }

      return preferences
    } catch (error) {
      console.error('Notion preferences read error:', error)
      return { senders: [], categories: [], whitelist: [] }
    }
  }

  async updatePreferences(preferences) {
    try {
      // Get existing preferences
      const existing = await this.notion.databases.query({
        database_id: this.databaseIds.preferences
      })

      // Archive old entries
      for (const page of existing.results) {
        await this.notion.pages.update({
          page_id: page.id,
          archived: true
        })
      }

      // Add current blocked senders
      for (const sender of preferences.senders || []) {
        await this.notion.pages.create({
          parent: { database_id: this.databaseIds.preferences },
          properties: {
            'Item': {
              title: [{ text: { content: sender } }]
            },
            'Type': {
              select: { name: 'Blocked Sender' }
            },
            'Status': {
              select: { name: 'Active' }
            },
            'Date Added': {
              date: { start: new Date().toISOString() }
            }
          }
        })
      }

      // Add blocked categories
      for (const category of preferences.categories || []) {
        await this.notion.pages.create({
          parent: { database_id: this.databaseIds.preferences },
          properties: {
            'Item': {
              title: [{ text: { content: category } }]
            },
            'Type': {
              select: { name: 'Blocked Category' }
            },
            'Status': {
              select: { name: 'Active' }
            },
            'Date Added': {
              date: { start: new Date().toISOString() }
            }
          }
        })
      }

      // Add whitelisted items
      for (const item of preferences.whitelist || []) {
        await this.notion.pages.create({
          parent: { database_id: this.databaseIds.preferences },
          properties: {
            'Item': {
              title: [{ text: { content: item } }]
            },
            'Type': {
              select: { name: 'Always Forward' }
            },
            'Status': {
              select: { name: 'Active' }
            },
            'Date Added': {
              date: { start: new Date().toISOString() }
            }
          }
        })
      }
    } catch (error) {
      console.error('Notion preferences update error:', error)
    }
  }

  categorizeEmail(email) {
    const from = (email.from || '').toLowerCase()
    const subject = (email.subject || '').toLowerCase()
    
    if (from.includes('amazon') || from.includes('aws')) return 'Amazon'
    if (from.includes('uber') || from.includes('lyft')) return 'Transportation'
    if (from.includes('doordash') || from.includes('grubhub') || from.includes('ubereats')) return 'Food Delivery'
    if (from.includes('starbucks') || from.includes('mcdonalds') || from.includes('subway')) return 'Restaurants'
    if (from.includes('walmart') || from.includes('target') || from.includes('costco')) return 'Retail'
    if (from.includes('netflix') || from.includes('spotify') || from.includes('adobe')) return 'Subscriptions'
    if (from.includes('paypal') || from.includes('venmo') || from.includes('square')) return 'Payments'
    
    return 'Other'
  }

  extractAmount(text) {
    const match = text.match(/\$([0-9,]+\.?[0-9]*)/);
    if (match) {
      return parseFloat(match[1].replace(',', ''));
    }
    return null;
  }

  parseCommandType(command) {
    const cmd = command.toLowerCase()
    if (cmd.includes('stop')) return 'Block'
    if (cmd.includes('more')) return 'Whitelist'
    if (cmd.includes('settings')) return 'Settings Request'
    return 'Other'
  }

  truncateText(text, maxLength) {
    if (!text) return ''
    return text.length > maxLength ? text.substring(0, maxLength - 3) + '...' : text
  }
}