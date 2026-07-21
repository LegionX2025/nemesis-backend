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
    // 1. Handle internal broadcast messages from the Queue Consumer
    if (request.method === 'POST' && request.url.includes('/broadcast')) {
        try {
            const payload = await request.text();
            for (const [ws] of this.sessions) {
                try { ws.send(payload); } catch(e) {}
            }
            return new Response("Broadcasted", { status: 200 });
        } catch (e) {
            return new Response("Broadcast failed", { status: 500 });
        }
    }

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
          return;
        }

        if (data.type === 'START_TRACE') {
          // Push to the Cloudflare Queue to process in background
          if (this.env.TRACE_QUEUE) {
            await this.env.TRACE_QUEUE.send({
                action: 'start_trace',
                trace_id: (data.seeds && data.seeds.length > 0) ? data.seeds[0] : 'default',
                seeds: data.seeds,
                target_amount: data.target_amount,
                network: data.network
            });
            server.send(JSON.stringify({ type: 'PROGRESS', data: { message: "Trace queued on Edge..." } }));
          } else {
            server.send(JSON.stringify({ type: 'PROGRESS', data: { message: "Error: TRACE_QUEUE binding missing!" } }));
          }
          return;
        }

        // Broadcast other messages to all clients in this DO (trace_id specific)
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
