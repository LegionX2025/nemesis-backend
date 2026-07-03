import { Hono } from 'hono'
import { cors } from 'hono/cors'
import { Client } from 'pg'
import { TraceCoordinator, RealtimeManager, AdminConsole } from './durable_objects'

type Bindings = {
  PYTHON_BACKEND_URL: string
  NEMESIS_CACHE: KVNamespace
  ENTITY_CACHE: KVNamespace
  SESSION_CACHE: KVNamespace
  TOKEN_CACHE: KVNamespace
  OSINT_CACHE: KVNamespace
  DB: D1Database
  REPORTS: R2Bucket
  TRACE_QUEUE: Queue
  ENTITY_QUEUE: Queue
  TRACE_COORDINATOR: DurableObjectNamespace
  REALTIME_MANAGER: DurableObjectNamespace
  ADMIN_CONSOLE: DurableObjectNamespace
  HYPERDRIVE: Hyperdrive
}

const app = new Hono<{ Bindings: Bindings }>()

app.use('*', cors({
  origin: '*',
  allowHeaders: ['Content-Type', 'Authorization', 'X-Requested-With'],
  allowMethods: ['POST', 'GET', 'OPTIONS']
}))

// Forward endpoints to FastAPI backend
const proxyToBackend = async (c: any, path: string) => {
  const backendUrl = c.env.PYTHON_BACKEND_URL || 'http://localhost:3001'
  // Avoid double slashes
  const cleanPath = path.startsWith('/') ? path : '/' + path;
  const targetUrl = new URL(cleanPath, backendUrl).toString();
  
  // Create a new request based on the original to safely override the URL
  const originalReq = c.req.raw;
  const proxyReq = new Request(targetUrl, originalReq);
  
  return fetch(proxyReq);
}

// Postgres Test Route using Hyperdrive
app.get('/api/pg-test', async (c) => {
  const client = new Client({ connectionString: c.env.HYPERDRIVE.connectionString });
  await client.connect();

  try {
    const result = await client.query("SELECT * FROM pg_tables");
    return c.json({ result: result.rows });
  } catch (e) {
    return c.json({ error: e instanceof Error ? e.message : String(e) }, 500);
  } finally {
    // Prevent connection leaks
    await client.end();
  }
})

// D1 Database Proxy Endpoint
app.post('/db-api/query', async (c) => {
  try {
    const { query, params } = await c.req.json();
    if (!query) return c.json({ success: false, error: "Query is required" }, 400);
    
    let stmt = c.env.DB.prepare(query);
    if (params && Array.isArray(params)) {
      stmt = stmt.bind(...params);
    }
    
    // Determine if it's a read or write operation
    const isWrite = query.trim().toUpperCase().startsWith('INSERT') || 
                    query.trim().toUpperCase().startsWith('UPDATE') || 
                    query.trim().toUpperCase().startsWith('DELETE');
                    
    if (isWrite) {
      const result = await stmt.run();
      return c.json({ success: true, result });
    } else {
      const result = await stmt.all();
      return c.json({ success: true, result: result.results });
    }
  } catch (e) {
    return c.json({ success: false, error: e instanceof Error ? e.message : String(e) }, 500);
  }
})

app.all('/api/*', (c) => proxyToBackend(c, c.req.path))
app.all('/admin/*', (c) => proxyToBackend(c, c.req.path))

// WebSocket endpoints (Proxying to Durable Objects)
app.get('/ws/:trace_id', (c) => {
  const id = c.env.REALTIME_MANAGER.idFromName(c.req.param('trace_id'))
  const stub = c.env.REALTIME_MANAGER.get(id)
  return stub.fetch(c.req.raw)
})

export default {
  fetch: app.fetch,
  async queue(batch: any, env: Bindings, ctx: any) {
    console.log(`Processing queue: ${batch.queue}`);
    for (const message of batch.messages) {
      console.log(`Message: ${JSON.stringify(message.body)}`);
    }
  }
}
export { TraceCoordinator, RealtimeManager, AdminConsole }
