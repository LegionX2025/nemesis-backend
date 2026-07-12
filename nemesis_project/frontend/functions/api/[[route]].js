export async function onRequest(context) {
    const { request, env, params } = context;
    const url = new URL(request.url);
    
    // Handle CORS preflight requests
    if (request.method === "OPTIONS") {
        return new Response(null, {
            headers: {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, OPTIONS, PUT, DELETE",
                "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Nemesis-Signature",
                "Access-Control-Max-Age": "86400",
            }
        });
    }

    // We are proxying requests to /api/* to the Backend Worker
    const targetUrl = new URL(url.pathname + url.search, env.BACKEND_API_URL || "https://nemesis-python-worker.legionxgaming2021.workers.dev");
    
    // Create a new request object to forward
    const proxyRequest = new Request(targetUrl, request);
    
    // Inject the Nemesis Edge Signature to authenticate with the backend
    proxyRequest.headers.set('X-Nemesis-Signature', env.NEMESIS_EDGE_SECRET || "default_dev_secret_override");
    
    // Check if the request is a GET request and can be cached
    const cacheKey = new Request(url.toString(), request);
    const cache = caches.default;
    
    if (request.method === "GET") {
        let response = await cache.match(cacheKey);
        if (response) {
            // Found in Cloudflare edge cache
            // Async log to D1 (fire and forget)
            context.waitUntil(logToD1(env, "CACHE_HIT", url.pathname));
            return response;
        }
    }
    
    // Async log to D1 (fire and forget)
    context.waitUntil(logToD1(env, "PROXY_API", url.pathname));
    
    // Forward the request to the Render backend
    let response = await fetch(proxyRequest);
    
    // Clone response so we can cache it
    response = new Response(response.body, response);
    
    // Set CORS headers for the frontend to consume
    response.headers.set('Access-Control-Allow-Origin', '*');
    
    // Cache GET responses
    if (request.method === "GET" && response.status === 200) {
        response.headers.set('Cache-Control', 's-maxage=60'); // Cache at edge for 60 seconds
        context.waitUntil(cache.put(cacheKey, response.clone()));
    }
    
    return response;
}

async function logToD1(env, action, details) {
    try {
        if (!env.DB) return; // DB binding not available
        await env.DB.prepare(
            "INSERT INTO audit_logs (action, details, timestamp) VALUES (?, ?, ?)"
        ).bind(action, details, new Date().toISOString()).run();
    } catch (e) {
        // Silently fail if D1 is not set up correctly yet
        console.error("D1 Logging Error:", e);
    }
}
