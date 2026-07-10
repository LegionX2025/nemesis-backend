export async function onRequest(context) {
  const { request, env } = context;
  const url = new URL(request.url);
  
  // The backend Tunnel URL
  const backend = env.PYTHON_BACKEND_URL || "http://127.0.0.1:3001";
  const targetUrl = backend + url.pathname + url.search;
  
  console.log(`Proxying ${request.method} to ${targetUrl}`);
  
  // Create a new request based on the original
  const newRequest = new Request(targetUrl, request);
  
  try {
    const response = await fetch(newRequest);
    return response;
  } catch (err) {
    return new Response(JSON.stringify({ error: "Backend proxy failed: " + err.message }), {
      status: 502,
      headers: { "Content-Type": "application/json" }
    });
  }
}
