// README.md
# Receipt Forwarder with Notion Integration

Automatically forwards receipts from your Gmail and iCloud accounts to your wife, with smart filtering, preference learning, and complete Notion dashboard integration.

## 🎯 Features

- 🔍 **Automatic receipt detection** from Gmail and iCloud
- 📧 **Smart forwarding** with beautiful email templates
- 🚫 **Intelligent blocking** based on wife's replies
- 📊 **Complete Notion integration** for monitoring and control
- 📱 **Mobile management** via Notion app
- 🎛️ **Manual overrides** directly in Notion databases
- 🎯 **Manual forwarding system** with custom rules and pattern matching
- 💰 **Spending analysis** with amount extraction
- 🔄 **Real-time sync** between email replies and Notion

## 🚀 Quick Start

1. **Follow SETUP.md** for complete installation guide
2. **Create 5 Notion databases** (Activity, Preferences, Replies, Stats, Manual Forward)
3. **Deploy to Vercel** with environment variables
4. **Test with sample receipt** email

## 🎛️ Control Methods

### Email Commands (for your wife)
Reply to any forwarded email with:
- `STOP amazon` - Block Amazon receipts
- `STOP restaurants` - Block restaurant category  
- `MORE starbucks` - Always forward Starbucks
- `SETTINGS` - View current preferences

### Notion Dashboard
- **Activity Log** - Every email processed with details
- **Preferences** - Add/remove blocks directly
- **Wife's Replies** - Command history and actions taken
- **System Stats** - Performance and health monitoring
- **Manual Forward Rules** - Custom forwarding rules with pattern matching

### Manual Overrides
Add entries directly to Notion Preferences database:
- **Blocked Sender**: Item="amazon", Type="Blocked Sender"
- **Always Forward**: Item="starbucks", Type="Always Forward"
- **Blocked Category**: Item="restaurants", Type="Blocked Category"

### Manual Forward Rules
Create custom forwarding rules in the Manual Forward database:
- **Email Pattern**: "*@amazon.com" (wildcards supported)
- **Subject Pattern**: "*order*" or "receipt"
- **Forward To**: custom-email@example.com
- **Priority**: Lower numbers = higher priority

## 📊 Analytics

Track spending patterns with:
- Amount extraction from receipts
- Category-based analysis
- Monthly/weekly summaries
- Blocked vs forwarded ratios

## 🔧 Customization

**Add your stores** in `lib/receipt-detector.js`:
```javascript
if (from.includes('your-local-store')) return 'Local Shopping'
```

**Adjust schedule** in `vercel.json`:
```json
"schedule": "*/30 * * * *"  // Every 30 minutes
```

## 📱 Mobile Access

- Install Notion mobile app
- Pin your Receipt Dashboard page  
- Get notifications for new activity
- Add blocks on the go

## 🛡️ Privacy & Security

- Uses app passwords, not main credentials
- All data stored in your Notion workspace
- No third-party data sharing
- Full audit trail of all actions

## 📝 License

MIT License - Use freely for personal projects

---

**Need help?** Check SETUP.md for detailed instructions or create an issue.