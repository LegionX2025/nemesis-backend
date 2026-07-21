export default {
  // This worker handles incoming messages from the Cloudflare Queue
  async queue(batch, env) {
    console.log(`Received ${batch.messages.length} messages in queue batch.`);
    
    // The URL of your Python backend via Cloudflare Tunnel
    // E.g., https://api.yourdomain.com or https://random-words.trycloudflare.com
    const BACKEND_URL = env.PYTHON_BACKEND_URL;
    
    if (!BACKEND_URL) {
      console.error("Missing PYTHON_BACKEND_URL in environment variables.");
      return;
    }

    for (const message of batch.messages) {
      try {
        const payload = message.body;
        console.log("Processing trace request:", payload.trace_id);
        
        // Forward the trace request to the Python backend
        const response = await fetch(`${BACKEND_URL}/api/start_trace`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-Queue-Source': 'Cloudflare',
          },
          body: JSON.stringify(payload)
        });

        if (!response.ok) {
          const errText = await response.text();
          console.error(`Backend failed with status ${response.status}: ${errText}`);
          // Throwing an error causes the queue to retry this message later
          throw new Error("Backend processing failed.");
        }
        
        console.log("Trace successfully dispatched to backend:", payload.trace_id);
        // Message is implicitly acknowledged if no error is thrown
        message.ack();

      } catch (err) {
        console.error("Error processing queue message:", err);
        // Do not ack the message, let it retry
        message.retry();
      }
    }
  }
};
