// lib/manual-forwarder.js
import { GmailClient, ICloudClient, EmailSender } from './email-clients.js'
import { NotionDashboard } from './notion-client.js'
import { PreferenceManager } from './preferences.js'
import { CONFIG } from './config.js'

export class ManualForwarder {
  constructor() {
    this.gmailClient = new GmailClient()
    this.icloudClient = new ICloudClient()
    this.emailSender = new EmailSender()
    this.notion = new NotionDashboard()
  }

  async processManualForwards(since = new Date(Date.now() - 24 * 60 * 60 * 1000)) {
    console.log('Starting manual forward processing...')
    
    try {
      // Get recent emails from both accounts
      const [gmailEmails, icloudEmails] = await Promise.all([
        this.gmailClient.getRecentEmails(since).catch((err) => {
          console.error('Gmail error:', err)
          return []
        }),
        this.icloudClient.getRecentEmails(since).catch((err) => {
          console.error('iCloud error:', err)
          return []
        })
      ])

      const allEmails = [...gmailEmails, ...icloudEmails]
      console.log(`Found ${allEmails.length} emails to process for manual forwarding`)

      // Get already processed emails to avoid duplicates
      const processedEmails = await PreferenceManager.getProcessedEmails('manual_forwards')

      let processedCount = 0
      let forwardedCount = 0
      let failedCount = 0
      let skippedCount = 0

      for (const email of allEmails) {
        // Skip if already processed
        if (processedEmails.includes(email.id)) {
          skippedCount++
          continue
        }

        const rule = await this.notion.findManualForwardRule(email)
        
        if (rule) {
          console.log(`Found matching rule "${rule.name}" for email: ${email.subject}`)
          processedCount++
          
          const success = await this.forwardEmail(email, rule)
          if (success) {
            forwardedCount++
            console.log(`Successfully forwarded via manual rule`)
          } else {
            failedCount++
            console.log(`Failed to forward via manual rule`)
          }
          
          await this.notion.logManualForward(email, rule, success)
        }

        // Mark as processed regardless of whether it matched a rule
        await PreferenceManager.markAsProcessed(email.id, 'manual_forwards')
      }

      console.log(`Manual forward processing complete: ${processedCount} processed, ${forwardedCount} forwarded, ${failedCount} failed`)
      
      return {
        totalEmails: allEmails.length,
        processed: processedCount,
        forwarded: forwardedCount,
        failed: failedCount,
        skipped: skippedCount
      }
    } catch (error) {
      console.error('Manual forward processing error:', error)
      throw error
    }
  }

  async forwardEmail(email, rule) {
    try {
      const forwardSubject = `[Manual Forward] ${email.subject}`
      
      const forwardBody = `
        <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif; max-width: 600px; margin: 0 auto; background: #ffffff;">
          <div style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white; padding: 24px; border-radius: 12px 12px 0 0;">
            <h2 style="margin: 0; font-size: 20px; font-weight: 600;">📬 Manual Forward</h2>
            <p style="margin: 8px 0 0 0; opacity: 0.9; font-size: 14px;">Forwarded via rule: ${rule.name}</p>
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
                <strong style="color: #37352f;">Source:</strong><br>
                <span style="background: #f3f4f6; padding: 2px 8px; border-radius: 4px; color: #374151; font-size: 12px;">${email.source}</span>
              </div>
              <div>
                <strong style="color: #37352f;">Rule:</strong><br>
                <span style="color: #10b981; font-weight: 600;">${rule.name}</span>
              </div>
            </div>
            
            <div style="background: #f9fafb; padding: 16px; border-radius: 8px; border-left: 4px solid #10b981; margin-bottom: 20px;">
              <h4 style="margin: 0 0 8px 0; color: #37352f; font-size: 14px;">Original Subject:</h4>
              <p style="margin: 0; color: #6b7280; font-size: 14px;">${email.subject}</p>
            </div>
            
            <div style="background: #ffffff; border: 1px solid #e5e7eb; border-radius: 8px; padding: 16px; max-height: 300px; overflow-y: auto; font-family: 'SF Mono', Monaco, 'Cascadia Code', monospace; font-size: 13px; line-height: 1.5;">
              ${email.body.substring(0, 2000)}${email.body.length > 2000 ? '...' : ''}
            </div>
          </div>
          
          <div style="background: #f8fafc; padding: 20px; border: 1px solid #e1e5e9; border-top: none; border-radius: 0 0 12px 12px;">
            <h4 style="margin: 0 0 12px 0; color: #37352f; font-size: 14px;">📋 Rule Details</h4>
            <div style="font-size: 13px; color: #6b7280; line-height: 1.6;">
              <strong>Matching Rule:</strong> ${rule.name}<br>
              ${rule.emailPattern ? `• Email Pattern: "${rule.emailPattern}"<br>` : ''}
              ${rule.subjectPattern ? `• Subject Pattern: "${rule.subjectPattern}"<br>` : ''}
              • Priority: ${rule.priority}
            </div>
            
            <div style="margin-top: 20px; padding: 16px; background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%); border-radius: 8px; border-left: 4px solid #22c55e;">
              <div style="display: flex; align-items: center; margin-bottom: 8px;">
                <span style="font-size: 16px; margin-right: 8px;">🎯</span>
                <h5 style="margin: 0; color: #14532d; font-size: 14px; font-weight: 600;">Manual Forward System</h5>
              </div>
              <p style="margin: 0; font-size: 12px; color: #166534; line-height: 1.4;">
                This email was caught by a custom rule you created in your Notion database. The system detected this email 
                might not have been forwarded by the regular receipt detection, so it used your manual rules to ensure you see it.
              </p>
              <div style="margin-top: 8px; font-size: 11px; color: #15803d;">
                ✨ <strong>Manual Catch-All:</strong> Pattern matching → Backup forwarding → Nothing gets missed → Complete coverage
              </div>
            </div>
            
            <div style="margin-top: 20px; padding: 16px; background: linear-gradient(135deg, #fefce8 0%, #fef3c7 100%); border-radius: 8px; border-left: 4px solid #f59e0b;">
              <div style="display: flex; align-items: center; margin-bottom: 8px;">
                <span style="font-size: 16px; margin-right: 8px;">💬</span>
                <h5 style="margin: 0; color: #92400e; font-size: 14px; font-weight: 600;">Need to Make Changes?</h5>
              </div>
              <div style="font-size: 12px; color: #a16207; line-height: 1.4;">
                <strong>Update your rules in Notion:</strong><br>
                • Edit the "${rule.name}" rule to modify patterns<br>
                • Change priority to adjust rule order<br>
                • Set status to "Inactive" to disable<br>
                • Create new rules for different forwarding needs
              </div>
            </div>
            
            <div style="margin-top: 12px; padding-top: 12px; border-top: 1px solid #e5e7eb; font-size: 12px; color: #9ca3af; text-align: center;">
              🎛️ Manage all rules in Notion • 📊 View forwarding analytics • 🤖 Fully automated system
            </div>
          </div>
        </div>
      `

      const success = await this.emailSender.sendEmail(
        process.env.WIFE_EMAIL,
        forwardSubject,
        forwardBody
      )

      return success
    } catch (error) {
      console.error('Forward email error:', error)
      return false
    }
  }

  async processSpecificEmails(emailIds, ruleId = null) {
    console.log(`Processing specific emails: ${emailIds.join(', ')}`)
    
    try {
      const allEmails = await this.getAllRecentEmails()
      const specificEmails = allEmails.filter(email => emailIds.includes(email.id))
      
      let processedCount = 0
      let forwardedCount = 0
      let failedCount = 0

      for (const email of specificEmails) {
        let rule
        
        if (ruleId) {
          const rules = await this.notion.getManualForwardRules()
          rule = rules.find(r => r.id === ruleId)
        } else {
          rule = await this.notion.findManualForwardRule(email)
        }
        
        if (rule) {
          processedCount++
          const success = await this.forwardEmail(email, rule)
          if (success) {
            forwardedCount++
          } else {
            failedCount++
          }
          await this.notion.logManualForward(email, rule, success)
        }
      }

      return {
        processed: processedCount,
        forwarded: forwardedCount,
        failed: failedCount
      }
    } catch (error) {
      console.error('Process specific emails error:', error)
      throw error
    }
  }

  async getAllRecentEmails(since = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000)) {
    const [gmailEmails, icloudEmails] = await Promise.all([
      this.gmailClient.getRecentEmails(since).catch(() => []),
      this.icloudClient.getRecentEmails(since).catch(() => [])
    ])
    
    return [...gmailEmails, ...icloudEmails]
  }
}