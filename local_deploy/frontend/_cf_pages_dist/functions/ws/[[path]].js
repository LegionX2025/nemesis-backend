export async function onRequest(context) {
  const { request, env } = context;
  const url = new URL(request.url);
  
  // The backend Tunnel URL
  const backend = env.PYTHON_BACKEND_URL || "http://127.0.0.1:3001";
  
  // Convert https:// to wss:// and http:// to ws://
  let wsBackend = backend;
  if (wsBackend.startsWith("https://")) wsBackend = wsBackend.replace("https://", "wss://");
  else if (wsBackend.startsWith("http://")) wsBackend = wsBackend.replace("http://", "ws://");
  
  const targetUrl = wsBackend + url.pathname + url.search;
  
  console.log(`Proxying WebSocket to ${targetUrl}`);
  
  // Create a new request for the WebSocket upgrade
  const newRequest = new Request(targetUrl, request);
  
  try {
    const response = await fetch(newRequest);
    return response;
  } catch (err) {
    return new Response(JSON.stringify({ error: "WebSocket proxy failed: " + err.message }), {
      status: 502,
      headers: { "Content-Type": "application/json" }
    });
  }
}
