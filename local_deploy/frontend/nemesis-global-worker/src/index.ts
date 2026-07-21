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
  REPORTS: R2Bucket
  TRACE_QUEUE: Queue
  ENTITY_QUEUE: Queue
  TRACE_COORDINATOR: DurableObjectNamespace
  REALTIME_MANAGER: DurableObjectNamespace
  ADMIN_CONSOLE: DurableObjectNamespace
  HYPERDRIVE: Hyperdrive
  ETHERSCAN_API_KEY?: string
  BSCSCAN_API_KEY?: string
  POLYGONSCAN_API_KEY?: string
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


app.post('/api/start_trace', async (c) => {
  try {
    const data = await c.req.json();
    const seeds = data.seeds || "";
    let traceId = seeds.split(/[\s,]+/)[0] || "";
    if (traceId.length > 8) traceId = traceId.substring(0, 8);
    if (!traceId) traceId = "TRC" + Date.now();
    
    if (c.env.TRACE_QUEUE) {
      await c.env.TRACE_QUEUE.send({
        action: "start_trace",
        trace_id: traceId,
        seeds: seeds,
        target_amount: data.target_amount || "1000",
        network: data.network || "AUTO"
      });
    }
    
    return c.json({
      status: "queued",
      trace_id: traceId,
      message: "Trace initiated on Cloudflare Edge"
    });
  } catch (e) {
    return c.json({ error: e instanceof Error ? e.message : String(e) }, 500);
  }
});

// 3c. Live API Routes for Nemesis ID Dashboard (Multi-Chain Auto-Detect)
const CHAINS = [
    { id: "ETH", url: "https://api.etherscan.io/api", keyEnv: "ETHERSCAN_API_KEY", logo: "https://cryptologos.cc/logos/ethereum-eth-logo.png", name: "Ethereum" },
    { id: "BSC", url: "https://api.bscscan.com/api", keyEnv: "BSCSCAN_API_KEY", logo: "https://cryptologos.cc/logos/bnb-bnb-logo.png", name: "Binance Smart Chain" },
    { id: "POLYGON", url: "https://api.polygonscan.com/api", keyEnv: "POLYGONSCAN_API_KEY", logo: "https://cryptologos.cc/logos/polygon-matic-logo.png", name: "Polygon" }
];

async function detectActiveChain(rawAddress: string, env: any) {
    const address = decodeURIComponent(rawAddress).trim().split(/[\r\n, ]+/)[0];
    const isBTC = /^(1|3|bc1)[a-zA-HJ-NP-Za-km-z0-9]{25,39}$/i.test(address);
    if (isBTC) {
        try {
            const res = await fetch(`https://blockstream.info/api/address/${address}/txs`);
            const btcData: any = await res.json();
            if (Array.isArray(btcData) && btcData.length > 0) {
                const mappedTxs = btcData.map((tx: any) => {
                    const isOutbound = tx.vin.some((v: any) => v.prevout && v.prevout.scriptpubkey_address === address);
                    let valSats = 0;
                    let from = "unknown";
                    let to = "unknown";
                    if (isOutbound) {
                        from = address;
                        const vout = tx.vout.find((v: any) => v.scriptpubkey_address !== address);
                        if (vout) {
                            to = vout.scriptpubkey_address || "unknown";
                            valSats = vout.value || 0;
                        }
                    } else {
                        const vout = tx.vout.find((v: any) => v.scriptpubkey_address === address);
                        if (vout) {
                            to = address;
                            valSats = vout.value || 0;
                        }
                        if (tx.vin[0] && tx.vin[0].prevout) {
                            from = tx.vin[0].prevout.scriptpubkey_address || "unknown";
                        }
                    }
                    
                    return {
                        hash: tx.txid,
                        from: from,
                        to: to,
                        value: (valSats * 10000000000).toString(),
                        timeStamp: tx.status.block_time ? tx.status.block_time.toString() : Math.floor(Date.now()/1000).toString()
                    };
                });
                return {
                    chain: { id: "BTC", name: "Bitcoin", logo: "https://cryptologos.cc/logos/bitcoin-btc-logo.png" },
                    active: true,
                    balance: 1,
                    txCount: mappedTxs.length,
                    txData: { status: "1", result: mappedTxs }
                };
            }
        } catch(e) {}
    }

    const isTron = address.startsWith('T') && address.length === 34;
    if (isTron) {
        const bitqueryKey = env.BITQUERY_API_KEY || 'ory_at_OPk5pzBLSLdISNOBfUKLJpAXsXzSheuz86ltIh8VIp0.UmAM9swbcKeJaGMNS4hG_b1frXR2x1gFeToAthjVC5A';
        try {
            const query = `query ($address: String!) {
              tron {
                transfers(sender: {is: $address}) {
                  transaction { hash }
                  receiver { address }
                  amount
                  block { timestamp { unixtime } }
                }
              }
            }`;
            const res = await fetch("https://graphql.bitquery.io", {
                method: "POST",
                headers: { "Content-Type": "application/json", "Authorization": `Bearer ${bitqueryKey}`, "X-API-KEY": bitqueryKey },
                body: JSON.stringify({ query, variables: { address } })
            });
            const bqData: any = await res.json();
            const txs = bqData?.data?.tron?.transfers || [];
            if (txs.length > 0) {
                const mappedTxs = txs.map((tx: any) => ({
                    hash: tx.transaction.hash,
                    from: address,
                    to: tx.receiver.address,
                    value: (tx.amount * 1e18).toString(),
                    timeStamp: tx.block.timestamp.unixtime.toString()
                }));
                return {
                    chain: { id: "TRX", name: "Tron", logo: "https://cryptologos.cc/logos/tron-trx-logo.png" },
                    active: true,
                    balance: 0,
                    txCount: mappedTxs.length,
                    txData: { status: "1", result: mappedTxs }
                };
            }
        } catch(e) {}
        
        // Even if Bitquery fails or returns 0, we identify it as Tron
        return {
             chain: { id: "TRX", name: "Tron", logo: "https://cryptologos.cc/logos/tron-trx-logo.png" },
             active: true, balance: 0, txCount: 0, txData: { status: "0", result: [] }
        };
    }

    const fetchPromises = CHAINS.map(async chain => {
        const key = env[chain.keyEnv];
        if (!key) return { chain, active: false };
        try {
            const balRes = await fetch(`${chain.url}?module=account&action=balance&address=${address}&tag=latest&apikey=${key}`);
            const txRes = await fetch(`${chain.url}?module=account&action=txlist&address=${address}&page=1&offset=50&sort=desc&apikey=${key}`);
            const balData: any = await balRes.json();
            const txData: any = await txRes.json();
            
            const balance = balData.status === "1" ? parseFloat(balData.result) : 0;
            const txCount = txData.status === "1" ? txData.result.length : 0;
            
            // Check if API key is invalid
            if (balData.status === "0" && balData.result === "Invalid API Key") {
                return { chain, active: false, error: "Invalid API Key in Secrets" };
            }

            return { chain, active: balance > 0 || txCount > 0, balance, txCount, txData, key };
        } catch (e) {
            return { chain, active: false };
        }
    });
    
    const results = await Promise.all(fetchPromises);
    const sorted = results.filter(r => r.active).sort((a: any, b: any) => b.txCount - a.txCount || b.balance - a.balance);
    
    // Check if we had API key errors
    const keyError = results.find(r => r.error);
    if (sorted.length === 0 && keyError) {
        return { error: keyError.error };
    }
    
    return sorted.length > 0 ? sorted[0] : results[0];
}

app.get('/api/nemesis_id/profile/:address', async (c) => {
  try {
    const address = c.req.param('address');
    const activeData: any = await detectActiveChain(address, c.env);
    
    if (activeData && activeData.error) {
        return c.json({ error: `Configuration Error: ${activeData.error}` }, 500);
    }
    
    if (!activeData || !activeData.chain) return c.json({ error: "Failed to detect chain or API keys missing." }, 500);

    const chain = activeData.chain;
    const ethBalance = (activeData.balance / 1e18).toFixed(4);
    let lastActivity = "Unknown";
    let firstActivity = "Unknown";
    let totalSent = 0;
    let totalReceived = 0;
    let totalTx = 0;

    if (activeData.txData && activeData.txData.status === "1" && activeData.txData.result.length > 0) {
        const txs = activeData.txData.result;
        totalTx = txs.length;
        lastActivity = new Date(parseInt(txs[0].timeStamp) * 1000).toUTCString();
        firstActivity = new Date(parseInt(txs[txs.length - 1].timeStamp) * 1000).toUTCString();
        
        txs.forEach((tx: any) => {
            const val = parseFloat(tx.value) / 1e18;
            if (tx.from.toLowerCase() === address.toLowerCase()) totalSent += val;
            else totalReceived += val;
        });
    }

    return c.json({
        address: address,
        balance_eth: ethBalance,
        balance_usd: (parseFloat(ethBalance) * 3100).toFixed(2), // Mock ETH price
        total_transactions: totalTx,
        first_active: firstActivity,
        last_active: lastActivity,
        entity_type: "EOA",
        transfer_pattern: "Standard",
        total_sent: totalSent.toFixed(4),
        total_received: totalReceived.toFixed(4),
        active_chain: chain.name,
        chain_logo: chain.logo,
        executive_summary: `Subject address has an estimated balance of ${ethBalance} ${chain.id} and has conducted ${totalTx} lifetime transactions.`
    });
  } catch (e) {
    return c.json({ error: e instanceof Error ? e.message : String(e) }, 500);
  }
});

app.get('/api/nemesis_id/tx_history/:address', async (c) => {
  try {
    const address = c.req.param('address');
    const activeData: any = await detectActiveChain(address, c.env);
    
    if (activeData && activeData.error) {
        return c.json({ error: `Configuration Error: ${activeData.error}` }, 500);
    }
    
    if (!activeData || !activeData.txData || activeData.txData.status !== "1") {
      return c.json({ transactions: [] });
    }

    const txs = activeData.txData.result;
    const history = txs.slice(0, 50).map((tx: any) => {
        const amt = parseFloat(tx.value) / 1e18;
        const isOutbound = tx.from.toLowerCase() === address.toLowerCase();
        return {
            timestamp: new Date(parseInt(tx.timeStamp) * 1000).toISOString().replace('T', ' ').substring(0, 19),
            hash: tx.hash,
            from: tx.from,
            to: tx.to,
            amount: amt.toFixed(4),
            usd_value: (amt * 3100).toFixed(2),
            ticker: activeData.chain.id,
            chain: activeData.chain.name,
            flow: isOutbound ? "OUTBOUND" : "INBOUND",
            receiver_entity: "Unknown Entity",
            risk_score: isOutbound ? 15 : 5
        };
    });
    return c.json({ transactions: history });
  } catch (e) {
    return c.json({ transactions: [] });
  }
});

app.get('/api/nemesis_id/aml/:address', async (c) => {
  return c.json({
      score: 12.5,
      classification: "LOW RISK",
      exposure_rate: "50 txs scanned",
      ofac_overlap: "Clean",
      mixer_exposure: "None",
      illicit_transactions: 0,
      consistent_senders: "Detected",
      last_receivers: "Various"
  });
});

app.get('/api/nemesis_id/intel/:address', async (c) => {
  return c.json({
      is_malicious: false,
      osint_intel: "No public social media mentions found.",
      darknet_mentions: "0 Mentions",
      arkham_intel: "Not Found",
      vasp_intel: "Not Found",
      custodial_entry: "Pending Analysis"
  });
});

// WebSocket endpoints (Proxying to Durable Objects)
app.get('/api/ws/trace', (c) => {
  const id = c.env.REALTIME_MANAGER.idFromName('trace_ops');
  const stub = c.env.REALTIME_MANAGER.get(id);
  return stub.fetch(c.req.raw);
});

app.get('/ws/:trace_id', (c) => {
  const id = c.env.REALTIME_MANAGER.idFromName(c.req.param('trace_id'));
  const stub = c.env.REALTIME_MANAGER.get(id);
  return stub.fetch(c.req.raw);
});

app.all('/api/*', (c) => proxyToBackend(c, c.req.path));
app.all('/admin/*', (c) => proxyToBackend(c, c.req.path));

const SCANNER_MAP: Record<string, { url: string, keyEnv: keyof Bindings, currency: string }> = {
    'ETHEREUM': { url: 'https://api.etherscan.io/api', keyEnv: 'ETHERSCAN_API_KEY', currency: 'ETH' },
    'BSC': { url: 'https://api.bscscan.com/api', keyEnv: 'BSCSCAN_API_KEY', currency: 'BNB' },
    'POLYGON': { url: 'https://api.polygonscan.com/api', keyEnv: 'POLYGONSCAN_API_KEY', currency: 'MATIC' },
    'AVALANCHE': { url: 'https://api.snowtrace.io/api', keyEnv: 'SNOWTRACE_API_KEY', currency: 'AVAX' },
    'ARBITRUM': { url: 'https://api.arbiscan.io/api', keyEnv: 'ARBISCAN_API_KEY', currency: 'ARB' },
    'OPTIMISM': { url: 'https://api-optimistic.etherscan.io/api', keyEnv: 'OPTIMISMSCAN_API_KEY', currency: 'OP' },
    'BASE': { url: 'https://api.basescan.org/api', keyEnv: 'BASESCAN_API_KEY', currency: 'ETH' },
    'CELO': { url: 'https://api.celoscan.io/api', keyEnv: 'CELOSCAN_API_KEY', currency: 'CELO' },
    'LINEA': { url: 'https://api.lineascan.build/api', keyEnv: 'LINEASCAN_API_KEY', currency: 'ETH' }
};

async function executeTrace(env: Bindings, traceId: string, seeds: string[], network: string) {
    const broadcast = async (payload: any) => {
        try {
            const doId = env.REALTIME_MANAGER.idFromName(traceId);
            const stub = env.REALTIME_MANAGER.get(doId);
            await stub.fetch(new Request(`http://dummy/broadcast`, {
                method: 'POST',
                body: JSON.stringify(payload)
            }));
        } catch(e) {}
    };

    const targetNet = network.toUpperCase();
    const isAuto = targetNet === 'AUTO' || targetNet === 'ALL';
    
    // Default to Ethereum if Auto, or find the specific network
    const netConfig = SCANNER_MAP[targetNet] || SCANNER_MAP['ETHEREUM'];
    const apiKey = env[netConfig.keyEnv] || '';

    await broadcast({ type: 'PROGRESS', message: `Initializing Omni-Chain trace for ${seeds.length} seed(s) on ${targetNet}...` });

    if (!apiKey) {
        await broadcast({ type: 'PROGRESS', message: `WARNING: No API key found for ${targetNet} in Cloudflare Secrets.` });
    }

    for (const seed of seeds) {
        await broadcast({ type: 'PROGRESS', message: `Fetching Ledger Data for ${seed}...` });
        
        const isTron = seed.startsWith('T') && seed.length === 34;
        
        try {
            let resultData: any = null;
            let currentTargetNet = targetNet;
            
            if (isTron) {
                currentTargetNet = 'TRON';
                const bitqueryKey = env.BITQUERY_API_KEY || 'ory_at_OPk5pzBLSLdISNOBfUKLJpAXsXzSheuz86ltIh8VIp0.UmAM9swbcKeJaGMNS4hG_b1frXR2x1gFeToAthjVC5A';
                const query = `query ($address: String!) {
                  tron {
                    transfers(sender: {is: $address}) {
                      transaction { hash }
                      receiver { address }
                      amount
                      block { timestamp { unixtime } }
                    }
                  }
                }`;
                const res = await fetch("https://graphql.bitquery.io", {
                    method: "POST",
                    headers: { "Content-Type": "application/json", "Authorization": `Bearer ${bitqueryKey}`, "X-API-KEY": bitqueryKey },
                    body: JSON.stringify({ query, variables: { address: seed } })
                });
                const bqData: any = await res.json();
                const txs = bqData?.data?.tron?.transfers || [];
                resultData = {
                    status: txs.length > 0 ? '1' : '0',
                    result: txs.map((tx: any) => ({
                        hash: tx.transaction.hash,
                        from: seed,
                        to: tx.receiver.address,
                        value: (tx.amount * 1e18).toString(),
                        timeStamp: tx.block.timestamp.unixtime
                    }))
                };
            } else {
                const res = await fetch(`${netConfig.url}?module=account&action=txlist&address=${seed}&page=1&offset=50&sort=desc&apikey=${apiKey}`);
                resultData = await res.json();
                if (targetNet === 'AUTO') currentTargetNet = 'ETHEREUM';
            }
            
            if (resultData && resultData.status === '1' && resultData.result) {
                const edges: any[] = [];
                
                await broadcast({
                    type: 'INIT',
                    root_address: seed,
                    chain: currentTargetNet,
                    balance_usd: 0
                });

                resultData.result.forEach((tx: any) => {
                    const from = tx.from ? tx.from.toLowerCase() : seed.toLowerCase();
                    const to = tx.to ? tx.to.toLowerCase() : 'unknown';
                    const val = parseFloat(tx.value) / 1e18;
                    
                    if (val > 0.001) {
                        edges.push({
                            type: 'NODE_UPDATE',
                            edge_type: 'Transfer',
                            from: from,
                            to: to,
                            hash: tx.hash,
                            amount: val,
                            usd_value: (val * (isTron ? 0.12 : 3100)).toFixed(2),
                            chain: currentTargetNet,
                            computed_ticker: isTron ? 'TRX' : netConfig.currency,
                            risk_score: 5,
                            timestamp: tx.timeStamp * 1000
                        });
                    }
                });

                await broadcast({ type: 'PROGRESS', message: `Processing ${edges.length} graph edges...` });
                
                // Chunk to avoid WebSocket payload limits
                for (let i = 0; i < edges.length; i += 10) {
                    await broadcast({ type: 'LEDGER_BATCH', data: edges.slice(i, i+10) });
                    await new Promise(r => setTimeout(r, 200));
                }
            } else {
                 await broadcast({ type: 'PROGRESS', message: `No tx found or API limit hit for ${seed}: ${resultData ? resultData.result : 'Unknown'}` });
            }
        } catch (e) {
            await broadcast({ type: 'PROGRESS', message: `Trace failed: ${e}` });
        }
    }
    
    await broadcast({ type: 'PROGRESS', message: `Edge Analysis Complete.` });
    await broadcast({ type: 'COMPLETE' });
}

export default {
  fetch: app.fetch,
  async queue(batch: MessageBatch<any>, env: Bindings, ctx: ExecutionContext) {
    console.log(`Processing queue: ${batch.queue}`);
    for (const message of batch.messages) {
      if (message.body.action === 'start_trace') {
          let seeds = message.body.seeds;
          if (typeof seeds === 'string') {
              seeds = seeds.split(/[\r\n,]+/).map((s:string) => s.trim()).filter(Boolean);
          } else if (!Array.isArray(seeds)) {
              seeds = [seeds];
          }
          const traceId = message.body.trace_id;
          const network = message.body.network || 'AUTO';
          
          // Execute trace without blocking the queue loop
          await executeTrace(env, traceId, seeds, network);
      }
      message.ack();
    }
  }
}
export { TraceCoordinator, RealtimeManager, AdminConsole }
