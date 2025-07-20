// pages/api/health.js - Simple health check endpoint
export default async function handler(req, res) {
  res.setHeader('Content-Type', 'application/json');
  res.setHeader('Cache-Control', 'no-cache, no-store, must-revalidate');
  
  if (req.method !== "GET") {
    return res.status(405).json({ 
      success: false,
      error: "Method not allowed",
      timestamp: new Date().toISOString()
    });
  }

  try {
    // Basic environment check
    const envCheck = {
      hasWifeEmail: !!process.env.WIFE_EMAIL,
      hasNotionToken: !!process.env.NOTION_TOKEN,
      hasNotionDatabase: !!process.env.NOTION_DATABASE_ID,
      hasGmailCredentials: !!(process.env.GMAIL_CLIENT_ID && process.env.GMAIL_CLIENT_SECRET),
      hasIcloudCredentials: !!(process.env.ICLOUD_EMAIL && process.env.ICLOUD_PASSWORD),
      hasKvUrl: !!process.env.KV_URL,
    };

    res.status(200).json({
      success: true,
      status: "healthy",
      timestamp: new Date().toISOString(),
      environment: envCheck,
      allRequiredEnvVarsPresent: Object.values(envCheck).every(Boolean)
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: "Health check failed",
      details: error.message,
      timestamp: new Date().toISOString()
    });
  }
}