import { Env } from '../index';

export class TraceSessionDO {
  state: DurableObjectState;
  env: Env;
  sessions: WebSocket[];

  constructor(state: DurableObjectState, env: Env) {
    this.state = state;
    this.env = env;
    this.sessions = [];
  }

  async fetch(request: Request) {
    const upgradeHeader = request.headers.get('Upgrade');
    if (!upgradeHeader || upgradeHeader !== 'websocket') {
      return new Response('Durable Object expected Upgrade: websocket', { status: 426 });
    }

    // Create the WebSocket pair
    const webSocketPair = new WebSocketPair();
    const [client, server] = Object.values(webSocketPair);

    // Accept the WebSocket connection on the server side
    server.accept();
    this.sessions.push(server);

    // Set up event listeners for the server WebSocket
    server.addEventListener('message', async (event) => {
      try {
        const msg = JSON.parse(event.data as string);
        
        // Broadcast incoming start_trace to initiate tracking
        if (msg.type === 'start_trace') {
          // Send initial node data (simulating TraceEngine)
          server.send(JSON.stringify({
            type: 'node',
            data: {
              id: msg.seeds,
              label: msg.seeds.substring(0, 8) + '...',
              type: 'wallet',
              risk_score: 95
            }
          }));

          // Simulate finding a hop after 2 seconds
          setTimeout(() => {
            server.send(JSON.stringify({
              type: 'edge',
              data: {
                from: msg.seeds,
                to: '0xThreatActorWallet123',
                label: '15.5 ETH',
                tx_hash: '0xabc123'
              }
            }));
            
            server.send(JSON.stringify({
              type: 'node',
              data: {
                id: '0xThreatActorWallet123',
                label: 'Threat Actor',
                type: 'cluster',
                risk_score: 99
              }
            }));
          }, 2000);
        }
      } catch (err) {
        console.error('Error processing WS message:', err);
      }
    });

    server.addEventListener('close', () => {
      this.sessions = this.sessions.filter(s => s !== server);
    });

    return new Response(null, {
      status: 101,
      webSocket: client,
    });
  }
}
