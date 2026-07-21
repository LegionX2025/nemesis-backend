import { WorkflowEntrypoint } from 'cloudflare:workers';
import { DurableObject } from 'cloudflare:workers';

// ============================================================================
// 1. CLOUDFLARE WORKFLOWS (Stateful Tracing Process)
// ============================================================================
export class TraceWorkflow extends WorkflowEntrypoint {
  async run(event, step) {
    const traceData = event.payload;
    const address = traceData.address || "unknown";

    // Step 1: Initialize Trace & Notify Realtime
    const initialized = await step.do('init_trace', async () => {
      console.log(`Starting trace workflow for ${address}`);
      await this.notifyRealtime(traceData.trace_id, `Starting Edge trace for ${address}`);
      return { status: "started", timestamp: Date.now() };
    });

    // Step 2: Edge Aggregation (Etherscan & Caching)
    const edgeData = await step.do('edge_aggregate', async () => {
      await this.notifyRealtime(traceData.trace_id, `Aggregating Blockchain APIs at Edge...`);
      
      // Check KV Cache
      const cacheKey = `eth_balance_${address}`;
      let cachedBal = await this.env.NEMESIS_CACHE.get(cacheKey);
      
      if (!cachedBal) {
        // Fetch from Etherscan if not in cache
        const ethKey = this.env.ETHERSCAN_API_KEY || "YourApiKeyToken";
        const res = await fetch(`https://api.etherscan.io/api?module=account&action=balance&address=${address}&tag=latest&apikey=${ethKey}`);
        const data = await res.json();
        
        if (data.status === "1") {
          cachedBal = data.result;
          // Cache for 1 hour
          await this.env.NEMESIS_CACHE.put(cacheKey, cachedBal, { expirationTtl: 3600 });
        }
      }
      
      return { etherscan_balance: cachedBal };
    });

    // Step 3: Trigger Python Engine for Heavy AI Analysis
    const pythonResult = await step.do('trigger_python_backend', async () => {
      await this.notifyRealtime(traceData.trace_id, `Triggering Deep AI Scraping on Local Backend...`);
      if (!this.env.PYTHON_BACKEND_URL) return { error: "Tunnel URL missing" };
      
      // Append the Edge data so Python doesn't have to fetch it
      traceData.edgeData = edgeData;
      
      const res = await fetch(`${this.env.PYTHON_BACKEND_URL}/api/start_trace`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(traceData)
      });
      return await res.json();
    });

    // Step 4: Archive Result to R2 Object Storage
    await step.do('archive_r2', async () => {
      await this.notifyRealtime(traceData.trace_id, `Archiving OmniChain Report to R2 Storage...`);
      const report = JSON.stringify({ original: traceData, edge: edgeData, ai_analysis: pythonResult });
      await this.env.STORAGE.put(`traces/${traceData.trace_id}.json`, report);
    });

    await this.notifyRealtime(traceData.trace_id, `Trace Complete! Report archived.`);
    return { success: true, edge_data: edgeData, python_result: pythonResult };
  }

  // Helper to send messages to Durable Object WebSocket
  async notifyRealtime(traceId, message) {
    try {
      const doId = this.env.REALTIME_WS.idFromName("/ws/operations");
      const stub = this.env.REALTIME_WS.get(doId);
      await stub.fetch("http://internal/broadcast", {
        method: "POST",
        body: JSON.stringify({ type: "ops_update", traceId, message })
      });
    } catch (e) {
      console.error("Failed to notify realtime:", e);
    }
  }
}

// ============================================================================
// 2. DURABLE OBJECTS (Real-Time WebSocket State)
// ============================================================================
export class RealtimeManager extends DurableObject {
  constructor(ctx, env) {
    super(ctx, env);
    this.sessions = [];
  }

  async fetch(request) {
    const url = new URL(request.url);

    // Internal endpoint for Workflows to broadcast messages
    if (url.pathname === "/broadcast" && request.method === "POST") {
      const msg = await request.text();
      for (const session of this.sessions) {
        session.send(msg);
      }
      return new Response("Broadcasted", { status: 200 });
    }

    const upgradeHeader = request.headers.get('Upgrade');
    if (!upgradeHeader || upgradeHeader !== 'websocket') {
      return new Response('Expected Upgrade: websocket', { status: 426 });
    }

    const [client, server] = Object.values(new WebSocketPair());
    
    server.accept();
    this.sessions.push(server);

    server.addEventListener('message', event => {
      console.log("DO received:", event.data);
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

export class TraceCoordinator extends DurableObject {
  constructor(ctx, env) { super(ctx, env); }
  async fetch(request) { return new Response("TraceCoordinator OK"); }
}

export class AdminConsole extends DurableObject {
  constructor(ctx, env) { super(ctx, env); }
  async fetch(request) { return new Response("AdminConsole OK"); }
}

export class NotificationHub extends DurableObject {
  constructor(ctx, env) { super(ctx, env); }
  async fetch(request) { return new Response("NotificationHub OK"); }
}

// ============================================================================
// 3. MAIN WORKER (Gateway, Queues, KV, D1, Analytics)
// ============================================================================
export default {
  // --- HTTP GATEWAY ---
  async fetch(request, env, ctx) {
    const url = new URL(request.url);

    // Allow CORS for operations dashboard
    if (request.method === "OPTIONS") {
      return new Response(null, {
        headers: {
          "Access-Control-Allow-Origin": "*",
          "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
          "Access-Control-Allow-Headers": "Content-Type",
        }
      });
    }

    const corsHeaders = {
      "Access-Control-Allow-Origin": "*",
    };

    // 3a. Start a Workflow
    if (url.pathname === '/api/workflow/start' && request.method === 'POST') {
      const payload = await request.json();
      const instance = await env.TRACE_WORKFLOW.create({ payload });
      
      // Write Telemetry to Analytics Engine
      if (env.NEMESIS_METRICS) {
        env.NEMESIS_METRICS.writeDataPoint({
          blobs: ["workflow_started", payload.trace_id],
          doubles: [1.0],
          indexes: [payload.address]
        });
      }

      return Response.json({ workflow_id: instance.id }, { headers: corsHeaders });
    }

    // 3b. Realtime WebSockets via Durable Objects
    if (url.pathname.startsWith('/api/ws/')) {
      const id = env.REALTIME_WS.idFromName("/ws/operations");
      const stub = env.REALTIME_WS.get(id);
      return stub.fetch(request);
    }

    // 3c. Mock API Routes for Nemesis ID Dashboard
    // 3c. Live API Routes for Nemesis ID Dashboard (Multi-Chain Auto-Detect)
    const CHAINS = [
        { id: "ETH", url: "https://api.etherscan.io/api", key: env.ETHERSCAN_API_KEY, logo: "https://cryptologos.cc/logos/ethereum-eth-logo.png", name: "Ethereum" },
        { id: "BSC", url: "https://api.bscscan.com/api", key: env.BSCSCAN_API_KEY, logo: "https://cryptologos.cc/logos/bnb-bnb-logo.png", name: "Binance Smart Chain" },
        { id: "POLYGON", url: "https://api.polygonscan.com/api", key: env.POLYGONSCAN_API_KEY, logo: "https://cryptologos.cc/logos/polygon-matic-logo.png", name: "Polygon" }
    ];

    async function detectActiveChain(address) {
        // Fetch balance from all 3 chains concurrently
        const fetchPromises = CHAINS.map(async chain => {
            if (!chain.key) return { chain, active: false };
            try {
                const balRes = await fetch(`${chain.url}?module=account&action=balance&address=${address}&tag=latest&apikey=${chain.key}`);
                const txRes = await fetch(`${chain.url}?module=account&action=txlist&address=${address}&page=1&offset=50&sort=desc&apikey=${chain.key}`);
                const balData = await balRes.json();
                const txData = await txRes.json();
                
                const balance = balData.status === "1" ? parseFloat(balData.result) : 0;
                const txCount = txData.status === "1" ? txData.result.length : 0;
                
                return { chain, active: balance > 0 || txCount > 0, balance, txCount, txData };
            } catch (e) {
                return { chain, active: false };
            }
        });
        
        const results = await Promise.all(fetchPromises);
        // Sort by most active (highest tx count, then balance)
        const sorted = results.filter(r => r.active).sort((a, b) => b.txCount - a.txCount || b.balance - a.balance);
        return sorted.length > 0 ? sorted[0] : results[0]; // Return best match or default ETH
    }

    if (url.pathname.startsWith('/api/nemesis_id/profile/')) {
      const address = url.pathname.split('/').pop();
      try {
        const activeData = await detectActiveChain(address);
        const chain = activeData.chain;
        
        const ethBalance = (activeData.balance / 1e18).toFixed(4);
        let lastActivity = "Unknown";
        let firstActivity = "Unknown";
        let totalSent = 0;
        let totalReceived = 0;

        if (activeData.txData && activeData.txData.status === "1" && activeData.txData.result.length > 0) {
            const txs = activeData.txData.result;
            lastActivity = new Date(parseInt(txs[0].timeStamp) * 1000).toUTCString();
            firstActivity = new Date(parseInt(txs[txs.length - 1].timeStamp) * 1000).toUTCString();
            
            txs.forEach(tx => {
                const val = parseFloat(tx.value) / 1e18;
                if (tx.from.toLowerCase() === address.toLowerCase()) totalSent += val;
                else totalReceived += val;
            });
        }

        return new Response(JSON.stringify({
          address: address,
          network: chain.name,
          network_logo: chain.logo,
          nemesis_id: "LGN-" + address.substring(2, 6).toUpperCase(),
          first_activity: firstActivity,
          last_activity: lastActivity,
          total_transactions: activeData.txCount || "0",
          total_received: totalReceived.toFixed(4) + ` ${chain.id}`,
          total_sent: totalSent.toFixed(4) + ` ${chain.id}`,
          balance: ethBalance + ` ${chain.id}`,
          entity: { name: "Auto-Detected Entity" },
          tx_categories: { "transfers": activeData.txCount || 0 },
          alert: `${chain.name} Network Activity Detected`,
          summary: `Live omni-chain scan auto-detected activity on ${chain.name}. Current balance is ${ethBalance} ${chain.id}. Last active: ${lastActivity}.`
        }), { headers: { "Content-Type": "application/json", ...corsHeaders } });
      } catch (err) {
        return new Response(JSON.stringify({ error: "Failed to fetch from block explorer" }), { status: 500, headers: corsHeaders });
      }
    }

    if (url.pathname.startsWith('/api/nemesis_id/aml/')) {
      // Stub AML response (Arkham/Chainalysis requires paid APIs, using heuristic placeholder)
      return new Response(JSON.stringify({
        risk_score: 45.0,
        classification: "MODERATE RISK"
      }), { headers: { "Content-Type": "application/json", ...corsHeaders } });
    }

    if (url.pathname.startsWith('/api/nemesis_id/intel/')) {
      // Stub OSINT intel response
      return new Response(JSON.stringify({
        custodial_entry: "Unknown CEX",
        osint_intel: "No direct social media associations found.",
        darknet_mentions: "0 Mentions",
        arkham_intel: "No label assigned",
        vasp_intel: "Standard EVM Interaction",
        is_malicious: false
      }), { headers: { "Content-Type": "application/json", ...corsHeaders } });
    }

    if (url.pathname.startsWith('/api/nemesis_id/tx_history/')) {
      const address = url.pathname.split('/').pop();
      try {
        const activeData = await detectActiveChain(address);
        
        let txns = [];
        if (activeData.txData && activeData.txData.status === "1") {
            txns = activeData.txData.result.map(tx => ({
                hash: tx.hash,
                timestamp: new Date(parseInt(tx.timeStamp) * 1000).toISOString(),
                from: tx.from,
                to: tx.to,
                value: (parseFloat(tx.value) / 1e18).toFixed(4),
                risk_score: Math.floor(Math.random() * 40) + 10 // Mock heuristic risk
            }));
        }

        return new Response(JSON.stringify({ transactions: txns }), { headers: { "Content-Type": "application/json", ...corsHeaders } });
      } catch (err) {
        return new Response(JSON.stringify({ error: "Failed to fetch tx history" }), { status: 500, headers: corsHeaders });
      }
    }

    // Default Proxy to Python Backend
    // In production, this should point to your Ngrok/Cloudflared tunnel
    let backendUrl = env.PYTHON_BACKEND_URL || "http://127.0.0.1:3001";
    if (backendUrl === "https://your-tunnel-url.trycloudflare.com") {
        // Fallback for local testing if Tunnel is not yet configured
        // Cloudflare Workers cannot fetch localhost, so if it's the default, we return 502
        return new Response(JSON.stringify({ 
            error: "Backend not configured.", 
            message: "PYTHON_BACKEND_URL must be set in wrangler.toml or Cloudflare Dashboard to point to your Python server."
        }), { 
            status: 502,
            headers: { "Content-Type": "application/json" }
        });
    }

    try {
        const proxyReq = new Request(backendUrl + url.pathname + url.search, request);
        return await fetch(proxyReq);
    } catch (e) {
        return new Response(JSON.stringify({ error: "Backend Unreachable", details: e.message }), { status: 502 });
    }
  },

  // --- QUEUE CONSUMER ---
  async queue(batch, env) {
    for (const msg of batch.messages) {
      try {
        console.log("Queue received:", msg.body);
        // Start a Workflow
        await env.TRACE_WORKFLOW.create({ payload: msg.body });
        msg.ack();
      } catch (err) {
        msg.retry();
      }
    }
  }
};
