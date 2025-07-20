// pages/api/process-all.js - Process everything in optimal order
export const config = {
  maxDuration: 60, // Extended timeout for processing everything
};

export default async function handler(req, res) {
  const startTime = Date.now();
  console.log(
    "🚀 Starting complete email processing at",
    new Date().toISOString()
  );

  const results = {
    replyProcessing: null,
    emailCheck: null,
    manualForward: null,
    summary: {
      totalProcessed: 0,
      totalForwarded: 0,
      totalBlocked: 0,
      repliesProcessed: 0,
      manualForwarded: 0,
    },
  };

  try {
    // STEP 1: Process wife's replies FIRST (updates preferences)
    console.log("💬 Step 1: Processing wife's replies...");
    try {
      const replyResponse = await fetch(
        `https://${req.headers.host}/api/process-replies`
      );
      if (replyResponse.ok) {
        results.replyProcessing = await replyResponse.json();
        results.summary.repliesProcessed =
          results.replyProcessing.processedReplies || 0;
        console.log(
          `✅ Processed ${results.summary.repliesProcessed} reply commands`
        );
      } else {
        console.error("⚠️ Reply processing failed:", replyResponse.status);
        results.replyProcessing = { error: `HTTP ${replyResponse.status}` };
      }
    } catch (error) {
      console.error("⚠️ Reply processing error:", error.message);
      results.replyProcessing = { error: error.message };
    }

    // Small delay to ensure preference updates are processed
    await new Promise((resolve) => setTimeout(resolve, 1000));

    // STEP 2: Check and process new emails (uses updated preferences)
    console.log("📧 Step 2: Processing new emails...");
    try {
      const emailResponse = await fetch(
        `https://${req.headers.host}/api/check-emails`
      );
      if (emailResponse.ok) {
        results.emailCheck = await emailResponse.json();
        results.summary.totalProcessed = results.emailCheck.processed || 0;
        results.summary.totalForwarded = results.emailCheck.forwarded || 0;
        results.summary.totalBlocked = results.emailCheck.skipped || 0;
        console.log(
          `✅ Processed ${results.summary.totalProcessed} emails, forwarded ${results.summary.totalForwarded}`
        );
      } else {
        console.error("⚠️ Email check failed:", emailResponse.status);
        results.emailCheck = { error: `HTTP ${emailResponse.status}` };
      }
    } catch (error) {
      console.error("⚠️ Email check error:", error.message);
      results.emailCheck = { error: error.message };
    }

    // STEP 3: Manual forwarding (if requested)
    const includeManual =
      req.query.manual === "true" || req.query.includeManual === "true";
    if (includeManual) {
      console.log("🎯 Step 3: Processing manual forwards...");
      try {
        const manualResponse = await fetch(
          `https://${req.headers.host}/api/manual-forward`
        );
        if (manualResponse.ok) {
          results.manualForward = await manualResponse.json();
          results.summary.manualForwarded =
            results.manualForward.forwarded || 0;
          console.log(
            `✅ Manual forwarded ${results.summary.manualForwarded} emails`
          );
        } else {
          console.error("⚠️ Manual forward failed:", manualResponse.status);
          results.manualForward = { error: `HTTP ${manualResponse.status}` };
        }
      } catch (error) {
        console.error("⚠️ Manual forward error:", error.message);
        results.manualForward = { error: error.message };
      }
    } else {
      console.log("⏭️ Skipping manual forwards (not requested)");
    }

    const duration = Date.now() - startTime;
    console.log(`✅ Complete processing finished in ${duration}ms`);

    // Determine overall success
    const hasErrors = [
      results.replyProcessing,
      results.emailCheck,
      results.manualForward,
    ]
      .filter(Boolean)
      .some((result) => result.error);

    res.status(hasErrors ? 207 : 200).json({
      success: !hasErrors,
      message: hasErrors
        ? "Completed with some errors"
        : "All processing completed successfully",
      results,
      summary: results.summary,
      duration,
      timestamp: new Date().toISOString(),
      processingOrder: [
        "1. Wife's reply commands (update preferences)",
        "2. New email detection and forwarding",
        "3. Manual forwarding (if requested)",
      ],
    });
  } catch (error) {
    const duration = Date.now() - startTime;
    console.error("💥 Complete processing failed:", error);

    res.status(500).json({
      success: false,
      error: "Complete processing failed",
      details: error.message,
      results,
      duration,
      timestamp: new Date().toISOString(),
    });
  }
}
