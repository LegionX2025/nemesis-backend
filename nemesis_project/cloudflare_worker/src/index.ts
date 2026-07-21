import { Hono } from 'hono'
import { cors } from 'hono/cors'

// Cloudflare Bindings Interface
export interface Env {
    DB: D1Database;
    NEMESIS_KV: KVNamespace;
    NEMESIS_STORAGE: R2Bucket;
    BACKEND_API_URL: string;
    NEMESIS_EDGE_SECRET: string;
    HYPERDRIVE: any;
}

const app = new Hono<{ Bindings: Env }>()

// Global CORS
app.use('*', cors())

// Healthcheck
app.get('/', (c) => {
    return c.json({ 
        status: 'online', 
        service: 'nemesis-edge-proxy',
        version: '1.0.0'
    })
})

// Proxy API requests to Render backend
app.all('/api/*', async (c) => {
    try {
        const url = new URL(c.req.url)
        const targetUrl = `${c.env.BACKEND_API_URL}${url.pathname}${url.search}`
        
        // Log access to D1 (async, don't await so we don't block response)
        c.executionCtx.waitUntil(
            c.env.DB.prepare('INSERT INTO audit_logs (event_type, target_wallet, actor_ip) VALUES (?, ?, ?)')
            .bind('API_ACCESS', url.pathname, c.req.header('cf-connecting-ip') || 'unknown')
            .run()
            .catch(err => console.error("D1 Audit log failed:", err))
        )

        // Generate an HMAC or simple secret token for the backend to verify
        // In a real prod environment, use WebCrypto for HMAC. Here we pass the secret.
        const edgeSecret = c.env.NEMESIS_EDGE_SECRET || "default_dev_secret_override";
        
        const newHeaders = new Headers(c.req.header());
        newHeaders.set('X-Nemesis-Signature', edgeSecret);

        const response = await fetch(targetUrl, {
            method: c.req.method,
            headers: newHeaders,
            body: c.req.method !== 'GET' && c.req.method !== 'HEAD' ? await c.req.arrayBuffer() : null
        })

        // Handle WebSocket Upgrade Native Response
        if (response.headers.get('Upgrade') === 'websocket') {
            return response;
        }

        const newResponse = new Response(response.body, response)
        // Add edge-specific headers
        newResponse.headers.set('X-Edge-Served-By', 'Cloudflare Nemesis Worker')
        return newResponse

    } catch (e: any) {
        return c.json({ error: "Edge Proxy Error", details: e.message }, 500)
    }
})

// Storage Fetcher
app.get('/assets/*', async (c) => {
    const key = c.req.path.replace('/assets/', '')
    const object = await c.env.NEMESIS_STORAGE.get(key)

    if (object === null) {
        return c.text('Asset Not Found', 404)
    }

    const headers = new Headers()
    object.writeHttpMetadata(headers)
    headers.set('etag', object.httpEtag)

    return new Response(object.body, { headers })
})

export default app
