import { DurableObject } from 'cloudflare:workers'

export class TraceCoordinator extends DurableObject {
  async fetch(request: Request) {
    if (request.method === 'POST') {
        const body = await request.json();
        // Here we would coordinate trace jobs, but for now we act as an event sink.
        return new Response(JSON.stringify({ status: "trace_job_accepted", id: this.ctx.id.toString() }), { status: 202 });
    }
    return new Response("Trace Coordinator DO Ready");
  }
}

export class RealtimeManager extends DurableObject {
  sessions: Map<WebSocket, string>;

  constructor(ctx: DurableObjectState, env: any) {
    super(ctx, env);
    this.sessions = new Map();
  }

  async fetch(request: Request) {
    const upgradeHeader = request.headers.get('Upgrade');
    if (!upgradeHeader || upgradeHeader !== 'websocket') {
      return new Response('Expected Upgrade: websocket', { status: 426 });
    }

    const [client, server] = Object.values(new WebSocketPair());
    
    server.accept();
    this.sessions.set(server, 'active');

    server.addEventListener('message', async (event) => {
      try {
        const data = JSON.parse(event.data as string);
        if (data.type === 'ping') {
          server.send(JSON.stringify({ type: 'pong', timestamp: Date.now() }));
        }
        // Broadcast to all clients in this DO (trace_id specific)
        for (const [ws] of this.sessions) {
           if (ws !== server) ws.send(event.data);
        }
      } catch (e) {
        console.error("WS error:", e);
      }
    });

    server.addEventListener('close', () => {
      this.sessions.delete(server);
    });

    return new Response(null, {
      status: 101,
      webSocket: client,
    });
  }
}

export class AdminConsole extends DurableObject {
  async fetch(request: Request) { 
      return new Response(JSON.stringify({ status: "admin_console_active" })); 
  }
}
