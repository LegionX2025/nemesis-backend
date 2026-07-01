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
// REST ENDPOINTS
// ----------------------------------------------------

app.get('/api/darknet/search', async (c) => {
  const query = c.req.query('q');
  if (!query) {
    return c.json({ results: [] });
  }
  
  // TODO: Connect to MongoDB Data API or D1 to fetch actual darknet records
  // For now, return a placeholder to verify routing
  return c.json({
    status: "success",
    results: [
      {
        "hash-ID": "CF-EDGE-MOCK",
        web_info: {
          title: "Darknet Migration in Progress",
          url: "http://nemesis.onion/migration",
          content: "The Darknet database is currently being migrated to the Cloudflare Edge."
        },
        uie_entities: [{ value: "MIGRATION" }],
        crawled_at: new Date().toISOString()
      }
    ]
  });
});

app.get('/api/intelligence/summary', async (c) => {
  return c.json({
    total_iocs: 15420,
    sanctioned_wallets: 342,
    active_threat_actors: 12,
    latest_intel: [
      { type: "Malware", value: "Lazarus Group Activity Detected (Edge Mock)" }
    ]
  });
});

app.post('/api/intelligence/analyze', async (c) => {
  const body = await c.req.json();
  return c.json({
    status: "analyzed",
    risk_score: 85,
    details: `Analysis complete for ${body.target || 'target'} at the Edge.`
  });
});

app.get('/admin/health', async (c) => {
  return c.json({
    active_websockets: 0,
    active_traces_count: 0,
    mongo_connected: false,
    environment: "Cloudflare Edge",
    active_traces: {}
  });
});

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
