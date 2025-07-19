// pages/api/manual-forward.js
import { ManualForwarder } from '../../lib/manual-forwarder.js'
import { NotionDashboard } from '../../lib/notion-client.js'

export default async function handler(req, res) {
  if (req.method !== 'POST' && req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' })
  }

  try {
    const manualForwarder = new ManualForwarder()
    const notion = new NotionDashboard()
    
    // Support both GET and POST requests
    const params = req.method === 'GET' ? req.query : req.body
    const { 
      mode = 'auto',
      emailIds = [],
      ruleId = null,
      hours = 24
    } = params

    let result

    switch (mode) {
      case 'auto':
        // Process all emails from the last X hours using automatic rule matching
        const since = new Date(Date.now() - hours * 60 * 60 * 1000)
        result = await manualForwarder.processManualForwards(since)
        break
      
      case 'specific':
        // Process specific email IDs with optional rule override
        const emailArray = Array.isArray(emailIds) ? emailIds : (emailIds ? emailIds.split(',') : [])
        if (!emailArray || emailArray.length === 0) {
          return res.status(400).json({ error: 'Email IDs required for specific mode' })
        }
        result = await manualForwarder.processSpecificEmails(emailArray, ruleId)
        break
      
      case 'list-rules':
        // Just return the current manual forward rules
        const rules = await notion.getManualForwardRules()
        return res.status(200).json({ 
          success: true, 
          rules,
          timestamp: new Date().toISOString()
        })
      
      case 'list-emails':
        // Return recent emails for manual selection
        const hours_back = hours || 24
        const emails = await manualForwarder.getAllRecentEmails(
          new Date(Date.now() - hours_back * 60 * 60 * 1000)
        )
        return res.status(200).json({
          success: true,
          emails: emails.map(email => ({
            id: email.id,
            subject: email.subject,
            from: email.from,
            date: email.date,
            source: email.source
          })),
          total: emails.length,
          timestamp: new Date().toISOString()
        })
      
      default:
        return res.status(400).json({ error: 'Invalid mode. Use: auto, specific, list-rules, or list-emails' })
    }

    console.log(`Manual forward API completed - Mode: ${mode}, Result:`, result)

    res.status(200).json({
      success: true,
      mode,
      result,
      timestamp: new Date().toISOString()
    })

  } catch (error) {
    console.error('Manual forward API error:', error)
    
    // Log the error to Notion
    try {
      const notion = new NotionDashboard()
      await notion.logActivity(
        { 
          subject: 'Manual Forward API Error', 
          from: 'system', 
          source: 'api' 
        },
        'error',
        error.message
      )
    } catch (logError) {
      console.error('Failed to log error to Notion:', logError)
    }

    res.status(500).json({ 
      error: 'Internal server error', 
      details: error.message,
      timestamp: new Date().toISOString()
    })
  }
}