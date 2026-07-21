// ═══════════════════════════════════════════════════════════════
// NEMESIS v2 — Cloudflare Worker Backend
// Multi-chain blockchain intelligence, tracing, and graph engine
// ═══════════════════════════════════════════════════════════════

export class AdminConsole {
  constructor(state, env) { this.state = state; this.env = env; }
  async fetch(request) {
    const url = new URL(request.url);
    if (url.pathname === '/stats') {
      const addrs = await this.state.storage.get('address_count') || 0;
      const traces = await this.state.storage.get('trace_count') || 0;
      return json({ addrs, traces, ts: Date.now() });
    }
    return json({ status: 'admin-console', ts: Date.now() });
  }
}

export class RealtimeManager {
  constructor(state, env) { this.state = state; this.env = env; this.sessions = new Set(); }
  async fetch(request) {
    if (request.headers.get('Upgrade') !== 'websocket') return new Response('Expected WebSocket', { status: 426 });
    const pair = new WebSocketPair();
    const [client, server] = Object.values(pair);
    server.accept();
    this.sessions.add(server);
    server.send(JSON.stringify({ type: 'connected', ts: Date.now() }));
    server.addEventListener('message', (event) => {
      try { const msg = JSON.parse(event.data); if (msg.type === 'subscribe') server.send(JSON.stringify({ type: 'subscribed', channel: msg.channel })); } catch (e) {}
    });
    server.addEventListener('close', () => { this.sessions.delete(server); });
    return new Response(null, { status: 101, webSocket: client });
  }
}

export class TraceCoordinator {
  constructor(state, env) { this.state = state; this.env = env; }
  async fetch(request) {
    const url = new URL(request.url);
    if (url.pathname === '/status') {
      const active = await this.state.storage.get('active_traces') || [];
      return json({ activeTraces: active.length, traces: active });
    }
    if (url.pathname === '/start' && request.method === 'POST') {
      const body = await request.json();
      const traceId = crypto.randomUUID();
      const active = await this.state.storage.get('active_traces') || [];
      active.push({ traceId, address: body.address, chain: body.chain, startedAt: Date.now() });
      await this.state.storage.put('active_traces', active);
      return json({ traceId, status: 'started' });
    }
    return json({ status: 'trace-coordinator' });
  }
}

const CORS_HEADERS = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type,Authorization,X-API-Key',
  'Access-Control-Max-Age': '86400',
};

function json(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: {
      'Content-Type': 'application/json',
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type,Authorization,X-API-Key',
    },
  });
}

function err(message, status = 400) { return json({ error: message }, status); }

function getExplorerConfig(env, chain) {
  const configs = {
    ethereum: { url: 'https://api.etherscan.io/api', key: env.ETHERSCAN_API_KEY },
    bsc: { url: 'https://api.bscscan.com/api', key: env.BSCSCAN_API_KEY },
    polygon: { url: 'https://api.polygonscan.com/api', key: env.POLYGONSCAN_API_KEY },
    arbitrum: { url: 'https://api.arbiscan.io/api', key: env.ARBISCAN_API_KEY },
    optimism: { url: 'https://api-optimistic.etherscan.io/api', key: env.OPTIMISMSCAN_API_KEY },
    base: { url: 'https://api.basescan.org/api', key: env.BASESCAN_API_KEY },
    avalanche: { url: 'https://api.snowtrace.io/api', key: env.SNOWTRACE_API_KEY },
    celo: { url: 'https://api.celoscan.io/api', key: env.CELOSCAN_API_KEY },
    linea: { url: 'https://api.lineascan.build/api', key: env.LINEASCAN_API_KEY },
  };
  return configs[chain];
}

function getExplorerUrl(chain, address) {
  const urls = {
    ethereum: `https://etherscan.io/address/${address}`,
    bsc: `https://bscscan.com/address/${address}`,
    polygon: `https://polygonscan.com/address/${address}`,
    arbitrum: `https://arbiscan.io/address/${address}`,
    optimism: `https://optimistic.etherscan.io/address/${address}`,
    base: `https://basescan.org/address/${address}`,
    avalanche: `https://snowtrace.io/address/${address}`,
    celo: `https://celoscan.io/address/${address}`,
    linea: `https://lineascan.build/address/${address}`,
    bitcoin: `https://blockchair.com/bitcoin/address/${address}`,
    solana: `https://solscan.io/account/${address}`,
    tron: `https://tronscan.org/#/address/${address}`,
    ripple: `https://livenet.xrpl.org/accounts/${address}`,
  };
  return urls[chain] || null;
}

async function fetchBalance(env, address, chain) {
  const cfg = getExplorerConfig(env, chain);
  if (!cfg?.key) return '0';
  try {
    const url = `${cfg.url}?module=account&action=balance&address=${address}&tag=latest&apikey=${cfg.key}`;
    const res = await fetch(url);
    const data = await res.json();
    if (data.status === '1') return (parseInt(data.result) / 1e18).toString();
  } catch (e) {}
  return '0';
}

async function fetchTransactions(env, address, chain, limit = 50) {
  const cfg = getExplorerConfig(env, chain);
  if (!cfg?.key) return [];
  try {
    const url = `${cfg.url}?module=account&action=txlist&address=${address}&startblock=0&endblock=99999999&page=1&offset=${limit}&sort=desc&apikey=${cfg.key}`;
    const res = await fetch(url);
    const data = await res.json();
    if (data.status === '1') {
      return data.result.map(tx => ({
        hash: tx.hash, from: tx.from, to: tx.to,
        value: (parseInt(tx.value) / 1e18).toString(),
        timestamp: new Date(parseInt(tx.timeStamp) * 1000).toISOString(),
        blockNumber: parseInt(tx.blockNumber),
        gasUsed: parseInt(tx.gasUsed), gasPrice: parseInt(tx.gasPrice),
        isError: tx.isError === '1',
      }));
    }
  } catch (e) {}
  return [];
}

async function fetchTokenTransfers(env, address, chain, limit = 50) {
  const cfg = getExplorerConfig(env, chain);
  if (!cfg?.key) return [];
  try {
    const url = `${cfg.url}?module=account&action=tokentx&address=${address}&startblock=0&endblock=99999999&page=1&offset=${limit}&sort=desc&apikey=${cfg.key}`;
    const res = await fetch(url);
    const data = await res.json();
    if (data.status === '1') {
      return data.result.map(tx => ({
        hash: tx.hash, from: tx.from, to: tx.to,
        tokenSymbol: tx.tokenSymbol, tokenDecimal: parseInt(tx.tokenDecimal),
        value: (parseInt(tx.value) / Math.pow(10, parseInt(tx.tokenDecimal))).toString(),
        timestamp: new Date(parseInt(tx.timeStamp) * 1000).toISOString(),
      }));
    }
  } catch (e) {}
  return [];
}

function classifyEntity(label) {
  label = (label || '').toLowerCase();
  if (label.includes('exchange') || label.includes('binance') || label.includes('coinbase') || label.includes('kraken') || label.includes('okx') || label.includes('bybit')) return 'exchange';
  if (label.includes('bridge')) return 'bridge';
  if (label.includes('mixer') || label.includes('tornado')) return 'mixer';
  if (label.includes('contract')) return 'contract';
  if (label.includes('token')) return 'token';
  if (label.includes('wallet')) return 'wallet';
  if (label.includes('phishing') || label.includes('scam') || label.includes('hack')) return 'malicious';
  return 'unknown';
}

async function scrapeEntityLabel(env, address, chain) {
  if (env.ENTITY_CACHE) {
    try {
      const cached = await env.ENTITY_CACHE.get(`entity:${chain}:${address}`);
      if (cached) return JSON.parse(cached);
    } catch (e) {}
  }
  const cfg = getExplorerConfig(env, chain);
  if (cfg?.key) {
    try {
      const url = `${cfg.url}?module=account&action=addresslabel&address=${address}&apikey=${cfg.key}`;
      const res = await fetch(url);
      const data = await res.json();
      if (data.status === '1' && data.result) {
        const label = typeof data.result === 'string' ? data.result : data.result.label;
        if (label && label !== 'None') {
          const entity = { address, label, entity: label, type: classifyEntity(label), source: 'explorer', confidence: 0.75, chain, scrapedAt: Date.now() };
          if (env.ENTITY_CACHE) await env.ENTITY_CACHE.put(`entity:${chain}:${address}`, JSON.stringify(entity), { expirationTtl: 86400 });
          if (env.DB) {
            try { await env.DB.prepare('INSERT OR REPLACE INTO labels (id, address, label, label_type, confidence, source, chain) VALUES (?, ?, ?, ?, ?, ?, ?)').bind(crypto.randomUUID(), address, label, classifyEntity(label), 0.75, 'explorer', chain).run(); } catch (e) {}
          }
          return entity;
        }
      }
    } catch (e) {}
  }
  return null;
}

async function buildTransactionGraph(env, address, chain, maxDepth = 3) {
  const visited = new Set();
  const nodes = [];
  const edges = [];
  await bfsTraverse(env, address, chain, 0, maxDepth, visited, nodes, edges);
  for (let i = 0; i < nodes.length; i++) {
    const angle = (i / nodes.length) * 2 * Math.PI;
    nodes[i].x = Math.cos(angle) * (nodes[i].depth + 1) * 60;
    nodes[i].y = Math.sin(angle) * (nodes[i].depth + 1) * 60;
    nodes[i].size = Math.max(5, Math.min(25, (nodes[i].txCount || 1) * 2));
    nodes[i].color = nodes[i].riskScore > 0.7 ? '#ff0000' : nodes[i].riskScore > 0.5 ? '#ff6600' : nodes[i].riskScore > 0.3 ? '#ffcc00' : '#00cc00';
  }
  return { nodes, edges, metadata: { rootAddress: address, chain, depth: maxDepth, nodeCount: nodes.length, edgeCount: edges.length, builtAt: Date.now() } };
}

async function bfsTraverse(env, address, chain, depth, maxDepth, visited, nodes, edges) {
  const key = `${chain}:${address}`;
  if (visited.has(key) || depth > maxDepth || nodes.length >= 100) return;
  visited.add(key);
  const txs = await fetchTransactions(env, address, chain, 20);
  const entity = (env.AUTO_LABEL_WALLETS === 'true' || env.AUTO_SCRAPE_ENTITIES === 'true') ? await scrapeEntityLabel(env, address, chain) : null;
  nodes.push({ id: key, address, chain, depth, label: entity?.label || `${address.slice(0, 8)}...`, entity: entity?.entity || null, entityType: entity?.type || null, riskScore: entity?.type === 'malicious' ? 0.9 : entity?.type === 'mixer' ? 0.7 : entity?.type === 'exchange' ? 0.2 : 0, txCount: txs.length });
  const nextAddresses = new Set();
  for (const tx of txs) {
    if (tx.from && tx.to) {
      edges.push({ id: crypto.randomUUID(), source: `${chain}:${tx.from}`, target: `${chain}:${tx.to}`, txHash: tx.hash, value: parseFloat(tx.value) || 0, timestamp: tx.timestamp, chain });
      if (tx.from !== address && !visited.has(`${chain}:${tx.from}`)) nextAddresses.add(tx.from);
      if (tx.to !== address && !visited.has(`${chain}:${tx.to}`)) nextAddresses.add(tx.to);
    }
  }
  const batchSize = parseInt(env.PARALLEL_FETCH_LIMIT || '12');
  const batch = Array.from(nextAddresses).slice(0, batchSize);
  await Promise.allSettled(batch.map(addr => bfsTraverse(env, addr, chain, depth + 1, maxDepth, visited, nodes, edges)));
}

async function bitqueryQuery(env, query, variables = {}) {
  if (!env.BITQUERY_API_KEY) return null;
  try {
    const res = await fetch('https://graphql.bitquery.io', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-API-KEY': env.BITQUERY_API_KEY },
      body: JSON.stringify({ query, variables }),
    });
    return await res.json();
  } catch (e) { return null; }
}

async function aiAnalyze(env, prompt, model = null) {
  if (env.GEMINI_API_KEY) {
    try {
      const res = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=${env.GEMINI_API_KEY}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ contents: [{ parts: [{ text: prompt }] }], generationConfig: { temperature: 0.4, maxOutputTokens: 2048 } }),
      });
      const data = await res.json();
      if (data.candidates?.[0]?.content?.parts?.[0]?.text) return { text: data.candidates[0].content.parts[0].text, model: 'gemini-2.0-flash', provider: 'gemini' };
    } catch (e) {}
  }
  if (env.OPENAI_API_KEY && env.OPENAI_API_KEY !== 'sk-proj-nemesis-placeholder-fallback') {
    try {
      const res = await fetch('https://api.openai.com/v1/chat/completions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${env.OPENAI_API_KEY}` },
        body: JSON.stringify({ model: 'gpt-4o-mini', messages: [{ role: 'user', content: prompt }], temperature: 0.4, max_tokens: 2048 }),
      });
      const data = await res.json();
      if (data.choices?.[0]?.message?.content) return { text: data.choices[0].message.content, model: 'gpt-4o-mini', provider: 'openai' };
    } catch (e) {}
  }
  if (env.AI) {
    try {
      const result = await env.AI.run('@cf/meta/llama-3.1-8b-instruct', { prompt });
      if (result.response) return { text: result.response, model: 'llama-3.1-8b-instruct', provider: 'workers-ai' };
    } catch (e) {}
  }
  return { text: 'AI analysis unavailable — no provider configured', model: 'none', provider: 'none' };
}

async function persistAddress(env, address, chain, data) {
  if (!env.DB) return;
  try {
    await env.DB.prepare('INSERT OR REPLACE INTO addresses (id, address, chain, label, entity_name, entity_type, tx_count, balance, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime(\'now\'))').bind(crypto.randomUUID(), address, chain, data.label || null, data.entity || null, data.entityType || null, data.txCount || 0, data.balance || '0').run();
  } catch (e) {}
}

async function persistTransactions(env, address, chain, txs) {
  if (!env.DB || !txs.length) return;
  try {
    const stmt = env.DB.prepare('INSERT OR IGNORE INTO transactions (id, tx_hash, chain, from_address, to_address, value, block_number, block_timestamp, gas_used, gas_price, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)');
    for (const tx of txs.slice(0, 50)) {
      await stmt.bind(crypto.randomUUID(), tx.hash, chain, tx.from, tx.to, parseFloat(tx.value) || 0, tx.blockNumber || 0, tx.timestamp || null, tx.gasUsed || 0, tx.gasPrice || 0, tx.isError ? 0 : 1).run();
    }
  } catch (e) {}
}

async function persistTrace(env, traceId, address, chain, graph) {
  if (!env.DB) return;
  try {
    await env.DB.prepare('INSERT OR REPLACE INTO traces (id, trace_id, root_address, chain, max_depth, status, node_count, edge_count, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime(\'now\'))').bind(crypto.randomUUID(), traceId, address, chain, graph.metadata?.depth || 3, 'completed', graph.nodes?.length || 0, graph.edges?.length || 0).run();
    for (const node of (graph.nodes || []).slice(0, 100)) {
      await env.DB.prepare('INSERT OR IGNORE INTO trace_nodes (id, trace_id, address, depth, label, entity_name, is_root) VALUES (?, ?, ?, ?, ?, ?, ?)').bind(crypto.randomUUID(), traceId, node.address, node.depth, node.label, node.entity, node.depth === 0 ? 1 : 0).run();
    }
    for (const edge of (graph.edges || []).slice(0, 200)) {
      await env.DB.prepare('INSERT OR IGNORE INTO trace_edges (id, trace_id, source_address, target_address, tx_hash, value, depth) VALUES (?, ?, ?, ?, ?, ?, ?)').bind(crypto.randomUUID(), traceId, edge.source, edge.target, edge.txHash, edge.value, edge.depth || 0).run();
    }
  } catch (e) {}
}

async function saveReportToR2(env, traceId, reportData) {
  if (!env.REPORTS) return null;
  try {
    const key = `reports/${traceId}/${Date.now()}.json`;
    await env.REPORTS.put(key, JSON.stringify(reportData), { httpMetadata: { contentType: 'application/json' }, customMetadata: { traceId, createdAt: new Date().toISOString() } });
    return key;
  } catch (e) {}
  return null;
}

function addSecurityHeaders(response) {
  response.headers.set('Strict-Transport-Security', 'max-age=31536000; includeSubDomains; preload');
  response.headers.set('X-Content-Type-Options', 'nosniff');
  response.headers.set('X-Frame-Options', 'DENY');
  response.headers.set('Referrer-Policy', 'strict-origin-when-cross-origin');
  response.headers.set('Permissions-Policy', 'geolocation=(), microphone=(), camera=()');
  return response;
}

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    const path = url.pathname;
    const method = request.method;
    if (method === 'OPTIONS') return new Response(null, { status: 204, headers: CORS_HEADERS });
    let response;
    try {
      // Health
      if (path === '/health' || path === '/api/health') {
        response = json({ status: 'ok', version: '2.0.0', timestamp: Date.now(), services: { d1: !!env.DB, kv: !!env.NEMESIS_CACHE, r2: !!env.EVIDENCE, queues: !!env.TRACE_QUEUE, durableObjects: !!env.REALTIME_MANAGER, ai: !!env.AI } });
      }
      // Address Lookup
      else if (path === '/api/address' && method === 'GET') {
        const address = url.searchParams.get('address');
        const chain = url.searchParams.get('chain') || 'ethereum';
        const includeGraph = url.searchParams.get('graph') === 'true';
        const depth = parseInt(url.searchParams.get('depth') || '3');
        if (!address) { response = err('address parameter required'); }
        else {
          const [balanceResult, txResult, entityResult] = await Promise.allSettled([
            fetchBalance(env, address, chain),
            fetchTransactions(env, address, chain, 50),
            (env.AUTO_LABEL_WALLETS === 'true' || env.AUTO_SCRAPE_ENTITIES === 'true') ? scrapeEntityLabel(env, address, chain) : Promise.resolve(null),
          ]);
          const balance = balanceResult.status === 'fulfilled' ? balanceResult.value : '0';
          const transactions = txResult.status === 'fulfilled' ? txResult.value : [];
          const entity = entityResult.status === 'fulfilled' ? entityResult.value : null;
          const result = { address, chain, balance, transactions, label: entity?.label || null, entity: entity?.entity || null, entityType: entity?.type || null, txCount: transactions.length, explorerUrl: getExplorerUrl(chain, address) };
          if (includeGraph) result.graph = await buildTransactionGraph(env, address, chain, depth);
          await persistAddress(env, address, chain, result);
          await persistTransactions(env, address, chain, transactions);
          response = json(result);
        }
      }
      // Graph
      else if (path === '/api/graph' && method === 'GET') {
        const address = url.searchParams.get('address');
        const chain = url.searchParams.get('chain') || 'ethereum';
        const depth = parseInt(url.searchParams.get('depth') || '3');
        if (!address) { response = err('address parameter required'); }
        else { response = json(await buildTransactionGraph(env, address, chain, depth)); }
      }
      // Trace
      else if (path === '/api/trace' && method === 'POST') {
        const body = await request.json();
        const { address, chain, depth, hops } = body;
        if (!address) { response = err('address required'); }
        else {
          const traceId = crypto.randomUUID();
          if (env.TRACE_QUEUE) {
            try {
              await env.TRACE_QUEUE.send({ type: 'trace', traceId, address, chain: chain || 'ethereum', depth: depth || 3, hops: hops || 10 });
              response = json({ traceId, status: 'queued', message: 'Trace queued for processing' });
            } catch (e) {
              const graph = await buildTransactionGraph(env, address, chain || 'ethereum', depth || 3);
              await persistTrace(env, traceId, address, chain || 'ethereum', graph);
              response = json({ traceId, status: 'completed', graph });
            }
          } else {
            const graph = await buildTransactionGraph(env, address, chain || 'ethereum', depth || 3);
            await persistTrace(env, traceId, address, chain || 'ethereum', graph);
            response = json({ traceId, status: 'completed', nodeCount: graph.nodes.length, edgeCount: graph.edges.length });
          }
        }
      }
      // Batch
      else if (path === '/api/batch' && method === 'POST') {
        const body = await request.json();
        const { addresses, chain } = body;
        if (!addresses || !Array.isArray(addresses)) { response = err('addresses array required'); }
        else {
          const results = await Promise.allSettled(addresses.map(addr => fetchBalance(env, addr, chain || 'ethereum')));
          response = json({ results: results.map((r, i) => ({ address: addresses[i], balance: r.status === 'fulfilled' ? r.value : null })) });
        }
      }
      // Labels
      else if (path === '/api/labels' && method === 'GET') {
        const address = url.searchParams.get('address');
        const chain = url.searchParams.get('chain') || 'ethereum';
        if (!address) { response = err('address parameter required'); }
        else {
          if (env.DB) {
            try {
              const labels = await env.DB.prepare('SELECT * FROM labels WHERE address = ?').bind(address).all();
              if (labels.results.length) { response = json({ address, labels: labels.results }); }
              else { const entity = await scrapeEntityLabel(env, address, chain); response = json({ address, label: entity?.label || null, entity: entity?.entity || null, type: entity?.type || 'unknown' }); }
            } catch (e) { const entity = await scrapeEntityLabel(env, address, chain); response = json({ address, label: entity?.label || null, entity: entity?.entity || null, type: entity?.type || 'unknown' }); }
          } else { const entity = await scrapeEntityLabel(env, address, chain); response = json({ address, label: entity?.label || null, entity: entity?.entity || null, type: entity?.type || 'unknown' }); }
        }
      }
      // Entity Search
      else if (path === '/api/entity' && method === 'GET') {
        const q = url.searchParams.get('q');
        if (!q) { response = err('q parameter required'); }
        else {
          if (env.DB) {
            try {
              const results = await env.DB.prepare('SELECT * FROM addresses WHERE label LIKE ? OR entity_name LIKE ? OR address LIKE ? LIMIT 20').bind(`%${q}%`, `%${q}%`, `%${q}%`).all();
              response = json({ results: results.results, query: q });
            } catch (e) { response = json({ results: [], query: q }); }
          } else { response = json({ results: [], query: q }); }
        }
      }
      // Stats
      else if (path === '/api/stats' && method === 'GET') {
        if (env.DB) {
          try {
            const addrCount = await env.DB.prepare('SELECT COUNT(*) as c FROM addresses').first();
            const txCount = await env.DB.prepare('SELECT COUNT(*) as c FROM transactions').first();
            const traceCount = await env.DB.prepare('SELECT COUNT(*) as c FROM traces').first();
            const labelCount = await env.DB.prepare('SELECT COUNT(*) as c FROM labels').first();
            response = json({ addresses: addrCount?.c || 0, transactions: txCount?.c || 0, traces: traceCount?.c || 0, labels: labelCount?.c || 0 });
          } catch (e) { response = json({ error: 'database not initialized' }, 500); }
        } else { response = json({ error: 'no database binding' }, 500); }
      }
      // Providers
      else if (path === '/api/providers' && method === 'GET') {
        const providers = [];
        const chains = ['ethereum', 'bsc', 'polygon', 'arbitrum', 'optimism', 'base', 'avalanche', 'celo', 'linea'];
        for (const chain of chains) {
          const cfg = getExplorerConfig(env, chain);
          if (cfg?.key) providers.push({ chain, provider: 'blockchain-explorer', hasKey: true });
        }
        if (env.BITQUERY_API_KEY) providers.push({ chain: 'multi', provider: 'bitquery', hasKey: true });
        if (env.TATUM_API_KEY) providers.push({ chain: 'multi', provider: 'tatum', hasKey: true });
        if (env.ANKR_API_KEY) providers.push({ chain: 'multi', provider: 'ankr', hasKey: true });
        if (env.GEMINI_API_KEY) providers.push({ chain: 'n/a', provider: 'gemini-ai', hasKey: true });
        if (env.OPENAI_API_KEY && env.OPENAI_API_KEY !== 'sk-proj-nemesis-placeholder-fallback') providers.push({ chain: 'n/a', provider: 'openai', hasKey: true });
        if (env.AI) providers.push({ chain: 'n/a', provider: 'workers-ai', hasKey: true });
        response = json({ providers, total: providers.length });
      }
      // AI Analysis
      else if (path === '/api/ai/analyze' && method === 'POST') {
        const body = await request.json();
        const { prompt, address, chain, context } = body;
        if (!prompt && !address) { response = err('prompt or address required'); }
        else {
          let fullPrompt = prompt;
          if (address) {
            const txs = await fetchTransactions(env, address, chain || 'ethereum', 20);
            const entity = await scrapeEntityLabel(env, address, chain || 'ethereum');
            fullPrompt = `Analyze the blockchain address ${address} on ${chain || 'ethereum'}.\nEntity: ${entity?.label || 'Unknown'}\nTransaction count: ${txs.length}\nRecent transactions: ${JSON.stringify(txs.slice(0, 10))}\nProvide a risk assessment and entity identification analysis.\n${prompt || ''}`;
          }
          const result = await aiAnalyze(env, fullPrompt);
          response = json({ analysis: result.text, model: result.model, provider: result.provider });
        }
      }
      // Token Transfers
      else if (path === '/api/tokens' && method === 'GET') {
        const address = url.searchParams.get('address');
        const chain = url.searchParams.get('chain') || 'ethereum';
        if (!address) { response = err('address parameter required'); }
        else { const tokens = await fetchTokenTransfers(env, address, chain, 50); response = json({ address, chain, tokens }); }
      }
      // R2 Report Save
      else if (path === '/api/report' && method === 'POST') {
        const body = await request.json();
        const { traceId, reportData } = body;
        if (!traceId || !reportData) { response = err('traceId and reportData required'); }
        else {
          const key = await saveReportToR2(env, traceId, reportData);
          if (key) response = json({ status: 'saved', key, traceId });
          else response = json({ status: 'failed', message: 'R2 not configured' }, 500);
        }
      }
      // Bitquery Proxy
      else if (path === '/api/bitquery' && method === 'POST') {
        const body = await request.json();
        const { query, variables } = body;
        if (!query) { response = err('query required'); }
        else { const result = await bitqueryQuery(env, query, variables || {}); response = json(result || { error: 'Bitquery query failed' }); }
      }
      // WebSocket
      else if (path === '/ws' && request.headers.get('Upgrade') === 'websocket' && env.REALTIME_MANAGER) {
        const id = env.REALTIME_MANAGER.idFromName('global');
        response = env.REALTIME_MANAGER.get(id).fetch(request);
      }
      // 404
      else {
        response = json({ error: 'not found', path, endpoints: ['/health', '/api/address', '/api/graph', '/api/trace', '/api/batch', '/api/labels', '/api/entity', '/api/stats', '/api/providers', '/api/ai/analyze', '/api/tokens', '/api/report', '/api/bitquery', '/ws'] }, 404);
      }
    } catch (e) {
      response = json({ error: 'server error', message: e.message }, 500);
    }
    return addSecurityHeaders(response);
  },

  async queue(batch, env, ctx) {
    for (const msg of batch) {
      try {
        if (msg.body?.type === 'trace') {
          const graph = await buildTransactionGraph(env, msg.body.address, msg.body.chain || 'ethereum', msg.body.depth || 3);
          await persistTrace(env, msg.body.traceId, msg.body.address, msg.body.chain || 'ethereum', graph);
        }
        msg.ack();
      } catch (e) { msg.retry({ maxRetries: 3 }); }
    }
  },

  async scheduled(event, env, ctx) {
    ctx.waitUntil((async () => {
      const cfg = getExplorerConfig(env, 'ethereum');
      if (cfg?.key) {
        try {
          await fetch(`${cfg.url}?module=stats&action=ethsupply&apikey=${cfg.key}`);
          if (env.NEMESIS_CACHE) await env.NEMESIS_CACHE.put('provider:health', JSON.stringify({ ts: Date.now() }), { expirationTtl: 300 });
        } catch (e) {}
      }
    })());
  },
};
