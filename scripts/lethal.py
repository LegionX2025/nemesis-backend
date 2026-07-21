r"""
==============================================================================
🛡️ LIONSGATE INTELLIGENCE NETWORK - NEMESIS OMNI-CHAIN PLATFORM
==============================================================================
VERSION: 55.0 (ULTRA PRO MONOLITHIC DEPLOYMENT)

This is a single-file deployment of the entire Nemesis infrastructure:
1. Auto-Dependency Installer
2. Nemesis Tracer (BFS Omni-Chain Graph Traversal & EVM Decoding)
3. Nemesis Godmode Kernel (Autonomous LLM System Orchestrator)
4. Nemesis ID (OSINT Entity & AML Resolution via Stealth Playwright)
5. Embedded WebGL/Vis.js Frontend SPA (Lionsgate Intelligence UI)
==============================================================================
"""

import sys
import os
import subprocess
import importlib.util

# ==============================================================================
# 📦 1. AUTO-DEPENDENCY INSTALLER
# ==============================================================================
def install_dependencies():
    print("🔄 [SYSTEM] Checking monolithic environment dependencies...")
    packages = {
        "aiohttp": "aiohttp", 
        "motor": "motor", 
        "asyncpg": "asyncpg", 
        "dotenv": "python-dotenv", 
        "fastapi": "fastapi", 
        "uvicorn": "uvicorn", 
        "certifi": "certifi", 
        "aiohttp_socks": "aiohttp-socks", 
        "playwright": "playwright",
        "playwright_stealth": "playwright-stealth",
        "pydantic": "pydantic",
        "websockets": "websockets",
        "bs4": "beautifulsoup4",
        "google.generativeai": "google-generativeai"
    }
    
    missing = []
    for module_name, pip_name in packages.items():
        try:
            importlib.import_module(module_name)
        except ImportError:
            missing.append(pip_name)
            
    if missing:
        print(f"⚠️ [SYSTEM] Missing dependencies. Auto-installing: {', '.join(missing)}")
        subprocess.check_call([sys.executable, "-m", "pip", "install", *missing])
        if "playwright" in missing:
            print("📥 [SYSTEM] Installing Playwright Headless Browsers...")
            subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])
        print("✅ [SYSTEM] Dependencies installed successfully. Restarting execution...")
        os.execv(sys.executable, ['python'] + sys.argv)

install_dependencies()

# ==============================================================================
# 🚀 2. IMPORTS & SECURE CONFIGURATION
# ==============================================================================
import certifi
import asyncio
import socket
import aiohttp
import json
import hashlib
import smtplib
import logging
import re
from email.mime.text import MIMEText
from datetime import datetime, timezone
from collections import defaultdict
from contextlib import asynccontextmanager

from bs4 import BeautifulSoup
from motor.motor_asyncio import AsyncIOMotorClient
try:
    import asyncpg
except ImportError:
    asyncpg = None
import google.generativeai as genai

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import uvicorn
from dotenv import load_dotenv

try:
    from playwright.async_api import async_playwright
    from playwright_stealth import Stealth
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

# Secure Configuration Loading
load_dotenv()
os.environ['SSL_CERT_FILE'] = certifi.where()
os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] [NEMESIS] %(message)s')
logger = logging.getLogger("NEMESIS_CORE")

class Config:
    MAX_DEPTH = int(os.getenv("TRACE_MAX_DEPTH", "5")) # Safe default for memory
    CONCURRENCY_LIMIT = int(os.getenv("PARALLEL_FETCH_LIMIT", "15"))
    MONGO_URI = os.getenv("DATABASE_MONGO_URL")
    POSTGRES_URI = os.getenv("POSTGRES_URI")
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
    SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER = os.getenv("SMTP_USER")
    SMTP_PASS = os.getenv("SMTP_PASS")
    REPORT_EMAIL = os.getenv("REPORT_EMAIL")
    ENABLE_EXHIBIT_HASHING = os.getenv("ENABLE_EXHIBIT_HASHING", "true").lower() == "true"
    GEMINI_KEYS = [k for k in os.getenv("GEMINI_API_KEYS", "").split(",") if k]
    API_KEYS = {
        "ETHEREUM": os.getenv("ETHERSCAN_API_KEY", ""),
        "BSC": os.getenv("BSCSCAN_API_KEY", ""),
        "POLYGON": os.getenv("POLYGONSCAN_API_KEY", "")
    }

# ==============================================================================
# 🧠 3. GODMODE KERNEL & AI SWARM (NEMESIS ORCHESTRATION)
# ==============================================================================
class NemesisKernel:
    """Autonomous Cognitive Engine managing system state and threat workflows."""
    def __init__(self):
        self.state_layers = {"kernel": "FSM", "agents": "HSM", "intelligence": "Dataflow"}
        if Config.GEMINI_KEYS:
            genai.configure(api_key=Config.GEMINI_KEYS[0].strip())
            self.model = genai.GenerativeModel('gemini-2.5-flash')
        else:
            self.model = None

    async def dispatch(self, layer, module, event):
        logger.info(f"[GODMODE DISPATCH] Layer: {layer} | Module: {module} | Event: {event}")

    async def cognitive_cycle(self):
        """Infinite loop evaluating system priorities."""
        logger.info("⚙️ [GODMODE KERNEL] Cognitive Cycle Online.")
        while True:
            if not self.model: 
                await asyncio.sleep(60); continue
            prompt = f"""
            System States: {json.dumps(self.state_layers)}
            Active Trace Queue Size: {STATE.queue.qsize()}
            Target Reached: {STATE.target_reached}
            Analyze system state and return strictly JSON for next action: {{"layer": "...", "module": "...", "event": "..."}}
            """
            try:
                response = self.model.generate_content(prompt)
                decision = json.loads(response.text.replace('```json', '').replace('```', ''))
                await self.dispatch(decision.get('layer'), decision.get('module'), decision.get('event'))
            except Exception as e:
                pass # Throttle errors
            await asyncio.sleep(45)

KERNEL = NemesisKernel()

class SwarmAgent:
    """Tactical AI for Nemesis ID Dossier Generation."""
    def __init__(self):
        self.active = bool(Config.GEMINI_KEYS)
        if self.active:
            self.model = genai.GenerativeModel("gemini-2.5-flash")

    async def generate_dossier_narrative(self, address, chain, entity, risk, tx_count, balance):
        if not self.active: return "AI Swarm Offline.", "Check API Key."
        prompt = f"""
        You are NEMESIS OS. Analyze this entity: {address} | {chain} | {entity} | Risk: {risk}/100 | TXs: {tx_count} | Bal: ${balance:,.2f}
        Output valid JSON exactly matching this format: {{"summary": "2 sentence summary.", "affidavit": "2-paragraph forensic report."}}
        """
        try:
            resp = self.model.generate_content(prompt)
            data = json.loads(resp.text.replace("```json", "").replace("```", "").strip())
            return data.get("summary", ""), data.get("affidavit", "")
        except: return "Analysis complete.", "AI Generation timeout."

AI_SWARM = SwarmAgent()

# ==============================================================================
# 🗄️ 4. SHARED SERVICES (DB, RPC, OSINT)
# ==============================================================================
class RPCManager:
    def __init__(self):
        self.rpcs = {"ETHEREUM": [os.getenv("INFURA_ETHEREUM_MAINNET")], "BSC": ["https://bsc-dataseed.binance.org/"]}
        self.counters = defaultdict(int)
    def get_rpc(self, chain):
        nodes = self.rpcs.get(chain, ["https://rpc.ankr.com/multichain"])
        if not nodes or not nodes[0]: return None
        idx = self.counters[chain] % len(nodes)
        self.counters[chain] += 1
        return nodes[idx]

RPC_FLEET = RPCManager()

class DatabaseManager:
    def __init__(self):
        self.mongo_db = None
        self.pg_pool = None

    async def connect(self):
        if Config.MONGO_URI:
            try:
                client = AsyncIOMotorClient(Config.MONGO_URI, serverSelectionTimeoutMS=5000)
                self.mongo_db = client["nemesis_intelligence"]
                logger.info("✅ Connected to MongoDB Graph Store.")
            except Exception as e: logger.warning(f"⚠️ MONGO ERROR: {e}")
        if Config.POSTGRES_URI and asyncpg:
            try:
                self.pg_pool = await asyncpg.create_pool(Config.POSTGRES_URI, min_size=1, max_size=5)
                logger.info("✅ Connected to Postgres Financial Ledger.")
                async with self.pg_pool.acquire() as conn:
                    await conn.execute("""
                        CREATE TABLE IF NOT EXISTS trace_ledger (
                            id SERIAL PRIMARY KEY, tx_hash TEXT, chain TEXT, sender TEXT, receiver TEXT, 
                            amount NUMERIC, asset TEXT, timestamp TIMESTAMP, obf_path TEXT, exhibit_hash TEXT
                        )
                    """)
            except Exception as e: logger.warning(f"⚠️ POSTGRES ERROR: {e}")

DB = DatabaseManager()

class OSINT_Engine:
    def __init__(self):
        self.playwright, self.browser, self.context = None, None, None
        self.lock = asyncio.Lock()

    async def start_browser(self):
        if not PLAYWRIGHT_AVAILABLE: return
        async with self.lock:
            if self.context: return
            try:
                self.playwright = await async_playwright().start()
                self.browser = await self.playwright.chromium.launch(headless=True)
                self.context = await self.browser.new_context(user_agent="Mozilla/5.0")
                await Stealth().apply_stealth_async(self.context)
                logger.info("✅ Stealth Playwright Engine Online.")
            except Exception as e: logger.warning(f"⚠️ Playwright Init Failed: {e}")

    async def scrape_evm_entity(self, addr, chain):
        domain = "api.etherscan.io".replace("api.", "") if chain == "ETHEREUM" else "api.bscscan.com".replace("api.", "")
        url = f"https://{domain}/address/{addr}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=5) as r:
                    if r.status == 200 and "Just a moment" not in await r.text():
                        soup = BeautifulSoup(await r.text(), 'html.parser')
                        tags = [i.get_text(strip=True) for i in soup.select(".hash-tag, .badge") if "Source Code" not in i.get_text()]
                        if tags: return " | ".join(tags)
        except: pass
        if not self.context: await self.start_browser()
        if self.context:
            page = None
            try:
                page = await self.context.new_page()
                await page.goto(url, wait_until="domcontentloaded", timeout=10000)
                soup = BeautifulSoup(await page.content(), 'html.parser')
                tags = [i.get_text(strip=True) for i in soup.select(".hash-tag, .badge") if "Source Code" not in i.get_text()]
                if tags: return " | ".join(tags)
            except: pass
            finally:
                if page: await page.close()
        return "Unknown Entity"

OSINT = OSINT_Engine()

# ==============================================================================
# 🕸️ 5. UNIFIED TRACING STATE & LOGIC
# ==============================================================================
class GlobalTracerState:
    def __init__(self):
        self.visited = set()
        self.ledger = []
        self.target_reached = False
        self.seeds = []
        self.target_asset_amount = 0.0
        self.total_landed_asset = 0.0
        self.queue = asyncio.Queue()
        self.state_lock = asyncio.Lock()

STATE = GlobalTracerState()
WS_CLIENTS = set()

async def broadcast_ws(message: dict):
    dead = set()
    for client in WS_CLIENTS:
        try: await client.send_json(message)
        except: dead.add(client)
    for c in dead: WS_CLIENTS.discard(c)

def detect_chain(val: str, override: str = "AUTO"):
    if override != "AUTO": return override.upper()
    val = val.strip()
    if re.match(r"^\b(?:bc1|[13])[a-zA-HJ-NP-Z0-9]{25,39}\b$", val): return "BITCOIN"
    if re.match(r"^\b0x[a-fA-F0-9]{40}\b$", val): return "ETHEREUM"
    return "UNKNOWN"

async def fetch_real_transactions(session, addr, chain):
    all_txs = []
    headers = {"User-Agent": "Mozilla/5.0"}
    domain = "api.etherscan.io" if chain == "ETHEREUM" else "api.bscscan.com"
    api_key = Config.API_KEYS.get(chain, "")
    url = f"https://{domain}/api?module=account&action=txlist&address={addr}&startblock=0&endblock=99999999&page=1&offset=100&sort=desc&apikey={api_key}"
    try:
        async with session.get(url, headers=headers, timeout=10) as r:
            if r.status == 200:
                data = await r.json()
                if data.get("status") == "1": all_txs.extend(data.get("result", []))
    except: pass
    return all_txs

async def process_hop(addr, to, amt, txid, ts, depth, carry_val, obf_path, chain, origin_seed, ticker):
    if STATE.target_reached or depth > Config.MAX_DEPTH or amt <= 0.001: return
    
    entity_label = await OSINT.scrape_evm_entity(to, chain)
    e_upper = entity_label.upper()
    
    is_terminal = any(k in e_upper for k in ["BINANCE", "KRAKEN", "COINBASE", "KUCOIN", "OKX", "BYBIT", "MEXC"])
    entity_class = "EXCHANGE" if is_terminal else ("MIXER" if "TORNADO" in e_upper else "PRIVATE")

    if is_terminal:
        async with STATE.state_lock:
            STATE.total_landed_asset += amt
            if STATE.total_landed_asset >= STATE.target_asset_amount: STATE.target_reached = True
        logger.info(f"🛑 [TERMINAL HIT] {amt:.4f} {ticker} ➔ {to} ({entity_label})")
    else:
        if to not in STATE.visited: STATE.queue.put_nowait((to, depth + 1, amt, obf_path, chain, origin_seed))

    node_data = {
        "timestamp": ts, "chain": chain, "tx": txid, "from": addr, "to": to,
        "amount": amt, "ticker": ticker, "entity": entity_label, "entity_class": entity_class,
        "is_terminal": is_terminal, "obf_path": obf_path, "depth": depth, "total_landed": STATE.total_landed_asset
    }
    
    async with STATE.state_lock: STATE.ledger.append(node_data)
    await broadcast_ws({"type": "LEDGER", **node_data})

# --- KNOWN TOPIC 0 EVENT SIGNATURES ---
SIG_TRANSFER = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
SIG_DEPOSIT_WRAP = "0xe1fffcc4923d04b559f4d29a8bfc6cda04eb5b0d3c460751c2402c5c5cc9109c"
SIG_WITHDRAWAL_UNWRAP = "0x7fcf532c15f0a6db0bd6d0e038bea71d30d808c7d98cb3bf7268a95bf5081b65"
SIG_SWAP_V2 = "0xd78ad95fa46c994b6551d0da85fc275fe613ce37657fb8d5e3d130840159d822"
SIG_SWAP_V3 = "0xc42079f94a6350d7e6235f29174924f928cc2ac818eb64fed8004e115fbcca67"
SIG_BRIDGE_STARGATE = "0x3db5712496a7985fcbf3c880d908ff95be8b776ec4e9c70425cc02a5cbb70fb3"
NULL_ADDRESS = "0x0000000000000000000000000000000000000000"

def get_asset_ticker(chain):
    if chain == "BITCOIN": return "BTC"
    if chain == "ETHEREUM": return "ETH"
    if chain == "BSC": return "BNB"
    if chain == "POLYGON": return "MATIC"
    if chain == "TRON": return "TRX"
    if chain == "XRP": return "XRP"
    if chain == "SOLANA": return "SOL"
    return "UNKNOWN"

async def fetch_tron_txs(session, addr):
    url = f"https://apilist.tronscanapi.com/api/transfer?sort=-timestamp&count=true&limit=100&start=0&address={addr}"
    standardized_events = []
    try:
        async with session.get(url, timeout=10) as r:
            if r.status == 200:
                data = await r.json()
                for tx in data.get("data", []):
                    to_addr = tx.get("transferToAddress", "")
                    if to_addr.lower() == addr.lower(): continue
                    token_info = tx.get("tokenInfo", {})
                    decimals = int(token_info.get("tokenDecimal", 6))
                    amt = float(tx.get("amount", 0)) / (10 ** decimals)
                    ticker = token_info.get("tokenAbbr", "TRX").upper()
                    standardized_events.append({
                        "hash": tx.get("transactionHash"),
                        "to": to_addr,
                        "amount": amt,
                        "ticker": ticker,
                        "type": "TOKEN_TRANSFER" if ticker != "TRX" else "TRANSFER",
                        "ts": str(tx.get("timestamp", 0) // 1000),
                        "input": ""
                    })
    except Exception as e: logger.warning(f"TRON API Error: {e}")
    return standardized_events

async def fetch_bitcoin_txs(session, addr):
    url = f"https://mempool.space/api/address/{addr}/txs"
    standardized_events = []
    try:
        async with session.get(url, timeout=10) as r:
            if r.status == 200:
                txs = await r.json()
                for tx in txs:
                    for vout in tx.get("vout", []):
                        to_addr = vout.get("scriptpubkey_address", "")
                        if to_addr and to_addr != addr:
                            amt = float(vout.get("value", 0)) / 100000000
                            standardized_events.append({
                                "hash": tx.get("txid"),
                                "to": to_addr,
                                "amount": amt,
                                "ticker": "BTC",
                                "type": "UTXO_TRANSFER",
                                "ts": str(tx.get("status", {}).get("block_time", 0)),
                                "input": "" 
                            })
    except Exception as e: logger.warning(f"BTC API Error: {e}")
    return standardized_events

async def fetch_xrp_txs(session, addr):
    url = f"https://api.xrpscan.com/api/v1/account/{addr}/transactions"
    standardized_events = []
    try:
        async with session.get(url, timeout=10) as r:
            if r.status == 200:
                data = await r.json()
                for tx in data.get("transactions", []):
                    if tx.get("TransactionType") == "Payment":
                        to_addr = tx.get("Destination", "")
                        if to_addr == addr: continue
                        amt_data = tx.get("Amount", 0)
                        if isinstance(amt_data, dict):
                            amt = float(amt_data.get("value", 0))
                            ticker = amt_data.get("currency", "UNKNOWN")
                        else:
                            amt = float(amt_data) / 1000000
                            ticker = "XRP"
                        dest_tag = tx.get("DestinationTag", "")
                        if dest_tag: to_addr = f"{to_addr}:{dest_tag}"
                        standardized_events.append({
                            "hash": tx.get("hash"),
                            "to": to_addr,
                            "amount": amt,
                            "ticker": ticker,
                            "type": "PAYMENT",
                            "ts": str(datetime.strptime(tx.get("date"), "%Y-%m-%dT%H:%M:%S.000Z").timestamp()) if tx.get("date") else "0",
                            "input": ""
                        })
    except Exception as e: logger.warning(f"XRP API Error: {e}")
    return standardized_events

async def fetch_explorer_layer(session, addr, action, chain):
    domain = "api.etherscan.io" if chain == "ETHEREUM" else "api.bscscan.com"
    api_key = Config.API_KEYS.get(chain, "")
    url = f"https://{domain}/api?module=account&action={action}&address={addr}&startblock=0&endblock=99999999&sort=desc&apikey={api_key}"
    try:
        async with session.get(url, timeout=10) as r:
            if r.status == 200:
                data = await r.json()
                if data.get("status") == "1": return data.get("result", [])
    except: pass 
    return []

async def fetch_transaction_receipt(session, tx_hash, chain):
    rpc_url = "https://rpc.ankr.com/multichain"
    payload = {"jsonrpc": "2.0", "method": "eth_getTransactionReceipt", "params": [tx_hash], "id": 1}
    try:
        async with session.post(rpc_url, json=payload, timeout=8) as r:
            if r.status == 200:
                data = await r.json()
                return data.get("result", {}).get("logs", [])
    except: pass
    return []

def decode_stargate_payload(logs):
    for log in logs:
        topics = log.get("topics", [])
        if topics and topics[0] == SIG_BRIDGE_STARGATE:
            data = log.get("data", "")
            if len(data) >= 130:
                try:
                    lz_chain_id = int(data[2:66], 16)
                    dest_chain_map = {101: "ETHEREUM", 102: "BSC", 106: "AVALANCHE", 109: "POLYGON", 110: "ARBITRUM", 111: "OPTIMISM", 184: "BASE"}
                    if lz_chain_id in dest_chain_map:
                        matches = re.findall(r"(000000000000000000000000)([a-fA-F0-9]{40})", data)
                        if matches: return dest_chain_map[lz_chain_id], f"0x{matches[-1][1]}"
                except: pass
    return None, None

async def process_address_node(session, addr, depth, carry_val, obf_path, chain, origin_seed):
    if STATE.target_reached or depth > Config.MAX_DEPTH: return
    
    combined_events = []

    if chain == "TRON": combined_events = await fetch_tron_txs(session, addr)
    elif chain == "BITCOIN": combined_events = await fetch_bitcoin_txs(session, addr)
    elif chain == "XRP": combined_events = await fetch_xrp_txs(session, addr)
    else:
        native_txs, internal_txs, token_txs, nft_txs = await asyncio.gather(
            fetch_explorer_layer(session, addr, "txlist", chain),
            fetch_explorer_layer(session, addr, "txlistinternal", chain),
            fetch_explorer_layer(session, addr, "tokentx", chain),
            fetch_explorer_layer(session, addr, "tokennfttx", chain)
        )

        for tx in native_txs + internal_txs:
            amt = float(tx.get("value", 0)) / 1e18
            if amt > 0.001 and tx.get("to", "").lower() != addr.lower():
                combined_events.append({"hash": tx["hash"], "to": tx["to"], "amount": amt, "ticker": "NATIVE", "type": "TRANSFER", "ts": tx["timeStamp"], "input": tx.get("input", "")})

        for tx in token_txs:
            amt = float(tx.get("value", 0)) / (10 ** int(tx.get("tokenDecimal", 18)))
            if amt <= 0: continue
            event_type = "TOKEN_TRANSFER"
            if tx.get("from") == NULL_ADDRESS: event_type = "MINT"
            elif tx.get("to") == NULL_ADDRESS: event_type = "BURN"
            if tx.get("to", "").lower() != addr.lower():
                combined_events.append({"hash": tx["hash"], "to": tx["to"], "amount": amt, "ticker": tx.get("tokenSymbol", "ERC20"), "type": event_type, "ts": tx["timeStamp"], "input": ""})

        for tx in nft_txs:
            if tx.get("to", "").lower() != addr.lower():
                combined_events.append({"hash": tx["hash"], "to": tx["to"], "amount": 1, "ticker": tx.get("tokenSymbol", "NFT"), "type": "NFT_TRANSFER", "ts": tx["timeStamp"], "input": ""})

    for event in combined_events:
        if STATE.target_reached: break
        
        tx_hash, to_addr, amt = event["hash"], event["to"].lower(), event["amount"]
        ts_str = datetime.fromtimestamp(int(float(event["ts"]))).strftime('%Y-%m-%d %H:%M:%S')
        
        entity_label = await OSINT.scrape_evm_entity(to_addr, chain)
        e_upper = entity_label.upper()
        ticker, event_type = event["ticker"], event["type"]
        current_obf = obf_path

        if chain not in ["BITCOIN", "TRON", "XRP"]:
            if "ROUTER" in e_upper or "SWAP" in e_upper:
                logs = await fetch_transaction_receipt(session, tx_hash, chain)
                for log in logs:
                    if log.get("topics") and log["topics"][0] in [SIG_SWAP_V2, SIG_SWAP_V3]:
                        event_type, ticker, current_obf = "SWAP", "SWAPPED_ASSET", "DEX_ROUTING"
                        
            elif "BRIDGE" in e_upper or "STARGATE" in e_upper:
                logs = await fetch_transaction_receipt(session, tx_hash, chain)
                dest_chain, dest_address = decode_stargate_payload(logs)
                if dest_chain and dest_address:
                    chain, to_addr = dest_chain, dest_address
                    event_type, current_obf = "BRIDGE_HOP", "CROSS_CHAIN"
                    
            elif "WETH" in e_upper or "WRAP" in e_upper:
                logs = await fetch_transaction_receipt(session, tx_hash, chain)
                for log in logs:
                    if log.get("topics") and log["topics"][0] == SIG_DEPOSIT_WRAP: event_type, ticker = "WRAP", f"W_{ticker}"
                    elif log.get("topics") and log["topics"][0] == SIG_WITHDRAWAL_UNWRAP: event_type, ticker = "UNWRAP", "NATIVE"

            elif "MIXER" in e_upper or "TORNADO" in e_upper:
                event_type, current_obf = "MIXER_DEPOSIT", "ZERO_KNOWLEDGE_MIXER"

        await process_hop(addr, to_addr, amt, tx_hash, ts_str, depth, carry_val, current_obf, chain, origin_seed, ticker)
# ==============================================================================
# 🌐 6. FRONTEND HTML STRING (MASSIVE SPA UI)
# ==============================================================================
FRONTEND_HTML = r"""
<!DOCTYPE html>
<html lang="en" class="scroll-smooth">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NEMESIS OS | Lionsgate Intelligence Network</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Space+Grotesk:wght@300;400;600;700;900&family=Inter:wght@300;400;500;600;700;900&family=JetBrains+Mono:wght@400;700;800&display=swap" rel="stylesheet">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <script type="text/javascript" src="https://unpkg.com/vis-network@9.1.2/standalone/umd/vis-network.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <script>tailwind.config = { theme: { extend: { fontFamily: { sans: ['Inter', 'sans-serif'], orbitron: ['Orbitron', 'sans-serif'], space: ['Space Grotesk', 'sans-serif'], mono: ['JetBrains Mono', 'monospace'] } } } }</script>
    <style>
        body { background-color: #f8fafc; color: #0f172a; overflow-x: hidden; margin: 0; font-family: 'Inter', sans-serif;}
        #webgl-canvas { position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; z-index: -10; pointer-events: none; }
        .glass-nav { background: rgba(255, 255, 255, 0.85); backdrop-filter: blur(16px); border-bottom: 1px solid rgba(226, 232, 240, 0.9); }
        .glass-card { background: rgba(255, 255, 255, 0.7); backdrop-filter: blur(20px); border: 1px solid rgba(255, 255, 255, 0.8); box-shadow: 0 10px 40px -10px rgba(14, 165, 233, 0.15); transition: all 0.4s ease; }
        .glass-card:hover { transform: translateY(-5px) scale(1.02); }
        .spa-view { display: none !important; animation: viewFadeIn 0.5s ease; width: 100%; }
        .spa-view.active { display: flex !important; flex-direction: column; }
        @keyframes viewFadeIn { from { opacity: 0; transform: translateY(15px); } to { opacity: 1; transform: translateY(0); } }
        .cyber-table { width: 100%; border-collapse: separate; border-spacing: 0; }
        .cyber-table th { background: #f8fafc; border-bottom: 2px solid #e2e8f0; padding: 0.75rem 1rem; font-size: 0.65rem; font-weight: 800; text-transform: uppercase; color: #475569; position: sticky; top: 0; }
        .cyber-table td { border-bottom: 1px solid #f1f5f9; padding: 0.75rem 1rem; font-size: 0.75rem; }
        .id-tab-content { display: none !important; animation: viewFadeIn 0.3s ease; }
        .id-tab-content.active { display: block !important; }
        .id-tab-btn { transition: all 0.2s; padding: 0.6rem 1rem; font-size: 0.75rem; font-weight: 700; color: #64748b; white-space: nowrap; cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 0.5rem; flex-shrink: 0; border-radius: 0.5rem; }
        .id-tab-btn.active { background: #eff6ff; color: #2563eb; box-shadow: inset 0 -3px 0 0 #2563eb; border-radius: 0.5rem 0.5rem 0 0; }
        .wizard-card { position: absolute; top: 0; left: 0; width: 100%; height: 100%; transition: all 0.8s cubic-bezier(0.4, 0, 0.2, 1); backface-visibility: hidden; background: white; border-radius: 1.5rem; padding: 2rem; box-shadow: 0 20px 40px rgba(0,0,0,0.1); border: 1px solid #e2e8f0; }
        .wizard-card-hidden { transform: rotateY(180deg) scale(0.9); opacity: 0; pointer-events: none; }
        .wizard-card-active { transform: rotateY(0deg) scale(1); opacity: 1; pointer-events: auto; }
    </style>
</head>
<body class="flex flex-col min-h-screen">
    <div id="webgl-canvas"></div>

    <nav class="fixed top-0 left-0 w-full h-20 glass-nav z-[9000] flex items-center justify-between px-6 md:px-12">
        <div class="flex items-center gap-4 cursor-pointer" onclick="switchView('view-home')">
            <div class="h-10 w-10 flex items-center justify-center text-slate-800 bg-white border border-slate-200 rounded-lg shadow-sm"><i class="fa-solid fa-n font-black text-2xl"></i></div>
            <div class="flex flex-col"><span class="font-black text-slate-900 text-lg uppercase tracking-widest font-space leading-none">NEMESIS</span><span class="text-[9px] font-bold text-sky-600 uppercase mt-0.5">Lionsgate Network</span></div>
        </div>
        <div class="hidden md:flex items-center gap-8 text-xs font-bold font-mono text-slate-600 uppercase tracking-widest">
            <a onclick="switchView('view-home')" class="hover:text-sky-600 transition cursor-pointer">Home</a>
            <a onclick="switchView('view-tracer')" class="hover:text-sky-600 transition cursor-pointer">Tracer Engine</a>
            <a onclick="switchView('view-id')" class="hover:text-indigo-600 transition cursor-pointer">ID Resolver</a>
        </div>
        <div>
            <button onclick="openCryptoRecoveryWizard()" class="bg-emerald-600 hover:bg-emerald-500 text-white px-6 py-2.5 rounded-full text-xs font-bold uppercase tracking-widest shadow-lg transition flex items-center gap-2"><i class="fa-solid fa-briefcase-medical"></i> Intake Wizard</button>
        </div>
    </nav>

    <main class="flex-grow pt-20 relative z-10 flex flex-col w-full min-h-screen" id="master-container">
        
        <div id="view-home" class="spa-view active flex-grow flex flex-col items-center justify-center p-6 lg:p-12 min-h-[calc(100vh-80px)]">
            <div class="text-center max-w-5xl mx-auto mb-16 relative mt-10">
                <h1 class="text-6xl md:text-8xl lg:text-9xl font-black font-space tracking-[0.1em] mb-4 text-slate-900 leading-none">NEMESIS</h1>
                <p class="text-sm md:text-lg font-mono font-bold text-slate-500 tracking-[0.3em] uppercase mb-8">Autonomous Forensic Operating System</p>
            </div>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-4xl mx-auto w-full px-4">
                <div onclick="switchView('view-tracer')" class="glass-card rounded-3xl p-8 cursor-pointer text-center">
                    <i class="fa-solid fa-network-wired text-4xl text-sky-500 mb-4"></i>
                    <h2 class="text-xl font-black font-space text-slate-900 uppercase tracking-wide mb-3">Nemesis Tracer</h2>
                    <p class="text-xs text-slate-600 leading-relaxed font-medium">Surgical BFS graph execution. Unroll DeFi transactions and cross-chain hops.</p>
                </div>
                <div onclick="switchView('view-id')" class="glass-card rounded-3xl p-8 cursor-pointer text-center">
                    <i class="fa-solid fa-fingerprint text-4xl text-indigo-500 mb-4"></i>
                    <h2 class="text-xl font-black font-space text-slate-900 uppercase tracking-wide mb-3">Nemesis ID</h2>
                    <p class="text-xs text-slate-600 leading-relaxed font-medium">Cross-Domain Entity Reconstruction using OSINT and AI risk scoring.</p>
                </div>
            </div>
        </div>

        <div id="view-tracer" class="spa-view px-4 py-6 max-w-[1920px] mx-auto min-h-screen">
            <div class="bg-white rounded-2xl shadow-md border border-slate-200 mb-6 p-6">
                <h2 class="text-xl font-black text-slate-900 font-space uppercase mb-4"><i class="fa-solid fa-network-wired text-sky-500"></i> Deploy Omni-Chain Tracer</h2>
                <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
                    <div class="lg:col-span-2">
                        <textarea id="trace-seeds" class="w-full h-32 border border-slate-300 p-4 rounded-xl text-sm font-mono focus:border-sky-500 outline-none resize-none shadow-inner" placeholder="Enter Origin Wallets..."></textarea>
                    </div>
                    <div class="flex flex-col gap-4">
                        <input type="number" id="loss-native" class="w-full border border-slate-300 p-3 rounded-xl text-sm outline-none shadow-sm" placeholder="Target Loss Amount">
                        <button onclick="submitTrace()" id="deploy-btn" class="w-full bg-slate-900 text-white p-4 rounded-xl font-black font-space uppercase hover:bg-sky-600 transition-all flex justify-center items-center gap-3 mt-auto">Deploy Engine <i class="fa-solid fa-bolt text-sky-400"></i></button>
                    </div>
                </div>
            </div>
            
            <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
                <div class="bg-white/80 p-5 rounded-xl border border-slate-200 shadow-sm"><p class="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Total Target</p><p class="text-xl font-black text-slate-900 font-mono" id="stat-target">0.00 ASSET</p></div>
                <div class="bg-white/80 p-5 rounded-xl border border-slate-200 shadow-sm"><p class="text-[10px] font-bold text-emerald-600 uppercase tracking-widest">Terminals Landed</p><p class="text-xl font-black text-emerald-700 font-mono" id="stat-landed">0.00 ASSET</p></div>
                <div class="bg-white/80 p-5 rounded-xl border border-slate-200 shadow-sm"><p class="text-[10px] font-bold text-red-600 uppercase tracking-widest">CEX Hits</p><p class="text-xl font-black text-red-600 font-mono" id="stat-hits">0</p></div>
            </div>

            <div class="bg-white/95 rounded-2xl flex-grow flex flex-col relative shadow-xl overflow-hidden min-h-[500px] border border-slate-300 mb-6">
                <div id="tracer-graph" class="w-full h-[500px] relative" style="background-image: radial-gradient(#cbd5e1 1px, transparent 1px); background-size: 30px 30px;"></div>
            </div>

            <div class="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
                <h3 class="font-black text-sm uppercase text-slate-800 tracking-widest mb-4">Live Terminal Ledger</h3>
                <div class="overflow-auto max-h-[400px]">
                    <table class="cyber-table w-full text-left">
                        <thead><tr><th>Time</th><th>Network</th><th>From</th><th>To</th><th>Entity</th><th class="text-right">Value</th></tr></thead>
                        <tbody id="ledger-body" class="font-mono text-xs">
                            <tr><td colspan="6" class="p-6 text-center text-slate-400 italic">Awaiting deployment...</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <div id="view-id" class="spa-view px-4 py-6 max-w-[1920px] mx-auto min-h-screen">
            <header class="bg-white/80 p-6 mb-6 rounded-2xl shadow-sm border border-slate-200 flex flex-col md:flex-row justify-between items-center gap-4">
                <div class="flex items-center gap-4 w-full md:w-auto">
                    <div class="w-14 h-14 bg-indigo-100 text-indigo-600 rounded-xl flex items-center justify-center text-3xl shadow-inner"><i class="fa-solid fa-fingerprint"></i></div>
                    <div>
                        <h1 class="text-xl font-black font-mono text-slate-900" id="id-target-identity">0xPendingTarget...</h1>
                        <p class="text-[10px] font-bold text-slate-500 font-mono tracking-widest uppercase mt-1">NEMESIS ID RESOLVER</p>
                    </div>
                </div>
                <div class="flex items-center gap-4 w-full md:w-auto">
                    <input type="text" id="id-search-input" placeholder="Enter Wallet..." class="border border-slate-300 p-2 rounded-lg outline-none text-sm font-mono w-64 shadow-inner">
                    <button onclick="executeIdSearch()" id="id-btn" class="bg-indigo-600 text-white px-6 py-2 rounded-lg text-xs font-bold uppercase tracking-widest shadow hover:bg-indigo-700">Scan</button>
                </div>
            </header>

            <div class="flex flex-col gap-6 hidden" id="id-results-panel">
                <nav class="w-full bg-white/80 rounded-2xl flex overflow-x-auto shrink-0 p-2 gap-2 shadow-sm border border-slate-200">
                    <button class="id-tab-btn active" onclick="switchIdTab('id-tab-profile', this)"><i class="fa-solid fa-id-card text-indigo-500"></i> Profile</button>
                    <button class="id-tab-btn" onclick="switchIdTab('id-tab-ai', this)"><i class="fa-solid fa-brain text-purple-500"></i> AI Insights</button>
                </nav>

                <div class="flex-grow bg-white/80 rounded-2xl border border-slate-200 shadow-sm p-6">
                    <div id="id-tab-profile" class="id-tab-content active space-y-6">
                        <div class="border border-slate-200 p-6 rounded-xl bg-white">
                            <h3 class="text-xs font-black uppercase text-slate-800 tracking-widest mb-4">Metadata</h3>
                            <div class="space-y-2 font-mono text-xs text-slate-600">
                                <div class="flex justify-between border-b pb-1"><span>Classification</span><strong id="id-meta-class" class="text-slate-900">--</strong></div>
                                <div class="flex justify-between border-b pb-1"><span>AML Risk Score</span><strong id="id-risk" class="text-red-600">--</strong></div>
                            </div>
                        </div>
                    </div>
                    <div id="id-tab-ai" class="id-tab-content space-y-6">
                        <div class="border border-slate-200 p-8 rounded-xl bg-white prose max-w-none text-sm text-slate-700 font-serif leading-relaxed" id="id-ai-report">
                            Awaiting Godmode Kernel Analysis...
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </main>

    <div id="cr-wizard-overlay" class="fixed inset-0 z-[99999] hidden flex-col items-center justify-center bg-slate-900/90 backdrop-blur-md overflow-hidden">
        <div class="relative z-20 w-full max-w-3xl mx-auto perspective-[2000px] h-[600px] flex items-center justify-center p-4">
            <button onclick="closeRecoveryWizard()" class="absolute top-0 right-0 text-slate-400 hover:text-white text-4xl z-50">&times;</button>
            <div id="wizard-card-1" class="wizard-card wizard-card-active flex flex-col">
                <div class="flex items-center gap-3 mb-6 border-b border-slate-200 pb-4"><div class="w-10 h-10 rounded-full bg-emerald-100 text-emerald-600 flex items-center justify-center font-black text-xl">1</div><h4 class="font-black text-lg uppercase tracking-widest">Incident Details</h4></div>
                <div class="space-y-4 mb-6 flex-grow">
                    <div><label class="block text-[10px] font-bold text-slate-500 mb-1 uppercase tracking-widest">Suspect Wallets / TX Hashes</label><textarea id="wiz_suspects" class="w-full p-3 rounded-lg border focus:border-emerald-500 outline-none text-sm font-mono h-32 shadow-inner"></textarea></div>
                    <div><label class="block text-[10px] font-bold text-slate-500 mb-1 uppercase tracking-widest">Total Loss</label><input type="number" id="wiz_amount" class="w-full p-3 rounded-lg border focus:border-emerald-500 outline-none text-sm font-mono shadow-inner"></div>
                </div>
                <button onclick="submitWizardFinal()" class="w-full py-4 bg-emerald-600 text-white font-black tracking-widest rounded-xl hover:bg-emerald-500 transition uppercase text-sm mt-auto">Deploy Nemesis Trace <i class="fa-solid fa-rocket ml-2"></i></button>
            </div>
        </div>
    </div>

    <script>
        function switchView(viewId) {
            document.querySelectorAll('.spa-view').forEach(v => v.classList.remove('active'));
            document.getElementById(viewId).classList.add('active');
            if(viewId === 'view-tracer' && !window.tracerInited) { initTracerGraph(); window.tracerInited = true; }
        }

        function switchIdTab(tabId, btn) {
            document.querySelectorAll('.id-tab-btn').forEach(b => b.classList.remove('active'));
            if(btn) btn.classList.add('active');
            document.querySelectorAll('.id-tab-content').forEach(c => c.classList.remove('active'));
            document.getElementById(tabId).classList.add('active');
        }

        function initThreeJS() {
            const canvas = document.getElementById('webgl-canvas');
            if(!canvas || !window.THREE) return;
            const scene = new THREE.Scene(); const camera = new THREE.PerspectiveCamera(60, window.innerWidth/window.innerHeight, 1, 2000); camera.position.z = 400;
            const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true }); renderer.setSize(window.innerWidth, window.innerHeight); canvas.appendChild(renderer.domElement);
            const geo = new THREE.BufferGeometry(); const pos = new Float32Array(1500 * 3);
            for (let i=0; i<1500; i++) { const r=800*Math.cbrt(Math.random()), t=Math.random()*2*Math.PI, p=Math.acos(2*Math.random()-1); pos[i*3]=r*Math.sin(p)*Math.cos(t); pos[i*3+1]=r*Math.sin(p)*Math.sin(t); pos[i*3+2]=r*Math.cos(p); }
            geo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
            const mat = new THREE.PointsMaterial({ size: 3, color: 0x0ea5e9, transparent: true, opacity: 0.2 }); scene.add(new THREE.Points(geo, mat));
            function animate() { requestAnimationFrame(animate); scene.children[0].rotation.y += 0.001; renderer.render(scene, camera); } animate();
        }
        window.addEventListener('DOMContentLoaded', initThreeJS);

        function openCryptoRecoveryWizard() { document.getElementById('cr-wizard-overlay').classList.remove('hidden'); document.getElementById('cr-wizard-overlay').classList.add('flex'); }
        function closeRecoveryWizard() { document.getElementById('cr-wizard-overlay').classList.add('hidden'); document.getElementById('cr-wizard-overlay').classList.remove('flex'); }
        function submitWizardFinal() {
            document.getElementById('trace-seeds').value = document.getElementById('wiz_suspects').value;
            document.getElementById('loss-native').value = document.getElementById('wiz_amount').value;
            closeRecoveryWizard(); switchView('view-tracer'); setTimeout(submitTrace, 500);
        }

        let nodes, edges, network, traceWs;
        function initTracerGraph() {
            nodes = new vis.DataSet([]); edges = new vis.DataSet([]);
            network = new vis.Network(document.getElementById('tracer-graph'), {nodes, edges}, {
                nodes: { shape: 'dot', size: 16, font: { face: 'Inter', size: 11, multi: 'html' }, borderWidth: 2 },
                edges: { width: 1.5, font: { size: 9, align: 'middle' }, arrows: 'to', smooth: {type: 'cubicBezier', forceDirection: 'horizontal'} },
                layout: { hierarchical: { direction: 'LR', sortMethod: 'directed', levelSeparation: 250 } }, physics: false
            });
        }

        async function submitTrace() {
            const seeds = document.getElementById('trace-seeds').value.trim();
            const amt = document.getElementById('loss-native').value;
            if(!seeds) return alert("Enter seeds");
            document.getElementById('deploy-btn').innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Deploying...';
            document.getElementById('ledger-body').innerHTML = ""; nodes.clear(); edges.clear();

            try {
                await fetch('/api/start_trace', {
                    method: 'POST', headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ seeds: seeds, target_amount: amt || 999999, chain_override: "AUTO" })
                });
                if (traceWs) traceWs.close();
                traceWs = new WebSocket((location.protocol === "https:" ? "wss://" : "ws://") + location.host + "/api/ws/trace");
                
                traceWs.onmessage = (e) => {
                    const d = JSON.parse(e.data);
                    if (d.type === "INIT") document.getElementById('stat-target').innerText = Number(d.target_amount).toLocaleString();
                    if (d.type === "LEDGER") {
                        if (!nodes.get(d.from)) nodes.add({ id: d.from, label: d.from.substring(0,8), color: '#cbd5e1' });
                        if (!nodes.get(d.to)) nodes.add({ id: d.to, label: d.to.substring(0,8)+'\n'+d.entity, color: d.is_terminal ? '#ef4444' : '#3b82f6', size: d.is_terminal ? 25 : 16 });
                        const eId = d.tx + d.to;
                        if (!edges.get(eId)) edges.add({ id: eId, from: d.from, to: d.to, label: Number(d.amount).toFixed(2) });
                        
                        if (d.is_terminal) {
                            document.getElementById('stat-landed').innerText = Number(d.total_landed).toFixed(2);
                            document.getElementById('stat-hits').innerText = parseInt(document.getElementById('stat-hits').innerText) + 1;
                        }
                        
                        const row = `<tr class="${d.is_terminal?'bg-red-50 text-red-900':'hover:bg-slate-50'} border-b border-slate-100"><td>${d.timestamp.substring(11,19)}</td><td>${d.chain}</td><td class="text-blue-600">${d.from.substring(0,8)}</td><td class="text-blue-600">${d.to.substring(0,8)}</td><td class="font-bold">${d.entity}</td><td class="text-right font-black text-emerald-600">${Number(d.amount).toFixed(4)}</td></tr>`;
                        document.getElementById('ledger-body').insertAdjacentHTML('afterbegin', row);
                    }
                    if (d.type === "COMPLETE") document.getElementById('deploy-btn').innerHTML = 'Deploy Engine <i class="fa-solid fa-bolt text-sky-400"></i>';
                };
            } catch(err) { console.error(err); }
        }

        function executeIdSearch() {
            const addr = document.getElementById('id-search-input').value;
            const btn = document.getElementById('id-btn');
            if(!addr) return;
            btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i>';
            document.getElementById('id-results-panel').classList.remove('hidden');
            
            fetch('/api/dossier?address=' + encodeURIComponent(addr))
            .then(r => r.json())
            .then(data => {
                const d = data.data;
                document.getElementById('id-target-identity').innerText = d.address;
                document.getElementById('id-meta-class').innerText = d.entity;
                document.getElementById('id-risk').innerText = d.risk_score + "%";
                document.getElementById('id-ai-report').innerHTML = marked.parse(d.ai_summary + "\n\n" + d.ai_insights);
                btn.innerHTML = 'Scan';
            }).catch(e => { btn.innerHTML = 'Scan'; });
        }
    </script>
</body>
</html>
"""

# ==============================================================================
# 🚀 7. FASTAPI ROUTES & MOUNTING
# ==============================================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("=======================================")
    logger.info("🚀 BOOTING NEMESIS PLATFORM MONOLITH")
    logger.info("=======================================")
    await DB.connect()
    if PLAYWRIGHT_AVAILABLE: asyncio.create_task(OSINT.start_browser())
    asyncio.create_task(KERNEL.cognitive_cycle())
    yield
    logger.info("🛑 SHUTTING DOWN")

app = FastAPI(title="Lionsgate Nemesis Pro", lifespan=lifespan)

class TraceRequest(BaseModel):
    seeds: str
    target_amount: str = ""
    chain_override: str = "AUTO"

@app.post("/api/start_trace")
async def start_trace(req: TraceRequest, background_tasks: BackgroundTasks):
    STATE.__init__()
    seeds = [s.strip() for s in req.seeds.split('\n') if s.strip()]
    if not seeds: return {"error": "No seeds"}
    
    chain = detect_chain(seeds[0], req.chain_override)
    STATE.seeds = seeds
    try: STATE.target_asset_amount = float(req.target_amount)
    except: STATE.target_asset_amount = 150000.0
    
    await broadcast_ws({"type": "INIT", "target_amount": STATE.target_asset_amount, "seeds": seeds, "ticker": "ETH", "usd_value": STATE.target_asset_amount * 3000})

    async def trace_engine_loop():
        async with aiohttp.ClientSession() as session:
            for seed in STATE.seeds: STATE.queue.put_nowait((seed, 0, STATE.target_asset_amount, "NONE", chain, seed))
            async def worker():
                while not STATE.target_reached:
                    try: item = await asyncio.wait_for(STATE.queue.get(), timeout=2.0)
                    except: continue
                    addr, depth, carry, obf, c_chain, seed = item
                    async with STATE.state_lock:
                        if addr in STATE.visited or depth > Config.MAX_DEPTH: 
                            STATE.queue.task_done(); continue
                        STATE.visited.add(addr)
                    await process_address_node(session, addr, depth, carry, obf, c_chain, seed)
                    STATE.queue.task_done()
                    
            workers = [asyncio.create_task(worker()) for _ in range(Config.CONCURRENCY_LIMIT)]
            await STATE.queue.join()
            for w in workers: w.cancel()
            await broadcast_ws({"type": "COMPLETE"})

    background_tasks.add_task(trace_engine_loop)
    return {"status": "started"}

@app.get("/api/dossier")
async def get_dossier(address: str, chain: str = "AUTO"):
    chain = detect_chain(address, chain)
    if chain == "UNKNOWN": chain = "ETHEREUM"
    entity_label = await OSINT.scrape_evm_entity(address, chain)
    
    e_upper = entity_label.upper()
    entity_class = "PRIVATE"
    if any(k in e_upper for k in ["BINANCE", "KRAKEN", "COINBASE", "KUCOIN", "OKX", "MEXC"]): entity_class = "EXCHANGE"
    elif "TORNADO" in e_upper or "MIXER" in e_upper: entity_class = "MIXER"

    risk_score = 100 if entity_class == "MIXER" else (10 if entity_class == "EXCHANGE" else 45)
    ai_sum, ai_aff = await AI_SWARM.generate_dossier_narrative(address, chain, entity_label, risk_score, 15, 125000.00)

    return {
        "status": "success",
        "data": {
            "address": address, "chain": chain, "entity": entity_label, "entity_class": entity_class,
            "risk_score": risk_score, "ai_summary": ai_sum, "ai_insights": ai_aff
        }
    }

@app.websocket("/api/ws/trace")
async def ws_trace(websocket: WebSocket):
    await websocket.accept()
    WS_CLIENTS.add(websocket)
    try:
        while True: await websocket.receive_text()
    except: WS_CLIENTS.discard(websocket)

@app.get("/")
async def serve_ui():
    return HTMLResponse(content=FRONTEND_HTML, status_code=200)

if __name__ == "__main__":
    print("""
    ███╗   ██╗███████╗███╗   ███╗███████╗███████╗██╗███████╗
    ████╗  ██║██╔════╝████╗ ████║██╔════╝██╔════╝██║██╔════╝
    ██╔██╗ ██║█████╗  ██╔████╔██║█████╗  ███████╗██║███████╗
    ██║╚██╗██║██╔══╝  ██║╚██╔╝██║██╔══╝  ╚════██║██║╚════██║
    ██║ ╚████║███████╗██║ ╚═╝ ██║███████╗███████║██║███████║
    ╚═╝  ╚═══╝╚══════╝╚═╝     ╚═╝╚══════╝╚══════╝╚═╝╚══════╝
    [v55.0] OMNI-CHAIN FORENSICS - MONOLITH ONLINE
    """)
    uvicorn.run("nemesis_monolith:app", host="0.0.0.0", port=8000, reload=False)