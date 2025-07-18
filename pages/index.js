
// pages/index.js
export default function Home() {
  return (
    <div style={{ 
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
      padding: '40px',
      textAlign: 'center',
      maxWidth: '600px',
      margin: '0 auto',
      backgroundColor: '#f9fafb',
      minHeight: '100vh'
    }}>
      <div style={{
        backgroundColor: 'white',
        borderRadius: '12px',
        padding: '40px',
        boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)'
      }}>
        <h1 style={{ fontSize: '32px', marginBottom: '16px', color: '#1f2937' }}>📧 Receipt Forwarder</h1>
        <p style={{ fontSize: '18px', color: '#6b7280', marginBottom: '32px' }}>
          Your receipt forwarding system is running automatically every 15 minutes.
        </p>
        
        <div style={{ 
          background: '#f0f9ff', 
          border: '1px solid #0ea5e9', 
          borderRadius: '12px', 
          padding: '24px',
          marginBottom: '32px'
        }}>
          <h3 style={{ margin: '0 0 16px 0', color: '#0c4a6e' }}>📊 View Your Notion Dashboard</h3>
          <p style={{ margin: '0 0 20px 0', color: '#075985' }}>
            All activity, preferences, and controls are available in your Notion workspace.
          </p>
          <a 
            href={`https://notion.so`}
            target="_blank"
            rel="noopener noreferrer"
            style={{
              display: 'inline-block',
              background: '#000000',
              color: 'white',
              padding: '12px 24px',
              borderRadius: '8px',
              textDecoration: 'none',
              fontWeight: '500'
            }}
          >
            🚀 Open Notion Dashboard
          </a>
        </div>

        <div style={{ 
          background: '#ecfdf5', 
          border: '1px solid #10b981', 
          borderRadius: '12px', 
          padding: '20px',
          textAlign: 'left',
          marginBottom: '32px'
        }}>
          <h4 style={{ margin: '0 0 12px 0', color: '#059669' }}>✅ System Status</h4>
          <ul style={{ margin: 0, paddingLeft: '20px', color: '#065f46' }}>
            <li>Checking emails every 15 minutes</li>
            <li>Processing wife's replies every 5 minutes</li>
            <li>Logging all activity to Notion</li>
            <li>Learning from preferences automatically</li>
          </ul>
        </div>

        <div style={{
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          gap: '16px'
        }}>
          <button
            onClick={async () => {
              try {
                const response = await fetch('/api/check-emails')
                const result = await response.json()
                alert(`✅ Manual check complete!\nForwarded: ${result.forwarded}\nSkipped: ${result.skipped}`)
              } catch (error) {
                alert('❌ Manual check failed')
              }
            }}
            style={{
              padding: '12px 20px',
              background: '#3b82f6',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              cursor: 'pointer',
              fontWeight: '500'
            }}
          >
            🔄 Manual Check
          </button>
          
          <button
            onClick={async () => {
              try {
                const response = await fetch('/api/manual-check', { method: 'POST' })
                const result = await response.json()
                alert(`📧 Found ${result.receiptsFound} receipts out of ${result.totalEmails} emails`)
              } catch (error) {
                alert('❌ Analysis failed')
              }
            }}
            style={{
              padding: '12px 20px',
              background: '#10b981',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              cursor: 'pointer',
              fontWeight: '500'
            }}
          >
            📊 Analyze Emails
          </button>
        </div>

        <div style={{ 
          marginTop: '32px',
          padding: '20px',
          background: '#fef3c7',
          border: '1px solid #f59e0b',
          borderRadius: '8px',
          textAlign: 'left'
        }}>
          <h4 style={{ margin: '0 0 12px 0', color: '#92400e' }}>💡 Quick Commands for Your Wife</h4>
          <div style={{ fontSize: '14px', color: '#78350f' }}>
            She can reply to any forwarded email with:<br/>
            • <code style={{ background: '#fbbf24', padding: '2px 4px', borderRadius: '3px' }}>STOP amazon</code> - Block Amazon receipts<br/>
            • <code style={{ background: '#fbbf24', padding: '2px 4px', borderRadius: '3px' }}>STOP restaurants</code> - Block restaurant category<br/>
            • <code style={{ background: '#fbbf24', padding: '2px 4px', borderRadius: '3px' }}>MORE starbucks</code> - Always forward Starbucks<br/>
            • <code style={{ background: '#fbbf24', padding: '2px 4px', borderRadius: '3px' }}>SETTINGS</code> - View preferences
          </div>
        </div>
      </div>
    </div>
  )
}