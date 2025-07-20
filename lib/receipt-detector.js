// lib/receipt-detector.js - Much Smarter Receipt Detection
import { CONFIG } from "./config";

export class ReceiptDetector {
  static isReceipt(email) {
    const subject = (email.subject || "").toLowerCase();
    const body = (email.body || "").toLowerCase();
    const from = (email.from || "").toLowerCase();

    // STEP 0: EXCLUDE reply emails and forwards first
    if (this.isReplyOrForward(subject, from)) {
      console.log(`🚫 Excluded reply/forward email: ${email.subject}`);
      return false;
    }

    // STEP 1: HARD EXCLUDE spam/promotional emails
    if (this.isPromotionalEmail(subject, body, from)) {
      console.log(`🚫 Excluded promotional email: ${email.subject}`);
      return false;
    }

    // STEP 1.5: EXCLUDE shipping notifications (not receipts)
    if (this.isShippingNotification(subject, body, from)) {
      console.log(`🚫 Excluded shipping notification: ${email.subject}`);
      return false;
    }

    // STEP 2: Check for strong receipt indicators
    const strongIndicators = this.hasStrongReceiptIndicators(subject, body);
    if (strongIndicators) {
      console.log(`✅ Strong receipt indicators found: ${email.subject}`);
      return true;
    }

    // STEP 3: Check for transactional patterns (order + amount + confirmation)
    const transactionalScore = this.calculateTransactionalScore(
      subject,
      body,
      from
    );
    if (transactionalScore >= 3) {
      console.log(
        `✅ High transactional score (${transactionalScore}): ${email.subject}`
      );
      return true;
    }

    // STEP 4: Known receipt senders with transaction confirmation
    if (
      this.isKnownReceiptSender(from) &&
      this.hasTransactionConfirmation(subject, body)
    ) {
      console.log(`✅ Known sender with transaction: ${email.subject}`);
      return true;
    }

    console.log(`❌ Not a receipt: ${email.subject}`);
    return false;
  }

  static isReplyOrForward(subject, from) {
    // Check for reply patterns in subject
    const replyPatterns = [
      /^re:\s*/i, // "Re: "
      /^fwd?:\s*/i, // "Fwd: " or "Fw: "
      /^fw:\s*/i, // "Fw: "
      /^forward:\s*/i, // "Forward: "
      /\[fwd\]/i, // "[FWD]"
      /\(fwd\)/i, // "(FWD)"
    ];

    const hasReplySubject = replyPatterns.some((pattern) =>
      pattern.test(subject)
    );

    // Check if from your wife's email (replies to forwarded receipts)
    const isFromWife = from.includes(
      process.env.WIFE_EMAIL?.toLowerCase() || "your-wife@email.com"
    );

    // Check if from your own email addresses (replies from your accounts)
    const yourEmails = [
      process.env.GMAIL_EMAIL?.toLowerCase(),
      process.env.ICLOUD_EMAIL?.toLowerCase(),
      process.env.SENDER_EMAIL?.toLowerCase(),
    ].filter(Boolean);

    const isFromYou = yourEmails.some((email) => from.includes(email));

    return hasReplySubject || isFromWife || isFromYou;
  }

  static isShippingNotification(subject, body, from) {
    // Check for shipping-specific email addresses first (most reliable)
    const shippingEmailPatterns = [
      /shipment-tracking@amazon\.com/i,
      /ship-confirm@amazon\.com/i,
      /shipping@amazon\.com/i,
      /delivery@amazon\.com/i,
      /tracking@amazon\.com/i,
      /shipment@amazon\.com/i,
      /logistics@amazon\.com/i,
      /fulfillment@amazon\.com/i,
      /shipping-/i, // catches various shipping- prefixed emails
      /delivery-/i, // catches various delivery- prefixed emails
      /tracking-/i, // catches various tracking- prefixed emails
      /shipment-/i, // catches various shipment- prefixed emails
      
      // Other carriers
      /tracking@ups\.com/i,
      /delivery@fedex\.com/i,
      /tracking@usps\.com/i,
      /shipment@dhl\.com/i,
    ];

    // If from a known shipping email address, it's definitely a shipping notification
    const isFromShippingAddress = shippingEmailPatterns.some(pattern => pattern.test(from));
    if (isFromShippingAddress) {
      return true;
    }

    // Shipping/delivery notification patterns (NOT receipts)
    const shippingPatterns = [
      // Amazon shipping patterns
      /your\s+.*\s+(has\s+)?shipped/i,
      /shipped\s+today/i,
      /out\s+for\s+delivery/i,
      /delivered/i,
      /delivery\s+update/i,
      /package\s+delivered/i,
      /package\s+update/i,
      /shipment\s+notification/i,
      /tracking\s+information/i,
      /track\s+your\s+package/i,
      /delivery\s+notification/i,
      /shipment\s+delivered/i,
      /order.*shipped/i,
      /item.*shipped/i,
      /package.*shipped/i,
      
      // Delivery status updates
      /delivery\s+attempt/i,
      /delivery\s+rescheduled/i,
      /delivery\s+delayed/i,
      /package\s+is\s+on\s+the\s+way/i,
      /arriving\s+today/i,
      /arriving\s+tomorrow/i,
      /expected\s+delivery/i,
      /estimated\s+delivery/i,
      
      // Carrier notifications
      /ups\s+delivery/i,
      /fedex\s+delivery/i,
      /usps\s+delivery/i,
      /amazon\s+delivery/i,
      /dhl\s+delivery/i,
      
      // Amazon-specific shipping language
      /your\s+amazon.*order/i,
      /amazon.*shipment/i,
      /preparing\s+to\s+ship/i,
      /now\s+shipped/i,
      /has\s+been\s+shipped/i,
      /will\s+arrive/i,
    ];

    const text = `${subject} ${body}`.toLowerCase();
    
    // Check if it matches shipping patterns
    const hasShippingPattern = shippingPatterns.some(pattern => pattern.test(text));
    
    if (!hasShippingPattern) return false;

    // Additional confirmation - must NOT have purchase/payment indicators
    const purchaseIndicators = [
      /order\s+confirmation/i,
      /purchase\s+confirmation/i,
      /payment\s+confirmation/i,
      /receipt/i,
      /invoice/i,
      /charged/i,
      /payment\s+received/i,
      /total.*\$\d+/i,
      /amount.*\$\d+/i,
      /order\s+total/i,
      /subtotal/i,
      /tax.*\$\d+/i,
      /order\s+placed/i,
      /thank\s+you\s+for.*order/i,
    ];

    const hasPurchaseIndicators = purchaseIndicators.some(pattern => pattern.test(text));
    
    // It's a shipping notification if it has shipping patterns but NO purchase indicators
    return hasShippingPattern && !hasPurchaseIndicators;
  }

  static isPromotionalEmail(subject, body, from) {
    // Promotional/marketing keywords that indicate spam
    const promotionalKeywords = [
      "sale",
      "discount",
      "coupon",
      "deal",
      "deals",
      "offer",
      "promotion",
      "promo",
      "save",
      "savings",
      "off",
      "clearance",
      "limited time",
      "hurry",
      "newsletter",
      "weekly ad",
      "special offer",
      "flash sale",
      "free shipping",
      "member exclusive",
      "subscriber",
      "unsubscribe",
      "marketing",
      "browse",
      "shop now",
      "check out",
      "new arrivals",
      "trending",
      "bestseller",
      "featured",
      "recommended",
      "catalog",
      "circular",
      "black friday",
      "cyber monday",
      "holiday sale",
      "back to school",
      "rewards program",
      "loyalty",
      "points earned",
      "cashback earned",
      "gift card",
      "sweepstakes",
      "contest",
      "giveaway",
      "win",
      "personalized",
      "just for you",
      "based on your",
      "you might like",

      // Gaming/deals specific (like Xbox Deals)
      "weekly digest",
      "daily digest",
      "roundup",
      "this week",
      "new releases",
      "best deals",
      "top deals",
      "hot deals",
      "price drop",
      "discounted",
      "on sale",
      "reduced price",
      "lowest price",
      "price alert",
      "wishlist",
      "watch list",
      "compare prices",
      "deal alert",

      // Newsletter patterns
      "digest",
      "update",
      "news",
      "updates",
      "latest",
      "recent",
      "weekly",
      "monthly",
      "daily",
      "edition",
      "issue",
      "curated",
      "handpicked",
      "selected",
      "picks",

      // Marketing action words
      "discover",
      "explore",
      "find",
      "search",
      "browse",
      "view all",
      "see more",
      "learn more",
      "read more",
      "get started",
      "sign up",
      "join",
      "register",
      "download",
      "try",

      // Promotional urgency
      "expires",
      "ending",
      "last chance",
      "final",
      "closing",
      "while supplies last",
      "limited quantity",
      "almost gone",
    ];

    // Check subject for promotional content (more weight on subject)
    const hasPromoSubject = promotionalKeywords.some((keyword) =>
      subject.includes(keyword)
    );

    // Check body for promotional content
    const hasPromoBody = promotionalKeywords.some((keyword) =>
      body.includes(keyword)
    );

    // Check for marketing email patterns
    const marketingPatterns = [
      /\d+%\s*off/i, // "20% off"
      /save\s*\$\d+/i, // "save $10"
      /free\s*shipping/i, // "free shipping"
      /limited\s*time/i, // "limited time"
      /act\s*now/i, // "act now"
      /shop\s*now/i, // "shop now"
      /don't\s*miss/i, // "don't miss"
      /hurry/i, // "hurry"
      /ends\s*(soon|today)/i, // "ends soon/today"
      /check\s*this\s*week/i, // "check this week"
      /new\s*discounts/i, // "new discounts"
      /best\s*deals/i, // "best deals"
      /weekly\s*digest/i, // "weekly digest"
      /\+\d+\s*this\s*week/i, // "+1662 this week"
      /deals?\s*weekly/i, // "deals weekly"
      /price\s*drop/i, // "price drop"
      /now\s*\$\d+/i, // "now $19.99"
    ];

    const hasMarketingPattern = marketingPatterns.some(
      (pattern) => pattern.test(subject) || pattern.test(body)
    );

    // Check for excessive tracking/marketing links
    const trackingPatterns = [
      /awstrack\.me/i,
      /click\./i,
      /track\./i,
      /utm_/i,
      /newsletter/i,
      /unsubscribe/i,
    ];

    const hasTrackingLinks = trackingPatterns.some((pattern) =>
      body.includes(pattern.source.replace(/[\/\\]/g, ""))
    );

    // Gaming/deals site patterns
    const dealsPatterns = [
      /deals?\s*net/i, // "xbdeals.net"
      /deals?\s*com/i, // "gamedeals.com"
      /bargain/i, // bargain sites
      /slickdeals/i, // slickdeals
      /reddit.*deals/i, // reddit deals
      /steam.*sale/i, // steam sales
      /game.*deals/i, // game deals
    ];

    const isDealsWebsite = dealsPatterns.some(
      (pattern) =>
        pattern.test(from) || pattern.test(subject) || pattern.test(body)
    );

    return (
      hasPromoSubject ||
      hasPromoBody ||
      hasMarketingPattern ||
      hasTrackingLinks ||
      isDealsWebsite
    );
  }

  static hasStrongReceiptIndicators(subject, body) {
    // These are STRONG indicators of actual receipts (removed shipping-only terms)
    const strongKeywords = [
      "receipt",
      "invoice",
      "order confirmation",
      "payment confirmation",
      "purchase confirmation",
      "order complete",
      "payment received",
      "order summary",
      "order placed",
      "billing statement",
      "account statement",
      "thank you for your order",
      "order total",
      "amount charged",
    ];

    // Must have strong keyword AND supporting evidence
    const hasStrongKeyword = strongKeywords.some(
      (keyword) => subject.includes(keyword) || body.includes(keyword)
    );

    if (!hasStrongKeyword) return false;

    // Supporting evidence for real receipts
    const supportingEvidence = [
      /order\s*#?\s*[a-z0-9\-]{6,}/i, // Order number
      /invoice\s*#?\s*[a-z0-9\-]{6,}/i, // Invoice number
      /transaction\s*#?\s*[a-z0-9\-]{6,}/i, // Transaction ID
      /tracking\s*#?\s*[a-z0-9\-]{8,}/i, // Tracking number
      /\$[0-9,]+\.[0-9]{2}/, // Dollar amount
      /total:?\s*\$[0-9,]+\.[0-9]{2}/i, // Total amount
      /amount:?\s*\$[0-9,]+\.[0-9]{2}/i, // Amount
      /paid:?\s*\$[0-9,]+\.[0-9]{2}/i, // Paid amount
    ];

    return supportingEvidence.some((pattern) =>
      pattern.test(subject + " " + body)
    );
  }

  static calculateTransactionalScore(subject, body, from) {
    let score = 0;
    const text = subject + " " + body + " " + from;

    // +1 for each transactional indicator
    const indicators = [
      { pattern: /order\s*#?\s*[a-z0-9\-]{6,}/i, points: 2 }, // Order number (strong)
      { pattern: /\$[0-9,]+\.[0-9]{2}/, points: 2 }, // Dollar amount (strong)
      { pattern: /thank\s*you\s*for\s*(your\s*)?(order|purchase)/i, points: 2 }, // Thank you
      { pattern: /invoice\s*#?\s*[a-z0-9\-]{6,}/i, points: 2 }, // Invoice number
      { pattern: /transaction/i, points: 1 }, // Transaction
      { pattern: /payment/i, points: 1 }, // Payment
      { pattern: /billing/i, points: 1 }, // Billing
      { pattern: /statement/i, points: 1 }, // Statement
      { pattern: /account\s*balance/i, points: 1 }, // Account balance
      { pattern: /due\s*date/i, points: 1 }, // Due date
      { pattern: /autopay/i, points: 1 }, // Autopay
      { pattern: /direct\s*debit/i, points: 1 }, // Direct debit
    ];

    indicators.forEach((indicator) => {
      if (indicator.pattern.test(text)) {
        score += indicator.points;
      }
    });

    return score;
  }

  static isKnownReceiptSender(from) {
    // Only the most reliable receipt senders
    const reliableReceiptSenders = [
      "amazon.com",
      "amazon.co", 
      "amazonses.com",
      "auto-confirm@amazon.com",
      "order-update@amazon.com",
      "digital-no-reply@amazon.com",
      "payments-messages@amazon.com",
      "paypal.com",
      "paypal-communications.com",
      "stripe.com",
      "square.com",
      "apple.com",
      "itunes.com",
      "google.com",
      "googlepayments.com",
      "microsoft.com",
      "xbox.com",
      "uber.com",
      "lyft.com",
      "doordash.com",
      "grubhub.com",
      "instacart.com",
      "shipt.com",
    ];

    return reliableReceiptSenders.some((sender) => from.includes(sender));
  }

  static hasTransactionConfirmation(subject, body) {
    const confirmationPatterns = [
      /confirmation/i,
      /receipt/i,
      /order\s*#/i,
      /invoice/i,
      /payment/i,
      /charged/i,
      /bill/i,
      /statement/i,
      /\$[0-9,]+\.[0-9]{2}/,
    ];

    return confirmationPatterns.some(
      (pattern) => pattern.test(subject) || pattern.test(body)
    );
  }

  static categorizeReceipt(email) {
    const from = (email.from || "").toLowerCase();
    const subject = (email.subject || "").toLowerCase();

    // More specific categorization
    if (from.includes("amazon") || from.includes("aws")) return "amazon";
    if (from.includes("uber") || from.includes("lyft")) return "transportation";
    if (
      from.includes("doordash") ||
      from.includes("grubhub") ||
      from.includes("ubereats")
    )
      return "food-delivery";
    if (
      from.includes("starbucks") ||
      from.includes("mcdonalds") ||
      from.includes("subway")
    )
      return "restaurants";
    if (
      from.includes("walmart") ||
      from.includes("target") ||
      from.includes("costco")
    )
      return "retail";
    if (
      from.includes("netflix") ||
      from.includes("spotify") ||
      from.includes("adobe")
    )
      return "subscriptions";
    if (
      from.includes("paypal") ||
      from.includes("venmo") ||
      from.includes("square")
    )
      return "payments";

    // Utility detection
    if (
      from.includes("att") ||
      from.includes("verizon") ||
      from.includes("comcast") ||
      from.includes("xfinity") ||
      from.includes("spectrum")
    )
      return "utilities";

    // Healthcare
    if (
      from.includes("cvs") ||
      from.includes("walgreens") ||
      from.includes("pharmacy") ||
      subject.includes("prescription") ||
      subject.includes("copay")
    )
      return "healthcare";

    // Government/official
    if (
      from.includes("irs") ||
      from.includes("dmv") ||
      from.includes("gov") ||
      subject.includes("tax") ||
      subject.includes("license")
    )
      return "government";

    return "other";
  }

  // Helper method to get detection confidence
  static getDetectionConfidence(email) {
    const subject = (email.subject || "").toLowerCase();
    const body = (email.body || "").toLowerCase();
    const from = (email.from || "").toLowerCase();

    if (this.isPromotionalEmail(subject, body, from)) return 0;

    let confidence = 0;

    if (this.hasStrongReceiptIndicators(subject, body)) confidence += 40;

    const transactionScore = this.calculateTransactionalScore(
      subject,
      body,
      from
    );
    confidence += transactionScore * 10;

    if (this.isKnownReceiptSender(from)) confidence += 20;

    if (this.hasTransactionConfirmation(subject, body)) confidence += 10;

    return Math.min(confidence, 100);
  }
}
