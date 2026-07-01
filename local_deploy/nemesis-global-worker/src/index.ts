import { Hono } from 'hono'
import { cors } from 'hono/cors'
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

app.all('/api/*', (c) => proxyToBackend(c, c.req.path))
app.all('/admin/*', (c) => proxyToBackend(c, c.req.path))

// WebSocket endpoints (Proxying to Durable Objects)
app.get('/ws/:trace_id', (c) => {
  const id = c.env.REALTIME_MANAGER.idFromName(c.req.param('trace_id'))
  const stub = c.env.REALTIME_MANAGER.get(id)
  return stub.fetch(c.req.raw)
})

export default app
export { TraceCoordinator, RealtimeManager, AdminConsole }
