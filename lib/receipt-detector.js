
// lib/receipt-detector.js
import { CONFIG } from './config.js'

export class ReceiptDetector {
  static isReceipt(email) {
    const subject = (email.subject || '').toLowerCase()
    const body = (email.body || '').toLowerCase()
    const from = (email.from || '').toLowerCase()

    // Check for receipt keywords
    const hasReceiptKeywords = CONFIG.RECEIPT_KEYWORDS.some(keyword => 
      subject.includes(keyword) || body.includes(keyword)
    )

    // Check for known receipt senders
    const isReceiptSender = CONFIG.RECEIPT_SENDERS.some(sender => 
      from.includes(sender)
    )

    // Additional patterns
    const hasOrderNumber = /order[\s#]+\d+/i.test(subject + body)
    const hasAmount = /\$\d+\.\d{2}/.test(body)
    const hasInvoiceNumber = /invoice[\s#]+\d+/i.test(subject + body)
    
    return hasReceiptKeywords || isReceiptSender || (hasOrderNumber && hasAmount) || hasInvoiceNumber
  }

  static categorizeReceipt(email) {
    const from = (email.from || '').toLowerCase()
    const subject = (email.subject || '').toLowerCase()
    
    if (from.includes('amazon') || from.includes('aws')) return 'amazon'
    if (from.includes('uber') || from.includes('lyft')) return 'transportation'
    if (from.includes('doordash') || from.includes('grubhub')) return 'food-delivery'
    if (from.includes('starbucks') || from.includes('mcdonalds')) return 'restaurants'
    if (from.includes('walmart') || from.includes('target') || from.includes('costco')) return 'retail'
    if (from.includes('netflix') || from.includes('spotify')) return 'subscriptions'
    if (from.includes('paypal') || from.includes('venmo')) return 'payments'
    
    return 'other'
  }
}