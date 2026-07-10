// Cloudflare Pages Function (API Gateway / Queue Producer)
// This intercepts POST requests to /api/start_trace from the frontend
// and pushes them reliably to a Cloudflare Queue.

export async function onRequestPost(context) {
  const { request, env } = context;

  try {
    const payload = await request.json();
    
    // Generate a unique trace ID if one isn't provided
    const trace_id = payload.trace_id || crypto.randomUUID().substring(0, 8);
    payload.trace_id = trace_id;

    // Push the trace request to the Cloudflare Queue
    if (env.TRACE_QUEUE) {
      await env.TRACE_QUEUE.send(payload);
      console.log(`Trace ${trace_id} queued successfully.`);
      
      // Return immediately to the frontend so the UI can switch to tracing mode
      return new Response(JSON.stringify({
        status: "queued",
        trace_id: trace_id,
        message: "Trace request successfully pushed to global queue."
      }), {
        headers: { "Content-Type": "application/json" }
      });
    } else {
      console.error("TRACE_QUEUE binding is missing!");
      return new Response(JSON.stringify({ error: "System Queue misconfigured" }), {
        status: 500,
        headers: { "Content-Type": "application/json" }
      });
    }
  } catch (err) {
    return new Response(JSON.stringify({ error: err.message }), {
      status: 400,
      headers: { "Content-Type": "application/json" }
    });
  }
}
