

// lib/reply-parser.js
export class ReplyParser {
  static parseReply(replyText) {
    const text = replyText.toLowerCase().trim()
    const commands = []

    // Parse STOP commands
    const stopMatches = text.match(/stop\s+(\w+)/g)
    if (stopMatches) {
      stopMatches.forEach(match => {
        const target = match.replace('stop ', '').trim()
        commands.push({ action: 'block', type: 'senders', value: target })
      })
    }

    // Parse MORE commands (whitelist)
    const moreMatches = text.match(/more\s+(\w+)/g)
    if (moreMatches) {
      moreMatches.forEach(match => {
        const target = match.replace('more ', '').trim()
        commands.push({ action: 'whitelist', value: target })
      })
    }

    // Parse category blocks
    const categories = ['restaurants', 'transportation', 'retail', 'subscriptions', 'amazon', 'food-delivery']
    categories.forEach(category => {
      if (text.includes(`stop ${category}`)) {
        commands.push({ action: 'block', type: 'categories', value: category })
      }
    })

    // Parse SETTINGS command
    if (text.includes('settings')) {
      commands.push({ action: 'settings' })
    }

    return commands
  }
}