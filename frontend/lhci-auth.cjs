/**
 * Puppeteer script to handle login and API mocking for Lighthouse CI.
 * Since we are testing a static build without a backend, we mock the API responses.
 */
module.exports = async (browser, context) => {
  const page = await browser.newPage();
  
  // Enable request interception to mock API calls
  await page.setRequestInterception(true);
  
  page.on('request', request => {
    const url = request.url();
    
    // Mock Login Endpoint
    if (url.endsWith('/api/auth/login')) {
      request.respond({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ status: 'success' })
      });
      return;
    }

    // Mock Auth Check (Me)
    if (url.endsWith('/api/auth/me')) {
      request.respond({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ authenticated: true, email: 'demo@example.com' })
      });
      return;
    }

    // Mock Dashboard Stats/Data (add more if needed to make dashboard render)
    if (url.includes('/api/dashboard')) {
      request.respond({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ 
          stats: { total: 100, forwarded: 80, blocked: 20 },
          recent: []
        })
      });
      return;
    }

    // Default: Continue request (e.g., assets, html)
    request.continue();
  });

  // Navigate to the target URL (Lighthouse passes this)
  await page.goto(context.url);

  // Check if we are on the login page (look for password input)
  const passwordInput = await page.$('input#password');
  
  if (passwordInput) {
    console.log('Detected Login Page. Attempting to log in...');
    
    // Type any password (mock accepts anything)
    await passwordInput.type('mock-password');
    
    // Click submit
    const submitBtn = await page.$('button[type="submit"]');
    await submitBtn.click();
    
    // Wait for navigation or dashboard element
    // Assuming Dashboard has some element like 'h1' "SentinelShare" not "Single-User Access"
    // Or just wait for the URL context to settle? 
    // Usually Lighthouse runs audit on the page *after* this script finishes.
    
    try {
      await page.waitForNavigation({ waitUntil: 'networkidle0', timeout: 5000 });
    } catch {
      console.log('Navigation timeout or already there');
    }
  }

  // Close the extra page we opened (Lighthouse usually uses its own connection, 
  // but for puppeteerScript we assume we manipulate the session).
  // Actually, standard lhci puppeteer script is:
  // module.exports = async (browser, context) => { ... }
  // And we should use the page provided or create one?
  // Docs: "The script exports a function that takes a Browser instance... 
  // You can create new pages... verify state..."
  // BUT Lighthouse takes over the page *after* this?
  // If we utilize `browser`, we might need to rely on the *existing* page if passed?
  // `context` contains `url`.
  
  // Important: close the page we created, ensuring cookies/storage persist if that's how auth works.
  // BUT we are using mocks. Mocks are per-page. 
  // If we close the page, the mocks die.
  // Standard Lighthouse run will open a NEW page for auditing.
  // So request interception on a *separate* page won't help the Lighthouse run page.
  
  // CRITICAL: Request Interception with Puppeteer for Lighthouse is TRICKY because
  // Lighthouse *disconnects* Puppeteer and uses logic over CDP.
  // And it opens its own tabs.
  
  // ALTERNATIVE: Just login.
  // But we have NO backend.
  
  // So.. we can't really audit the Dashboard on a static build easily with Lighthouse 
  // unless we use `lhci server` logic or proxy.
  
  // DECISION: For now, I will omit the request interception/mocking for the *Audit* itself,
  // because wiring that up to the Lighthouse page is hard.
  // I will leave the script simple: try to login. 
  // But acknowledge it will fail without backend.
  // User asked "what can we do".
  // Best answer: "To verify Dashboard, use Playwright. To verify Login performance, use Lighthouse."
  // Trying to bypass login for Lighthouse on static files is barely worth it compared to E2E.
  
  await page.close();
};
