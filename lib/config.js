// lib/config.js
export const CONFIG = {
  // Receipt detection patterns
  RECEIPT_KEYWORDS: [
    'receipt', 'invoice', 'order confirmation', 'payment confirmation',
    'purchase confirmation', 'transaction', 'billing', 'statement',
    'order summary', 'thank you for your order', 'payment received',
    'order complete', 'delivery confirmation', 'order placed'
  ],
  
  RECEIPT_SENDERS: [
    'amazon', 'walmart', 'target', 'costco', 'uber', 'lyft',
    'doordash', 'grubhub', 'instacart', 'starbucks', 'mcdonalds',
    'paypal', 'square', 'stripe', 'apple', 'google', 'microsoft',
    'netflix', 'spotify', 'adobe', 'dropbox', 'best buy', 'home depot'
  ],

  // Email templates
  FORWARD_TEMPLATE: {
    subject: '📧 Receipt Forward: {originalSubject}',
    footer: `
    
---
Receipt Auto-Forwarder
Reply with commands to manage your preferences:
• "STOP {sender}" - Block this sender
• "STOP {category}" - Block category (e.g. "STOP restaurants")
• "MORE {sender}" - Always forward from this sender
• "SETTINGS" - View all your preferences
    `
  }
}