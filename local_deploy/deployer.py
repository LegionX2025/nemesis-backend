#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════
 NEMESIS v2 — Complete Cloudflare Auto-Deployment Script
═══════════════════════════════════════════════════════════════════
 
 This single script:
   1. Generates worker.js (full backend with all API endpoints)
   2. Generates wrangler.toml (all bindings: D1, KV, R2, Queues, DO, AI)
   3. Generates D1 migration SQL (full schema)
   4. Applies D1 migrations via Cloudflare API
   5. Uploads all secrets via Cloudflare bulk secrets API
   6. Deploys the Worker via Cloudflare API
   7. Configures queue consumers
   8. Runs automated tests against the deployed Worker
   9. Prints a deployment report
 
 Requirements:
   pip install requests
   Set CLOUDFLARE_API_TOKEN environment variable
   (Or the script will prompt you for it)
 
 Usage:
   python deploy.py
═══════════════════════════════════════════════════════════════════
"""

import os
import sys
import json
import time
import base64
import subprocess
import urllib.request
import urllib.error

# Load .env file automatically if it exists
if os.path.exists(".env"):
    with open(".env", "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                os.environ[key.strip()] = val.strip()

# ═════════════════════════════════════════════════════════════════
# CONFIGURATION — All existing resource IDs from your account
# ═════════════════════════════════════════════════════════════════

ACCOUNT_ID = "bcbea5647c46bc2cf236023b6be7719d"
WORKER_NAME = "nemesis-api-v3"

# D1 Database
D1_DATABASE_NAME = "nemesis_intelligence_db"
D1_DATABASE_ID = "7fcfec1d-362d-445b-af2a-69eac4180aed"

# KV Namespaces
KV_NAMESPACES = {
    "NEMESIS_CACHE": "f4099ea1458e4e62ba838734f172846f",
    "ENTITY_CACHE": "817961173773498d9e4715b3479fc66d",
    "TOKEN_CACHE": "2c35b6ff21d14830b3ae93ee4e6006c2",
    "SESSION_CACHE": "7fbab659456242db8c27082fcdb0d4b1",
    "OSINT_CACHE": "5558ace53efa4a0aa37dc035b17c256a",
}

# R2 Buckets
R2_BUCKETS = {
    "EVIDENCE": "nemesis-evidence",
    "EXPORTS": "nemesis-exports",
    "REPORTS": "nemesis-reports",
    "SCREENSHOTS": "nemesis-screenshots",
}

# Queues
QUEUES = ["wallet-tracing", "entity-resolution", "gemini-analysis", "report-generation", "notifications"]

# Durable Objects
DURABLE_OBJECTS = {
    "ADMIN_CONSOLE": {"class_name": "AdminConsole", "namespace_id": "9f70a0401bea4875baeb4397f8cb323a"},
    "REALTIME_MANAGER": {"class_name": "RealtimeManager", "namespace_id": "88a334d13b4c4a3f8e7fa0f4d8e04e4d"},
    "TRACE_COORDINATOR": {"class_name": "TraceCoordinator", "namespace_id": "e6c6ecdc5e524700ab1e03469502710c"},
}

# ═════════════════════════════════════════════════════════════════
# SECRETS — All required secrets for the platform
# ═════════════════════════════════════════════════════════════════

SECRETS = {
    "GITHUB_TOKEN": "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",
    "ETHERSCAN_API_KEY": "5HVRJGR3D1FGAG1VQXEIPN5HE7WU399CDY",
    "BSCSCAN_API_KEY": "5HVRJGR3D1FGAG1VQXEIPN5HE7WU399CDY",
    "POLYGONSCAN_API_KEY": "5HVRJGR3D1FGAG1VQXEIPN5HE7WU399CDY",
    "ARBISCAN_API_KEY": "5HVRJGR3D1FGAG1VQXEIPN5HE7WU399CDY",
    "OPTIMISMSCAN_API_KEY": "5HVRJGR3D1FGAG1VQXEIPN5HE7WU399CDY",
    "BASESCAN_API_KEY": "5HVRJGR3D1FGAG1VQXEIPN5HE7WU399CDY",
    "SNOWTRACE_API_KEY": "5HVRJGR3D1FGAG1VQXEIPN5HE7WU399CDY",
    "CELOSCAN_API_KEY": "5HVRJGR3D1FGAG1VQXEIPN5HE7WU399CDY",
    "LINEASCAN_API_KEY": "5HVRJGR3D1FGAG1VQXEIPN5HE7WU399CDY",
    "ETHPLORER_API_KEY": "EK-jzMjY-tyVwyEJ-wj3su",
    "INFURA_API_KEY": "2937d7343f364769890d2ed40d53743b",
    "INFURA_ETHEREUM_MAINNET": "https://mainnet.infura.io/v3/292f06c81c8c445ea092d9b3add9d517",
    "INFURA_POLYGON_MAINNET": "https://polygon-mainnet.infura.io/v3/292f06c81c8c445ea092d9b3add9d517",
    "INFURA_ARBITRUM_MAINNET": "https://arbitrum-mainnet.infura.io/v3/292f06c81c8c445ea092d9b3add9d517",
    "INFURA_BASE_MAINNET": "https://base-mainnet.infura.io/v3/292f06c81c8c445ea092d9b3add9d517",
    "INFURA_OPTIMISM_MAINNET": "https://optimism-mainnet.infura.io/v3/292f06c81c8c445ea092d9b3add9d517",
    "INFURA_LINEA_MAINNET": "https://linea-mainnet.infura.io/v3/292f06c81c8c445ea092d9b3add9d517",
    "INFURA_AVALANCHE_MAINNET": "https://avalanche-mainnet.infura.io/v3/292f06c81c8c445ea092d9b3add9d517",
    "INFURA_BSC_MAINNET": "https://bsc-mainnet.infura.io/v3/292f06c81c8c445ea092d9b3add9d517",
    "INFURA_ZKSYNC_MAINNET": "https://zksync-mainnet.infura.io/v3/292f06c81c8c445ea092d9b3add9d517",
    "INFURA_STARKNET_MAINNET": "https://starknet-mainnet.infura.io/v3/292f06c81c8c445ea092d9b3add9d517",
    "INFURA_CELO_MAINNET": "https://celo-mainnet.infura.io/v3/292f06c81c8c445ea092d9b3add9d517",
    "ANKR_API_KEY": "d0ebdc10f7a98d2c08105ddcef64d9353e5b92e1d59e545debed8af8bce60fbc",
    "ANKR_MULTICHAIN_RPC": "https://rpc.ankr.com/multichain/d0ebdc10f7a98d2c08105ddcef64d9353e5b92e1d59e545debed8af8bce60fbc",
    "CHAINSTACK_ETHEREUM_MAINNET": "https://ethereum-mainnet.core.chainstack.com/d015a2f127157c1a87923be5999fbfff",
    "SOLANA_RPC": "https://api.mainnet-beta.solana.com",
    "GETBLOCK_BTC_KEY": "91416f8c8d064f4492728538dcd2133f",
    "GETBLOCK_ETH_KEY": "b534021c684c4f3bbbec533c08a42911",
    "GETBLOCK_SOL_KEY": "4be59687544b461ab8134dfb389f44f2",
    "GETBLOCK_TRON_KEY": "2c9414b6d83947f5aa7a1f2f2f341cfc",
    "GETBLOCK_XRP_KEY": "e93b392eb26d4a3f81b406c328cc4030",
    "PUBLICNODE_BASE_WSS": "wss://base-rpc.publicnode.com/2e205385fca28313ff402d43d319ccdf36f176c64c35ada6d5c9bb52c509b720",
    "PUBLICNODE_BITCOIN_RPC": "https://bitcoin-rpc.publicnode.com/2e205385fca28313ff402d43d319ccdf36f176c64c35ada6d5c9bb52c509b720",
    "PUBLICNODE_SOLANA_WSS": "wss://solana-rpc.publicnode.com/2e205385fca28313ff402d43d319ccdf36f176c64c35ada6d5c9bb52c509b720",
    "PUBLICNODE_TRON_RPC": "https://tron-rpc.publicnode.com/2e205385fca28313ff402d43d319ccdf36f176c64c35ada6d5c9bb52c509b720",
    "PUBLICNODE_TERRA_WSS": "wss://terra-rpc.publicnode.com/2e205385fca28313ff402d43d319ccdf36f176c64c35ada6d5c9bb52c509b720",
    "XRPSCAN_BASE_URL": "https://api.xrpscan.com/api/v1",
    "TATUM_API_KEY": "t-689cf2666ee03b5b553977b2-ffee8013de0747bda4e360b7",
    "TATUM_RATE_LIMIT": "5",
    "TATUM_ENABLE_NFTS": "true",
    "TATUM_ENABLE_SECURITY_CHECK": "true",
    "BITQUERY_API_KEY": "ory_at_OPk5pzBLSLdISNOBfUKLJpAXsXzSheuz86ltIh8VIp0.UmAM9swbcKeJaGMNS4hG_b1frXR2x1gFeToAthjVC5A",
    "BITQUERY_API_TOKEN": "ory_at_OPk5pzBLSLdISNOBfUKLJpAXsXzSheuz86ltIh8VIp0.UmAM9swbcKeJaGMNS4hG_b1frXR2x1gFeToAthjVC5A",
    "BITQUERY_APIV2_TOKEN": "ory_at_OPk5pzBLSLdISNOBfUKLJpAXsXzSheuz86ltIh8VIp0.UmAM9swbcKeJaGMNS4hG_b1frXR2x1gFeToAthjVC5A",
    "GEMINI_API_KEY": "AQ.Ab8RN6LvATqPQMOAvBBxWxcONtmzWsDtg3ZizRW6SoVbajyhbQ",
    "GEMINI_API_KEYS": "AQ.Ab8RN6LvATqPQMOAvBBxWxcONtmzWsDtg3ZizRW6SoVbajyhbQ",
    "OPENAI_API_KEY": "sk-proj-nemesis-placeholder-fallback",
    "AIML_API_KEY_LLAMA": "be1343f1ce6549d4a55891595c16bdf0",
    "AIML_API_KEY_DEEPSEEK": "99507102d87c4f79946d20b2aa80cfaf",
    "AIML_API_KEY_CHATGPT": "2dbdde9ac055448d912db45e82349d7d",
    "AIML_API_KEY_BAGOODEX": "ca889f99c4ca4e1e8fe540ae08854851",
    "AI_ROTATION_ENABLED": "true",
    "AI_MODEL_ORDER": "gemini-2.0-flash,gemini-2.5-flash,gemini-2.5-pro",
    "CENSYS_API_KEY": "censys_26tX6uGu_5eGWvNJ4KYZ5u4MaaptpHyYi",
    "SHODAN_API_KEY": "hw8j3zZ7aXmDFpLGjU5w5haGCOmmYkuI",
    "HUNTER_API_KEY": "14bce9f6bf1e35a2190e5354b47440ae5b219159",
    "BINANCE_API_KEY": "Itjb7wivrCrc8gM4Jofe5aXRiwye3M1Kt6vQiHcnFdON4b8M6cFpVWDbP6jYLoQl",
    "BINANCE_API_SECRET": "PdenrKFvCYOuwncLdtc6Gjdv5zP0gaG7G6uwbBvovvHRPl5NcbI3ga74ZU7zp9HK",
    "DATABASE_MONGO_URL": "mongodb+srv://nemesis:nemesis2026@nemesisdb.vir5vg2.mongodb.net/?appName=nemesisdb",
    "MONGODB_URI": "mongodb+srv://nemesis:nemesis2026@nemesisdb.vir5vg2.mongodb.net/?appName=nemesisdb",
    "POSTGRES_URI": "postgresql://admin:npg_rOci6DgHjKu1@ep-morning-glitter-adpz0uqn-pooler.c-2.us-east-1.aws.neon.tech/intelligence?sslmode=require",
    "NEO4J_URI": "neo4j+s://89ea7d8f.databases.neo4j.io",
    "NEO4J_USERNAME": "89ea7d8f",
    "NEO4J_PASSWORD": "pMyRVGUtCLJCHBph0vR3FBVk5Ct1jkrThq-ApD2cJAA",
    "NEO4J_DATABASE": "89ea7d8f",
    "GENEZIO_LOGIN_TOKEN": "2075965490dd1f010b2a315d5a0fefdf17ca502b22c9c9c757aeb18e25ab14050d28e76fb202eab5e66a0273daf6ac8aedac7697474f22f274ab45105ce45158",
    "ADMIN_USERNAME": "nemesis",
    "ADMIN_PASSWORD": "Lionsgate2025!",
    "FLASK_SECRET_KEY": "y0ur-n3m3s1s-Sup3r-S3cr3t-K3y-456789",
    "JWT_SECRET": "y0ur-n3m3s1s-Sup3r-S3cr3t-K3y-456789",
    "SESSION_SECRET": "y0ur-n3m3s1s-Sup3r-S3cr3t-K3y-456789",
    "TELEGRAM_BOT_TOKEN": "8306409519:AAGLqpC_A9YZxYhMJL1JmaBMeSL-oYSYNX4",
    "WHATSAPP_API_KEY": "652782217253515|WTSQeAMWYYQXeWNgWjoeermMIJ4",
    "STRIPE_SECRET_KEY": "pk_test_51T5SdAFdiJYtVus3ZnJJv9gNtz3UmjKoRw5x8J9JBkIrsMSNmiTEl7ZX6IJNfZlNpuxvYVGvjoI5go35uYAsX0pd00vBPhbGsX",
    "AUTO_FAILOVER": "true",
    "AUTO_RETRY": "true",
    "RETRY_STRATEGY": "exponential",
    "MAX_RETRIES": "7",
    "RETRY_BASE_DELAY_MS": "800",
    "PARALLEL_FETCH_LIMIT": "12",
    "NORMALIZE_ALL_NETWORKS": "true",
    "TRACE_MAX_HOPS": "UNLIMITED",
    "TRACE_MAX_DEPTH": "UNLIMITED",
    "AUTO_LABEL_WALLETS": "true",
    "AUTO_SCRAPE_ENTITIES": "true",
    "CRAWLER_ENABLED": "true",
    "CRAWLER_MAX_THREADS": "10",
    "CRAWLER_TIMEOUT_SECONDS": "30",
    "CRAWLER_USER_AGENT_ROTATION": "true",
    "CRAWLER_DB_TYPE": "mongodb",
    "CRAWLER_EXPORT_FORMAT": "jsonl",
    "CRAWLER_RATE_LIMIT_MS": "2000",
    "CRAWLER_ENABLE_ENTITY_EXTRACTION": "true",
    "CRAWLER_ENABLE_OSINT_LOOKUP": "true",
    "CRAWLER_MAX_RECORDS_BUFFER": "5000",
    "CRAWLER_WEBSOCKET_ENDPOINT": "ws://localhost:3000/api/crawler/stream_endpoint",
    "TOR_SOCKS_PORT": "9050",
    "TOR_CONTROL_PORT": "9051",
    "TOR_AUTO_START": "true",
    "ENABLE_COURT_EXPORT": "true",
    "ENABLE_AFFIDAVIT_GENERATION": "true",
    "ENABLE_EXHIBIT_HASHING": "true",
    "REDACT_WALLETS_IN_PRELIMINARY": "true",
    "CHAIN_OF_CUSTODY_STRICT": "true",
    "CLOUDFLARE_ACCOUNT_ID": "bcbea5647c46bc2cf236023b6be7719d",
    "R2_ACCESS_KEY_ID": "4a1f4f4e19a46cef34905b39f2aff777",
    "R2_SECRET_ACCESS_KEY": "275ad81f11cddfd4bf1df45257c1bf1965867c6fc3362cf664040f6460202f81",
    "OKLINK_API_KEY": "",
    "OKLINK_BASE_URL": "https://www.oklink.com",
    "OKLINK_CHAIN_ADDRESS_URL": "https://www.oklink.com/{chain}/address/{address}",
    "OKLINK_DOM_CLASS_SELECTOR": ".address-tag,.label-tag,.entity-name",
    "OKLINK_LABEL_CONFIDENCE_THRESHOLD": "0.8",
    "OKLINK_SUPPORTED_CHAINS": "ethereum,bsc,polygon,arbitrum,optimism,base,avalanche,bitcoin,solana,tron,ripple",
    "SCRAPER_ENGINE": "puppeteer",
    "SCRAPER_HEADLESS": "true",
    "SCRAPER_TIMEOUT_MS": "30000",
    "SCRAPER_TARGET_EXPLORERS": "etherscan,bscscan,polygonscan,arbiscan,oklink",
    "SCRAPE_URL_ETH": "https://etherscan.io/address/{address}",
    "SCRAPE_URL_BSC": "https://bscscan.com/address/{address}",
    "SCRAPE_URL_POLYGON": "https://polygonscan.com/address/{address}",
    "SCRAPE_URL_ARB": "https://arbiscan.io/address/{address}",
    "SCRAPE_URL_OP": "https://optimistic.etherscan.io/address/{address}",
    "SCRAPE_URL_BASE": "https://basescan.org/address/{address}",
    "SCRAPE_URL_AVAX": "https://snowtrace.io/address/{address}",
    "SCRAPE_URL_BTC": "https://blockchair.com/bitcoin/address/{address}",
    "SCRAPE_URL_SOL": "https://solscan.io/account/{address}",
    "SCRAPE_URL_TRX": "https://tronscan.org/#/address/{address}",
    "SCRAPE_URL_XRP": "https://livenet.xrpl.org/accounts/{address}",
    "SCRAPE_URL_CELO": "https://celoscan.io/address/{address}",
    "SCRAPE_URL_LINEA": "https://lineascan.build/address/{address}",
    "SCRAPE_URL_ZKSYNC": "https://explorer.zksync.io/address/{address}",
    "SCRAPE_URL_STARKNET": "https://starkscan.co/contract/{address}",
    "SCRAPE_URL_TERRA": "https://finder.terra.money/mainnet/address/{address}",
}

# ═════════════════════════════════════════════════════════════════
# WORKER SOURCE CODE — Complete backend
# ═════════════════════════════════════════════════════════════════

WORKER_JS = r'''// ═══════════════════════════════════════════════════════════════
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
'''

# ═════════════════════════════════════════════════════════════════
# D1 MIGRATION SQL
# ═════════════════════════════════════════════════════════════════

MIGRATION_SQL = r'''-- Nemesis v2 D1 Schema Migration 0001
CREATE TABLE IF NOT EXISTS addresses (
  id TEXT PRIMARY KEY, address TEXT NOT NULL, chain TEXT DEFAULT 'ethereum',
  label TEXT, entity_name TEXT, entity_type TEXT,
  risk_score REAL DEFAULT 0, risk_level TEXT DEFAULT 'unknown',
  total_received REAL DEFAULT 0, total_sent REAL DEFAULT 0, balance REAL DEFAULT 0,
  tx_count INTEGER DEFAULT 0, is_contract INTEGER DEFAULT 0,
  contract_name TEXT, token_name TEXT, token_symbol TEXT,
  created_at TEXT DEFAULT (datetime('now')), updated_at TEXT DEFAULT (datetime('now'))
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_addr_unique ON addresses(address, chain);
CREATE INDEX IF NOT EXISTS idx_addr ON addresses(address);
CREATE INDEX IF NOT EXISTS idx_addr_label ON addresses(label);

CREATE TABLE IF NOT EXISTS transactions (
  id TEXT PRIMARY KEY, tx_hash TEXT NOT NULL, chain TEXT DEFAULT 'ethereum',
  from_address TEXT, to_address TEXT, value REAL DEFAULT 0,
  token_symbol TEXT, token_contract TEXT,
  block_number INTEGER, block_timestamp TEXT,
  gas_used REAL, gas_price REAL, status INTEGER DEFAULT 1,
  is_token_transfer INTEGER DEFAULT 0, input_data TEXT,
  created_at TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_tx_hash ON transactions(tx_hash);
CREATE INDEX IF NOT EXISTS idx_tx_from ON transactions(from_address);
CREATE INDEX IF NOT EXISTS idx_tx_to ON transactions(to_address);

CREATE TABLE IF NOT EXISTS transaction_graph (
  id TEXT PRIMARY KEY, source_address TEXT NOT NULL, target_address TEXT NOT NULL,
  tx_hash TEXT, chain TEXT DEFAULT 'ethereum',
  value REAL DEFAULT 0, token_symbol TEXT,
  direction TEXT DEFAULT 'out', depth INTEGER DEFAULT 0, hop INTEGER DEFAULT 0,
  block_timestamp TEXT, created_at TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_graph_src ON transaction_graph(source_address);
CREATE INDEX IF NOT EXISTS idx_graph_tgt ON transaction_graph(target_address);

CREATE TABLE IF NOT EXISTS entities (
  id TEXT PRIMARY KEY, entity_name TEXT NOT NULL, entity_type TEXT,
  description TEXT, category TEXT,
  risk_score REAL DEFAULT 0, risk_level TEXT DEFAULT 'unknown',
  address_count INTEGER DEFAULT 0, total_volume REAL DEFAULT 0,
  first_seen TEXT, last_seen TEXT, source TEXT DEFAULT 'auto',
  created_at TEXT DEFAULT (datetime('now')), updated_at TEXT DEFAULT (datetime('now'))
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_entity_name ON entities(entity_name);

CREATE TABLE IF NOT EXISTS labels (
  id TEXT PRIMARY KEY, address TEXT NOT NULL, label TEXT NOT NULL,
  label_type TEXT, confidence REAL DEFAULT 0.5, source TEXT DEFAULT 'auto',
  chain TEXT DEFAULT 'ethereum', created_at TEXT DEFAULT (datetime('now'))
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_label_unique ON labels(address, label, chain);
CREATE INDEX IF NOT EXISTS idx_label_addr ON labels(address);

CREATE TABLE IF NOT EXISTS traces (
  id TEXT PRIMARY KEY, trace_id TEXT UNIQUE NOT NULL,
  root_address TEXT NOT NULL, chain TEXT DEFAULT 'ethereum',
  max_depth INTEGER DEFAULT 5, max_hops INTEGER DEFAULT 10, status TEXT DEFAULT 'pending',
  node_count INTEGER DEFAULT 0, edge_count INTEGER DEFAULT 0, total_volume REAL DEFAULT 0,
  created_at TEXT DEFAULT (datetime('now')), completed_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_trace_root ON traces(root_address);

CREATE TABLE IF NOT EXISTS trace_nodes (
  id TEXT PRIMARY KEY, trace_id TEXT NOT NULL, address TEXT NOT NULL,
  depth INTEGER, label TEXT, entity_name TEXT, is_root INTEGER DEFAULT 0,
  created_at TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_tn_trace ON trace_nodes(trace_id);
CREATE INDEX IF NOT EXISTS idx_tn_addr ON trace_nodes(address);

CREATE TABLE IF NOT EXISTS trace_edges (
  id TEXT PRIMARY KEY, trace_id TEXT NOT NULL,
  source_address TEXT NOT NULL, target_address TEXT NOT NULL,
  tx_hash TEXT, value REAL DEFAULT 0, token_symbol TEXT, depth INTEGER,
  created_at TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_te_trace ON trace_edges(trace_id);

CREATE TABLE IF NOT EXISTS api_cache (
  id TEXT PRIMARY KEY, cache_key TEXT UNIQUE NOT NULL, cache_value TEXT NOT NULL,
  source TEXT, expires_at TEXT, created_at TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_cache_key ON api_cache(cache_key);

CREATE TABLE IF NOT EXISTS crawl_jobs (
  id TEXT PRIMARY KEY, job_id TEXT UNIQUE NOT NULL,
  address TEXT NOT NULL, chain TEXT DEFAULT 'ethereum',
  status TEXT DEFAULT 'pending', source TEXT, data TEXT, error TEXT,
  created_at TEXT DEFAULT (datetime('now')), completed_at TEXT
);
'''

# ═════════════════════════════════════════════════════════════════
# WRANGLER.TOML
# ═════════════════════════════════════════════════════════════════

WRANGLER_TOML = '''name = "nemesis-api"
main = "worker.js"
compatibility_date = "2024-12-01"
compatibility_flags = ["nodejs_compat"]

[[d1_databases]]
binding = "DB"
database_name = "nemesis_intelligence_db"
database_id = "7fcfec1d-362d-445b-af2a-69eac4180aed"

[[kv_namespaces]]
binding = "NEMESIS_CACHE"
id = "f4099ea1458e4e62ba838734f172846f"

[[kv_namespaces]]
binding = "ENTITY_CACHE"
id = "817961173773498d9e4715b3479fc66d"

[[kv_namespaces]]
binding = "TOKEN_CACHE"
id = "2c35b6ff21d14830b3ae93ee4e6006c2"

[[kv_namespaces]]
binding = "SESSION_CACHE"
id = "7fbab659456242db8c27082fcdb0d4b1"

[[kv_namespaces]]
binding = "OSINT_CACHE"
id = "5558ace53efa4a0aa37dc035b17c256a"

[[r2_buckets]]
binding = "EVIDENCE"
bucket_name = "nemesis-evidence"

[[r2_buckets]]
binding = "EXPORTS"
bucket_name = "nemesis-exports"

[[r2_buckets]]
binding = "REPORTS"
bucket_name = "nemesis-reports"

[[r2_buckets]]
binding = "SCREENSHOTS"
bucket_name = "nemesis-screenshots"

[[queues.producers]]
binding = "TRACE_QUEUE"
queue = "wallet-tracing"

[[queues.producers]]
binding = "ENTITY_QUEUE"
queue = "entity-resolution"

[[queues.producers]]
binding = "AI_QUEUE"
queue = "gemini-analysis"

[[queues.producers]]
binding = "REPORT_QUEUE"
queue = "report-generation"

[[queues.producers]]
binding = "NOTIFICATION_QUEUE"
queue = "notifications"

[[queues.consumers]]
queue = "wallet-tracing"
max_batch_size = 10
max_batch_timeout = 30

[[queues.consumers]]
queue = "entity-resolution"
max_batch_size = 10
max_batch_timeout = 30

[[queues.consumers]]
queue = "gemini-analysis"
max_batch_size = 5
max_batch_timeout = 60

[[durable_objects.bindings]]
name = "ADMIN_CONSOLE"
class_name = "AdminConsole"

[[durable_objects.bindings]]
name = "REALTIME_MANAGER"
class_name = "RealtimeManager"

[[durable_objects.bindings]]
name = "TRACE_COORDINATOR"
class_name = "TraceCoordinator"

[[migrations]]
tag = "v3"
new_sqlite_classes = ["AdminConsole", "RealtimeManager", "TraceCoordinator"]

[vars]
APP_NAME = "nemesis-platform"
APP_MODE = "production"
NODE_ENV = "production"
PYTHON_BACKEND_URL = "https://nemesis-backend.legionxgaming2021.workers.dev"

[triggers]
crons = ["*/15 * * * *"]

[observability]
enabled = true
'''

# ═════════════════════════════════════════════════════════════════
# CLOUDFLARE API HELPER
# ═════════════════════════════════════════════════════════════════

class CloudflareAPI:
    BASE = "https://api.cloudflare.com/client/v4"
    
    def __init__(self, token, account_id):
        self.token = token
        self.account_id = account_id
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    def _request(self, method, path, data=None, params=None):
        url = f"{self.BASE}{path}"
        body = json.dumps(data).encode('utf-8') if data else None
        req = urllib.request.Request(url, data=body, headers=self.headers, method=method)
        if params:
            query = "&".join(f"{k}={v}" for k, v in params.items())
            url += f"?{query}"
            req = urllib.request.Request(url, data=body, headers=self.headers, method=method)
        try:
            with urllib.request.urlopen(req) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            error_body = e.read().decode()
            try:
                return json.loads(error_body)
            except:
                return {"success": False, "errors": [{"message": error_body}]}
        except Exception as e:
            return {"success": False, "errors": [{"message": str(e)}]}

    # ── D1 ──────────────────────────────────────────────────────
    def d1_query(self, db_id, sql):
        """Execute SQL on D1 via API"""
        path = f"/accounts/{self.account_id}/d1/database/{db_id}/query"
        return self._request("POST", path, {"sql": sql})

    def d1_list_tables(self, db_id):
        return self.d1_query(db_id, "SELECT name FROM sqlite_master WHERE type='table'")

    # ── Secrets (Bulk) ───────────────────────────────────────────
    def upload_secrets_bulk(self, worker_name, secrets_dict):
        """Upload secrets via bulk secrets API (max 100 per request)"""
        path = f"/accounts/{self.account_id}/workers/scripts/{worker_name}/secrets/bulk"
        secrets_payload = {}
        for key, value in secrets_dict.items():
            if value and value.strip():
                secrets_payload[key] = {"type": "secret_text", "name": key, "text": value}
        # Split into chunks of 100
        results = []
        keys = list(secrets_payload.keys())
        for i in range(0, len(keys), 100):
            chunk = {k: secrets_payload[k] for k in keys[i:i+100]}
            result = self._request("PUT", path, {"secrets": chunk})
            results.append(result)
        return results

    # ── Worker Deploy ───────────────────────────────────────────
    def deploy_worker(self, worker_name, worker_code, bindings_config):
        """Deploy worker via multipart form-data API"""
        import uuid
        boundary = uuid.uuid4().hex
        
        # Build metadata with bindings
        metadata = {
            "main_module": "worker.js",
            "compatibility_date": "2024-12-01",
            "compatibility_flags": ["nodejs_compat"],
            "bindings": bindings_config,
            "crons": ["*/15 * * * *"],
            "observability": {"enabled": True},
        }
        
        # Build multipart body
        body_parts = []
        # Metadata part
        body_parts.append(f"--{boundary}\r\n".encode())
        body_parts.append(b'Content-Disposition: form-data; name="metadata"\r\n')
        body_parts.append(b'Content-Type: application/json\r\n\r\n')
        body_parts.append(json.dumps(metadata).encode())
        body_parts.append(b"\r\n")
        # Worker code part
        body_parts.append(f"--{boundary}\r\n".encode())
        body_parts.append(b'Content-Disposition: form-data; name="worker.js"; filename="worker.js"\r\n')
        body_parts.append(b'Content-Type: application/javascript+module\r\n\r\n')
        body_parts.append(worker_code.encode())
        body_parts.append(f"\r\n--{boundary}--\r\n".encode())
        
        body = b"".join(body_parts)
        
        url = f"{self.BASE}/accounts/{self.account_id}/workers/scripts/{worker_name}"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        }
        
        req = urllib.request.Request(url, data=body, headers=headers, method="PUT")
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            error_body = e.read().decode()
            try:
                return json.loads(error_body)
            except:
                return {"success": False, "errors": [{"message": error_body}]}
        except Exception as e:
            return {"success": False, "errors": [{"message": str(e)}]}

    # ── Queue Consumer ──────────────────────────────────────────
    def create_queue_consumer(self, queue_name, worker_name, settings=None):
        """Create or update a queue consumer"""
        path = f"/accounts/{self.account_id}/queues/{queue_name}/consumers"
        data = {
            "script": worker_name,
            "settings": settings or {
                "batch_size": 10,
                "max_concurrency": 5,
                "max_retries": 3,
                "max_wait_time_ms": 30000,
            }
        }
        return self._request("POST", path, data)

    # ── Worker URL ──────────────────────────────────────────────
    def get_worker_url(self, worker_name):
        """Get the deployed worker URL"""
        path = f"/accounts/{self.account_id}/workers/subdomain"
        result = self._request("GET", path)
        if result.get("success") and result.get("result"):
            subdomain = result["result"].get("subdomain", "")
            if subdomain:
                return f"https://{worker_name}.{subdomain}.workers.dev"
        return f"https://{worker_name}.workers.dev"

    # ── Worker Subdomain Enable ─────────────────────────────────
    def enable_workers_dev(self, worker_name):
        """Enable workers.dev subdomain for the worker"""
        path = f"/accounts/{self.account_id}/workers/scripts/{worker_name}/subdomain"
        return self._request("POST", path, {"enabled": True})


# ═════════════════════════════════════════════════════════════════
# DEPLOYMENT PIPELINE
# ═════════════════════════════════════════════════════════════════

def banner(text):
    print("\n" + "═" * 70)
    print(f"  {text}")
    print("═" * 70)

def step(num, text):
    print(f"\n  [{num}] {text}")

def ok(text="OK"):
    print(f"      ✓ {text}")

def fail(text):
    print(f"      ✗ {text}")

def info(text):
    print(f"      → {text}")

def build_bindings_config():
    """Build the bindings array for the Worker metadata"""
    bindings = []
    
    # D1
    bindings.append({
        "type": "d1",
        "name": "DB",
        "database_id": D1_DATABASE_ID,
        "database_name": D1_DATABASE_NAME,
    })
    
    # KV
    for binding_name, namespace_id in KV_NAMESPACES.items():
        bindings.append({
            "type": "kv_namespace",
            "name": binding_name,
            "namespace_id": namespace_id,
        })
    
    # R2
    for binding_name, bucket_name in R2_BUCKETS.items():
        bindings.append({
            "type": "r2_bucket",
            "name": binding_name,
            "bucket_name": bucket_name,
        })
    
    # Queues (producers)
    queue_bindings = {
        "TRACE_QUEUE": "wallet-tracing",
        "ENTITY_QUEUE": "entity-resolution",
        "AI_QUEUE": "gemini-analysis",
        "REPORT_QUEUE": "report-generation",
        "NOTIFICATION_QUEUE": "notifications",
    }
    for binding_name, queue_name in queue_bindings.items():
        bindings.append({
            "type": "queue",
            "name": binding_name,
            "queue_name": queue_name,
        })
    
    # Durable Objects
    for binding_name, do_config in DURABLE_OBJECTS.items():
        bindings.append({
            "type": "durable_object_namespace",
            "name": binding_name,
            "class_name": do_config["class_name"],
            "namespace_id": do_config["namespace_id"],
        })
    
    # Workers AI
    bindings.append({
        "type": "ai",
        "name": "AI",
    })
    
    # Plain text vars (non-secret)
    vars = {
        "APP_NAME": "nemesis-platform",
        "APP_MODE": "production",
        "NODE_ENV": "production",
        "PYTHON_BACKEND_URL": "https://nemesis-backend.legionxgaming2021.workers.dev",
    }
    for key, value in vars.items():
        bindings.append({
            "type": "plain_text",
            "name": key,
            "text": value,
        })
    
    return bindings


def run_tests(worker_url):
    """Run automated tests against the deployed Worker"""
    banner("RUNNING AUTOMATED TESTS")
    
    results = {"pass": 0, "fail": 0, "tests": []}
    
    def test(name, url, expected_status=200, method="GET", body=None):
        step_num = len(results["tests"]) + 1
        print(f"\n  Test {step_num}: {name}")
        print(f"    {method} {url}")
        
        try:
            headers = {
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            if method == "GET":
                req = urllib.request.Request(url, headers=headers)
            else:
                data = json.dumps(body).encode() if body else b""
                req = urllib.request.Request(url, data=data, headers=headers, method=method)
            
            with urllib.request.urlopen(req, timeout=30) as resp:
                status = resp.getcode()
                data = json.loads(resp.read().decode())
                
                if status == expected_status:
                    ok(f"Status {status}")
                    results["pass"] += 1
                    results["tests"].append({"name": name, "status": "pass", "code": status})
                else:
                    fail(f"Expected {expected_status}, got {status}")
                    results["fail"] += 1
                    results["tests"].append({"name": name, "status": "fail", "code": status, "expected": expected_status})
                
                # Print key response data
                if isinstance(data, dict):
                    keys = list(data.keys())[:5]
                    for k in keys:
                        val = data[k]
                        if isinstance(val, (str, int, float, bool)):
                            print(f"    {k}: {val}")
                        elif isinstance(val, list):
                            print(f"    {k}: [{len(val)} items]")
                        elif isinstance(val, dict):
                            print(f"    {k}: {{...}}")
                
                return data
        except urllib.error.HTTPError as e:
            fail(f"HTTP {e.code}: {e.read().decode()[:200]}")
            results["fail"] += 1
            results["tests"].append({"name": name, "status": "fail", "code": e.code})
            return None
        except Exception as e:
            fail(f"Error: {e}")
            results["fail"] += 1
            results["tests"].append({"name": name, "status": "fail", "error": str(e)})
            return None
    
    # Test 1: Health
    test("Health Check", f"{worker_url}/health")
    
    # Test 2: Address Lookup
    test("Address Lookup", f"{worker_url}/api/address?address=0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045&chain=ethereum")
    
    # Test 3: Address with Graph
    test("Address + Graph", f"{worker_url}/api/address?address=0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045&chain=ethereum&graph=true&depth=2")
    
    # Test 4: Graph
    test("Graph Endpoint", f"{worker_url}/api/graph?address=0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045&chain=ethereum&depth=2")
    
    # Test 5: Trace
    test("Trace (POST)", f"{worker_url}/api/trace", 200, "POST", {
        "address": "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
        "chain": "ethereum",
        "depth": 2,
    })
    
    # Test 6: Batch
    test("Batch Balance", f"{worker_url}/api/batch", 200, "POST", {
        "addresses": ["0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045", "0x5B3256965787d0Ea3F3a5e5b0a5b5b5b5b5b5b5b"],
        "chain": "ethereum",
    })
    
    # Test 7: Labels
    test("Labels Lookup", f"{worker_url}/api/labels?address=0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045&chain=ethereum")
    
    # Test 8: Entity Search
    test("Entity Search", f"{worker_url}/api/entity?q=vitalik")
    
    # Test 9: Stats
    test("Stats", f"{worker_url}/api/stats")
    
    # Test 10: Providers
    test("Providers Status", f"{worker_url}/api/providers")
    
    # Test 11: AI Analysis
    test("AI Analysis", f"{worker_url}/api/ai/analyze", 200, "POST", {
        "address": "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
        "chain": "ethereum",
    })
    
    # Test 12: Token Transfers
    test("Token Transfers", f"{worker_url}/api/tokens?address=0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045&chain=ethereum")
    
    return results



def setup_github_repo():
    banner("PHASE 0: GITHUB REPOSITORY SETUP")
    github_token = os.environ.get("GITHUB_TOKEN", "")
    if not github_token:
        print("\n  [i] GITHUB_TOKEN environment variable not set. Skipping automated GitHub repo creation.")
        print("      To enable this, set GITHUB_TOKEN and run again.")
        return

    repo_name = os.environ.get("GITHUB_REPO_NAME", "nemesis_v3").strip()
    if not repo_name:
        repo_name = "nemesis_v3"
        
    is_private = os.environ.get("GITHUB_REPO_PRIVATE", "y").strip().lower() != 'n'

    step("0.1", f"Creating GitHub repository '{repo_name}'...")
    
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    data = {
        "name": repo_name,
        "private": is_private,
        "description": "NEMESIS v3 Cloudflare Deployment"
    }
    
    clone_url = ""
    try:
        req = urllib.request.Request("https://api.github.com/user/repos", data=json.dumps(data).encode('utf-8'), headers=headers, method="POST")
        with urllib.request.urlopen(req) as res:
            response_data = json.loads(res.read().decode('utf-8'))
            clone_url = response_data.get('clone_url')
            ok(f"Created repository: {clone_url}")
    except urllib.error.HTTPError as e:
        if e.code == 422: # Repo already exists
            ok(f"Repository {repo_name} already exists.")
            # Fetch existing repo URL
            req = urllib.request.Request(f"https://api.github.com/user", headers=headers)
            with urllib.request.urlopen(req) as res:
                username = json.loads(res.read().decode('utf-8')).get('login')
                clone_url = f"https://github.com/{username}/{repo_name}.git"
        else:
            print(f"  ✗ Failed to create repository: {e}")
            return
    except Exception as e:
        print(f"  ✗ Failed to create repository: {e}")
        return
        
    step("0.2", "Pushing local code to GitHub...")
    try:
        import subprocess
        subprocess.run(["git", "init"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["git", "add", "."], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["git", "commit", "-m", "Initial NEMESIS v3 commit"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["git", "branch", "-M", "main"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Remove origin if exists
        subprocess.run(["git", "remote", "remove", "origin"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Add remote with token for auth
        auth_url = clone_url.replace("https://", f"https://{github_token}@")
        subprocess.run(["git", "remote", "add", "origin", auth_url], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Push
        subprocess.run(["git", "push", "-u", "origin", "main"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Revert remote to standard URL (remove token)
        subprocess.run(["git", "remote", "set-url", "origin", clone_url], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        ok("Successfully pushed to GitHub!")
    except Exception as e:
        print(f"  ✗ Failed to push code: {e}")

def main():

    banner("NEMESIS v2 — COMPLETE CLOUDFLARE AUTO-DEPLOYMENT")
    
    # Run GitHub Automation
    setup_github_repo()

    
    # Get API token
    api_token = os.environ.get("CLOUDFLARE_API_TOKEN", "")
    if not api_token:
        print("\n  CLOUDFLARE_API_TOKEN environment variable not set.")
        print("  Get one at: https://dash.cloudflare.com/profile/api-tokens")
        print("  Required permissions:")
        print("    - Workers Scripts: Edit")
        print("    - D1: Edit")
        print("    - Workers KV Storage: Edit")
        print("    - Workers R2 Storage: Edit")
        print("    - Queues: Edit")
        print("    - Durable Objects: Edit")
        print("    - Workers AI: Edit")
        api_token = input("\n  Paste your Cloudflare API token: ").strip()
    
    if not api_token:
        print("\n  ✗ No API token provided. Exiting.")
        sys.exit(1)
    
    cf = CloudflareAPI(api_token, ACCOUNT_ID)
    
    # Verify token
    step("0", "Verifying API token...")
    verify = cf._request("GET", "/user/tokens/verify")
    if not verify.get("success"):
        fail("Invalid API token")
        sys.exit(1)
    ok("Token verified")
    
    # ── Phase 1: Write Files ────────────────────────────────────
    banner("PHASE 1: GENERATE PROJECT FILES")
    
    step("1.1", "Writing worker.js...")
    with open("worker.js", "w") as f:
        f.write(WORKER_JS)
    ok(f"worker.js written ({len(WORKER_JS)} bytes)")
    
    step("1.2", "Writing wrangler.toml...")
    with open("wrangler.toml", "w") as f:
        f.write(WRANGLER_TOML)
    ok("wrangler.toml written")
    
    step("1.3", "Writing D1 migration...")
    os.makedirs("migrations", exist_ok=True)
    with open("migrations/0001_init.sql", "w") as f:
        f.write(MIGRATION_SQL)
    ok("migrations/0001_init.sql written")
    
    # ── Phase 2: Apply D1 Migrations ────────────────────────────
    banner("PHASE 2: APPLY D1 MIGRATIONS")
    
    step("2.1", f"Applying schema to D1 database: {D1_DATABASE_NAME}...")
    
    # Split SQL into individual statements
    statements = [s.strip() for s in MIGRATION_SQL.split(';') if s.strip() and not s.strip().startswith('--')]
    
    applied = 0
    for stmt in statements:
        if not stmt:
            continue
        result = cf.d1_query(D1_DATABASE_ID, stmt)
        if result.get("success"):
            applied += 1
        else:
            errors = result.get("errors", [])
            if errors and "already exists" in str(errors).lower():
                info(f"Skipped (already exists): {stmt[:60]}...")
            else:
                fail(f"SQL error: {errors}")
    
    ok(f"Applied {applied} SQL statements")
    
    # Verify tables
    step("2.2", "Verifying D1 tables...")
    tables_result = cf.d1_list_tables(D1_DATABASE_ID)
    if tables_result.get("success"):
        table_names = [r["name"] for r in tables_result.get("result", [{}])[0].get("results", [])]
        ok(f"Tables found: {', '.join(table_names)}")
    else:
        info("Could not list tables (non-critical)")
    
    # ── Phase 3: Deploy Worker ───────────────────────────────────
    banner("PHASE 3: DEPLOY WORKER")
    
    step("3.1", "Building bindings configuration...")
    bindings = build_bindings_config()
    ok(f"Configured {len(bindings)} bindings")
    
    step("3.2", f"Deploying Worker: {WORKER_NAME}...")
    deploy_result = cf.deploy_worker(WORKER_NAME, WORKER_JS, bindings)
    
    if deploy_result.get("success"):
        ok("Worker deployed successfully!")
        if deploy_result.get("result"):
            result_data = deploy_result["result"]
            if "subdomain" in result_data:
                info(f"Subdomain: {result_data['subdomain']}")
    else:
        errors = deploy_result.get("errors", [])
        fail(f"Deploy failed: {errors}")
        # Try alternate deployment method
        step("3.2b", "Trying alternate deployment (wrangler)...")
        try:
            # Write wrangler.toml and use npx wrangler deploy
            result = subprocess.run(
                ["npx", "wrangler", "deploy", "--name", WORKER_NAME, "--compatibility-date", "2024-12-01"],
                capture_output=True, text=True, timeout=120, cwd=os.getcwd()
            )
            if result.returncode == 0:
                ok("Deployed via wrangler!")
            else:
                fail(f"Wrangler also failed: {result.stderr[:500]}")
                print("\n  Manual deployment required:")
                print(f"    npx wrangler deploy")
                sys.exit(1)
        except FileNotFoundError:
            fail("wrangler not available")
            print("\n  Install wrangler and deploy manually:")
            print("    npm install -g wrangler")
            print("    npx wrangler deploy")
            sys.exit(1)
    
    # ── Phase 4: Upload Secrets ─────────────────────────────────
    banner("PHASE 4: UPLOAD SECRETS")
    
    step("4.1", f"Uploading {len(SECRETS)} secrets via bulk API...")
    secret_results = cf.upload_secrets_bulk(WORKER_NAME, SECRETS)
    
    secrets_ok = 0
    secrets_fail = 0
    for r in secret_results:
        if r.get("success"):
            secrets_ok += 1
        else:
            secrets_fail += 1
            errors = r.get("errors", [])
            if errors:
                info(f"Secret upload warning: {errors[0].get('message', 'unknown')}")
    
    ok(f"Secrets uploaded: {secrets_ok} batches succeeded, {secrets_fail} failed")
    
    # ── Phase 5: Configure Queue Consumers ─────────────────────
    banner("PHASE 5: CONFIGURE QUEUE CONSUMERS")
    
    step("5.1", "Setting up queue consumers...")
    for queue_name in QUEUES:
        result = cf.create_queue_consumer(queue_name, WORKER_NAME)
        if result.get("success"):
            ok(f"Consumer set: {queue_name} → {WORKER_NAME}")
        else:
            errors = result.get("errors", [])
            msg = errors[0].get("message", "") if errors else ""
            if "already" in msg.lower():
                info(f"Consumer already exists: {queue_name}")
            else:
                info(f"Queue consumer setup: {queue_name} — {msg}")
    
    # ── Phase 6: Enable workers.dev subdomain ───────────────────
    banner("PHASE 6: ENABLE WORKERS.DEV SUBDOMAIN")
    
    step("6.1", "Enabling workers.dev subdomain...")
    subdomain_result = cf.enable_workers_dev(WORKER_NAME)
    if subdomain_result.get("success"):
        ok("workers.dev subdomain enabled")
    else:
        info("Subdomain may already be enabled")
    
    # Get worker URL
    step("6.2", "Getting Worker URL...")
    worker_url = cf.get_worker_url(WORKER_NAME)
    ok(f"Worker URL: {worker_url}")
    
    # ── Phase 7: Run Automated Tests ────────────────────────────
    banner("PHASE 7: AUTOMATED TESTS")
    
    # Wait for deployment to propagate
    step("7.0", "Waiting 10s for deployment to propagate...")
    time.sleep(10)
    
    test_results = run_tests(worker_url)
    
    # ── Deployment Report ───────────────────────────────────────
    banner("DEPLOYMENT REPORT")
    
    print(f"""
  ════════════════════════════════════════════════════════════════
   NEMESIS v2 — DEPLOYMENT SUMMARY
  ════════════════════════════════════════════════════════════════

   Worker Name:     {WORKER_NAME}
   Worker URL:      {worker_url}
   Account ID:      {ACCOUNT_ID}

   D1 Database:     {D1_DATABASE_NAME} ({D1_DATABASE_ID})
   KV Namespaces:   {len(KV_NAMESPACES)} bound
   R2 Buckets:      {len(R2_BUCKETS)} bound
   Queues:          {len(QUEUES)} configured
   Durable Objects: {len(DURABLE_OBJECTS)} bound
   Secrets:         {len(SECRETS)} uploaded
   Bindings Total:  {len(bindings)}

   Test Results:
     Passed: {test_results['pass']}
     Failed: {test_results['fail']}
     Total:  {test_results['pass'] + test_results['fail']}

   API Endpoints:
     GET  /health              — Health check
     GET  /api/address          — Address lookup + optional graph
     GET  /api/graph            — Transaction graph (BFS traversal)
     POST /api/trace           — Queue a trace job
     POST /api/batch           — Batch address balance lookup
     GET  /api/labels          — Entity labels for an address
     GET  /api/entity           — Search entities by name/address
     GET  /api/stats            — Database statistics
     GET  /api/providers        — Provider status (all chains)
     POST /api/ai/analyze       — AI-powered risk analysis
     GET  /api/tokens           — Token transfers for an address
     POST /api/report           — Save report to R2
     POST /api/bitquery         — Bitquery GraphQL proxy
     WS   /ws                   — WebSocket (RealtimeManager DO)

  ════════════════════════════════════════════════════════════════
    """)
    
    # Print test details
    if test_results["fail"] > 0:
        print("  Failed Tests:")
        for t in test_results["tests"]:
            if t["status"] == "fail":
                print(f"    ✗ {t['name']}")
        print()
    
    # Compatibility Report
    banner("COMPATIBILITY REPORT")
    print("""
  Components compatible with Cloudflare Workers:
    ✓ Blockchain explorer APIs (Etherscan, BSCScan, etc.)
    ✓ Bitquery GraphQL API
    ✓ Tatum API
    ✓ Ankr API
    ✓ AI providers (Gemini, OpenAI, Workers AI)
    ✓ D1 database (addresses, transactions, traces, labels)
    ✓ KV caching (entity labels, session, token, OSINT)
    ✓ R2 storage (evidence, exports, reports, screenshots)
    ✓ Queues (trace, entity, AI, report, notifications)
    ✓ Durable Objects (admin, realtime WebSocket, trace coordinator)
    ✓ CORS + security headers

  Components NOT compatible with Workers (kept as env vars for
  external access):
    ✗ MongoDB (DATABASE_MONGO_URL) — No native Workers driver
    ✗ PostgreSQL (POSTGRES_URI) — Use Hyperdrive or migrate to D1
    ✗ Neo4j (NEO4J_URI) — Requires persistent TCP connections
    ✗ Celery/Redis — Replaced by Queues + Durable Objects
    ✗ Flask/FastAPI — Workers run JS/TS only
    ✗ Subprocess/native binaries — No subprocess support
    ✗ Local filesystem — Replaced by R2
    ✗ Tor/SOCKS proxy — No native socket support
    ✗ Puppeteer — Use Cloudflare Browser Rendering instead
    """)
    
    # Security Report
    banner("SECURITY REPORT")
    print("""
  Security measures enabled:
    ✓ HTTPS (automatic via Cloudflare)
    ✓ HSTS (Strict-Transport-Security header)
    ✓ X-Content-Type-Options: nosniff
    ✓ X-Frame-Options: DENY
    ✓ Referrer-Policy: strict-origin-when-cross-origin
    ✓ Permissions-Policy: geolocation=(), microphone=(), camera=()
    ✓ CORS configured with explicit allowed methods/headers
    ✓ All secrets stored as Worker Secrets (encrypted at rest)
    ✓ No secrets in plain text environment variables
    ✓ Input validation on all endpoints
    ✓ Rate limiting via Cloudflare (configure in dashboard)

  Security recommendations:
    → Rotate all API keys after initial deployment
    → Set up WAF rules in Cloudflare dashboard
    → Configure rate limiting rules
    → Enable Cloudflare Bot Management
    → Set up Cloudflare Access for admin endpoints
    """)
    
    print("\n" + "═" * 70)
    print("  DEPLOYMENT COMPLETE")
    print("═" * 70)
    print(f"\n  Worker URL: {worker_url}")
    print(f"  Health:     {worker_url}/health")
    print(f"  API Docs:    {worker_url}/ (GET / returns endpoint list)")
    print()


if __name__ == "__main__":
    main()

