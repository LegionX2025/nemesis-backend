import { Hono } from 'hono';
import { cors } from 'hono/cors';

export interface Env {
  TRACE_SESSION_DO: DurableObjectNamespace;
  DARKNET_QUEUE: Queue;
  ENVIRONMENT: string;
}

const app = new Hono<{ Bindings: Env }>();

// Enable CORS for all routes
app.use('/api/*', cors());

app.get('/', (c) => c.text('Lionsgate Nemesis API (Cloudflare Edge) - Online'));

// ----------------------------------------------------
// REST ENDPOINTS (PROXY TO BACKEND)
// ----------------------------------------------------

// Helper function to proxy requests to the true Python backend
async function proxyToBackend(c: any, path: string) {
  const backendUrl = c.env.PYTHON_BACKEND_URL || 'https://nemesis-backend.onrender.com';
  const url = new URL(c.req.url);
  
  try {
    const fetchUrl = `${backendUrl}${path}${url.search}`;
    const options: RequestInit = {
      method: c.req.method,
      headers: c.req.header(),
    };
    
    if (c.req.method !== 'GET' && c.req.method !== 'HEAD') {
      options.body = await c.req.text();
    }
    
    const response = await fetch(fetchUrl, options);
    const body = await response.text();
    
    return new Response(body, {
      status: response.status,
      headers: response.headers
    });
  } catch (err) {
    return c.json({ status: "error", message: `Edge Proxy Error: ${err}` }, 502);
  }
}

app.get('/api/darknet/search', (c) => proxyToBackend(c, '/api/darknet/search'));
app.get('/api/intelligence/summary', (c) => proxyToBackend(c, '/api/intelligence/summary'));
app.post('/api/intelligence/analyze', (c) => proxyToBackend(c, '/api/intelligence/analyze'));
app.get('/admin/health', (c) => proxyToBackend(c, '/admin/health'));

// ----------------------------------------------------
// WEBSOCKET TRACING ENDPOINT (DURABLE OBJECTS)
// ----------------------------------------------------

app.post('/api/start_trace', async (c) => {
  const body = await c.req.json().catch(() => ({}));
  const id = c.env.TRACE_SESSION_DO.newUniqueId().toString();
  return c.json({
    status: "started",
    trace_id: id
  });
});

app.get('/ws/:trace_id', async (c) => {
  const upgradeHeader = c.req.header('Upgrade');
  if (upgradeHeader !== 'websocket') {
    return c.text('Expected Upgrade: websocket', 426);
  }

  const traceId = c.req.param('trace_id');
  let id;
  try {
    id = c.env.TRACE_SESSION_DO.idFromString(traceId);
  } catch (e) {
    id = c.env.TRACE_SESSION_DO.newUniqueId();
  }
  const stub = c.env.TRACE_SESSION_DO.get(id);

  return stub.fetch(c.req.raw);
});

// Export the Worker handlers
export default {
  // Handle HTTP Requests via Hono
  fetch: app.fetch,

  // Handle Queue Consumption for Darknet Crawler
  async queue(batch: MessageBatch<any>, env: Env): Promise<void> {
    for (const message of batch.messages) {
      console.log(`Processing crawled URL: ${message.body.url}`);
      // TODO: Implement headless scraping via Browser Rendering API
      // Then store results in MongoDB or D1
    }
  }
};

// Re-export the Durable Object class so Cloudflare can bind it
export { TraceSessionDO } from './durable_objects/TraceSessionDO';
