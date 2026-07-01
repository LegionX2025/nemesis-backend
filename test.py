import sys
import os
import certifi
import socket
import asyncio
import csv
import json
import traceback
import threading
import aiohttp
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from collections import defaultdict
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import uvicorn
from motor.motor_asyncio import AsyncIOMotorClient

# Fix SSL and Windows Asyncio issues
os.environ['SSL_CERT_FILE'] = certifi.where()
os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()

if os.name == 'nt':
    _orig_getpeername = socket.socket.getpeername
    def _safe_getpeername(self):
        try: return _orig_getpeername(self)
        except OSError as e:
            if getattr(e, 'winerror', None) == 10014: return ('0.0.0.0', 0)
            raise
    socket.socket.getpeername = _safe_getpeername

# ==============================================================================
# 🛡️ LIONSGATE INTELLIGENCE NETWORK - SECURE ENVIRONMENT CONFIGURATION
# ==============================================================================

MAX_DEPTH = 1000  
CONCURRENCY_LIMIT = 20 
CSV_FILE = "LGN_OmniChain_Trace.csv"
JSON_FILE = "LGN_OmniChain_Trace.json"

FILE_WRITE_LOCK = threading.Lock()
IO_POOL = ThreadPoolExecutor(max_workers=20)

CONFIG = {
    "MONGO_URI": os.getenv("DATABASE_MONGO_URL", "mongodb+srv://MKpBkrUw:Z63zGHQaiYG6rhrb@us-east-1.ufsuw.mongodb.net/blockchain"),
    "ETHERSCAN_API_KEY": os.getenv("ETHERSCAN_API_KEY", "AYQRQWFDJRK8WAX2ICJ8U4JUSYXZT5J7II"),
    "BSCSCAN_API_KEY": os.getenv("BSCSCAN_API_KEY", "5HVRJGR3D1FGAG1VQXEIPN5HE7WU399CDY"),
    "POLYGONSCAN_API_KEY": os.getenv("POLYGONSCAN_API_KEY", "5HVRJGR3D1FGAG1VQXEIPN5HE7WU399CDY"),
}

EVM_DOMAINS = {
    "ETHEREUM": "api.etherscan.io", "BSC": "api.bscscan.com",
    "POLYGON": "api.polygonscan.com", "BASE": "api.basescan.org"
}

USD_RATES = {"ETHEREUM": 3100.00, "BITCOIN": 65000.00}

# Forensics Known Entity Database (Used strictly for OSINT mapping, NOT mocking)
KNOWN_ENTITIES = {
    "bc1qm34lsc65zpw79lxes69zkqmk6ee3ewf0j77s3h": "Binance Deposit",
    "bc1qdl52luxgq8e623gamzgk9faaxm0sjtdwej3dmg": "OKX Exchange",
    "0x28c6c06298d514db089934071355e5743bf21d60": "Binance 14 (Cold)",
    "0xd90e2f925da726b50c4ed8d0fb90ad053324f31b": "Tornado Cash Router",
}

TRANSFER_SIGS = {"0xa9059cbb", "0x23b872dd", "0x095ea7b3"}
DEX_SWAP_SIGS = {"0x38ed1739", "0x18cbafe5", "0x7ff36ab5", "0x5c11d795", "0x8803dbee"}
BRIDGE_HOP_SIGS = {"0x3d12a85a", "0x4faa8a26", "0xa3bc6e0e", "0x8b9e4f93"}
MIXER_SIGS = {"0xb1a1a882", "0x21a0adb6", "0x1249c58b", "0xa50d75a8"}
CEX_DEPOSIT_SIGS = {"0xe2bbb158", "0x6352211e", "0x3bc1f1ed", "0xb4b2a476"}

mongo_client = None
mongo_db = None

async def init_mongodb():
    global mongo_client, mongo_db
    try:
        mongo_client = AsyncIOMotorClient(CONFIG["MONGO_URI"], serverSelectionTimeoutMS=3000, tlsCAFile=certifi.where())
        mongo_db = mongo_client["blockchain"]
        await mongo_client.admin.command('ping')
        print("      ✅ [MONGO DB] Connected successfully.", flush=True)
    except Exception as e:
        mongo_db = None

def detect_chain(val: str, override: str = "AUTO") -> str:
    if override and override != "AUTO": return override.upper()
    val = val.strip()
    if val.startswith("bc1") or val.startswith("1") or val.startswith("3"): return "BITCOIN"
    elif val.startswith("0x"): return "ETHEREUM"
    return "ETHEREUM"

def thread_safe_file_write(ledger_data):
    with FILE_WRITE_LOCK:
        try:
            with open(JSON_FILE, "w", encoding="utf-8") as f: 
                json.dump(ledger_data, f, indent=4)
            with open(CSV_FILE, "w", newline="", encoding="utf-8") as f: 
                writer = csv.DictWriter(f, fieldnames=["Date", "Chain", "TXID", "From_Address", "To_Address", "Amount", "Asset", "Confidence", "Is_Consolidation", "Is_Terminal", "Cluster_ID", "Intent", "Obfuscation_Type", "Receiver_Entity"])
                writer.writeheader()
                for row in ledger_data:
                    writer.writerow({
                        "Date": row.get("timestamp"), "Chain": row.get("chain"), "TXID": row.get("tx"),
                        "From_Address": row.get("from"), "To_Address": row.get("to"), "Amount": row.get("amount"),
                        "Asset": row.get("ticker"), "Confidence": row.get("confidence"),
                        "Is_Consolidation": row.get("is_consolidation"), "Is_Terminal": row.get("is_terminal"),
                        "Cluster_ID": row.get("cluster"), "Intent": row.get("intent_action"), 
                        "Obfuscation_Type": row.get("obfuscation_path"), "Receiver_Entity": row.get("receiver_entity")
                    })
        except Exception: pass

async def file_writer_task():
    while True:
        await asyncio.sleep(5)
        if len(state.ledger) > 0:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(IO_POOL, thread_safe_file_write, list(state.ledger))

async def classify_tx_intent(tx: dict) -> dict:
    input_data = tx.get("input", "")
    method = input_data[:10].lower() if input_data and len(input_data) >= 10 else ""
    
    intent = {"action": "NATIVE_TRANSFER", "edge_type": "TRANSFER", "obf_path": "NONE"}
    if not input_data or input_data == "0x" or len(input_data) < 10: return intent

    if method in DEX_SWAP_SIGS: intent.update({"action": "DEX_SWAP", "edge_type": "SWAP", "obf_path": "DEX_ROUTING"})
    elif method in BRIDGE_HOP_SIGS: intent.update({"action": "CROSS_CHAIN_BRIDGE", "edge_type": "BRIDGE_HOP", "obf_path": "BRIDGE_HOP"})
    elif method in MIXER_SIGS: intent.update({"action": "MIXER_INTERACTION", "edge_type": "MIXER", "obf_path": "MIXER_USAGE"})
    elif method in CEX_DEPOSIT_SIGS: intent.update({"action": "CEX_DEPOSIT_SWEEP", "edge_type": "CEX_SWEEP", "obf_path": "CUSTODIAL_SETTLEMENT"})
    elif method in TRANSFER_SIGS: intent.update({"action": "TOKEN_TRANSFER", "edge_type": "TRANSFER"})
    return intent

class OSINT:
    def __init__(self):
        self.cache = {}

    async def resolve_address(self, addr, chain="ETHEREUM"):
        addr_lower = addr.lower()
        if addr_lower in self.cache: return self.cache[addr_lower]
        
        # Check Known Evidentiary Entities
        label = KNOWN_ENTITIES.get(addr_lower, None)
        if not label:
            label = f"{chain} Native Address" if chain in ["XRP", "SOLANA", "TRON", "BITCOIN"] else "Unknown Private Node"
                
        rich_entity = {"label": label}
        self.cache[addr_lower] = rich_entity
        return rich_entity

class ClusteringEngine:
    def __init__(self): 
        self.address_to_cluster = {}
        self.cluster_id_counter = 1
        
    def cluster_inputs(self, input_addresses):
        if len(input_addresses) < 2: return
        target_cluster = next((self.address_to_cluster[a] for a in input_addresses if a in self.address_to_cluster), None)
        if not target_cluster: 
            target_cluster = f"SYS-ACTOR-{self.cluster_id_counter:03d}"
            self.cluster_id_counter += 1
        for addr in input_addresses: self.address_to_cluster[addr] = target_cluster
        
    def assign_cluster(self, address, behavior_pattern):
        for cid, data in self.address_to_cluster.items():
            if isinstance(data, dict) and data.get('pattern') == behavior_pattern:
                data['members'].add(address)
                return cid
        new_cid = f"SYS-ACTOR-{self.cluster_id_counter:03d}"
        self.address_to_cluster[new_cid] = {"pattern": behavior_pattern, "members": {address}}
        self.cluster_id_counter += 1
        return new_cid

class CEX:
    def __init__(self):
        self.cex_keywords = ["MEXC", "BINANCE", "KRAKEN", "OKX", "COINBASE", "KUCOIN", "HOT WALLET", "EXCHANGE"]
        self.mixer_keywords = ["MIXER", "TORNADO CASH", "RAILGUN"]
        self.bridge_keywords = ["BRIDGE", "STARGATE", "MULTICHAIN", "ACROSS"]
    
    def classify(self, addr, osint_label):
        combined_lbl = osint_label.upper()
        if any(keyword in combined_lbl for keyword in self.cex_keywords): return "EXCHANGE_CUSTODIAL", 95
        if any(keyword in combined_lbl for keyword in self.bridge_keywords): return "CROSS_CHAIN_BRIDGE", 70
        if any(keyword in combined_lbl for keyword in self.mixer_keywords): return "MIXER_LIKE", 10
        return "PRIVATE_NODE", 10

class SOCState:
    def __init__(self):
        self.visited = set()
        self.ledger = []
        self.cex = CEX()
        self.clustering = ClusteringEngine()
        self.osint = OSINT()
        self.seeds = []
        self.seed_chains = {}
        self.queue = asyncio.Queue()
        self.state_lock = asyncio.Lock()
        self.inbound_sources = defaultdict(set) 
        
    def setup(self, seeds, target_amount, default_chain="AUTO"):
        self.seeds = []
        for seed in seeds:
            chain = detect_chain(seed, default_chain)
            # EVM normalization
            if chain == "ETHEREUM": seed = seed.lower()
            
            self.seeds.append(seed)
            self.seed_chains[seed] = chain
            self.queue.put_nowait((seed, 0, target_amount, "NONE", chain, seed)) 

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_mongodb()
    yield

app = FastAPI(lifespan=lifespan)
state = SOCState()
clients = set()
active_engine_task = None

def get_asset_ticker(chain: str) -> str:
    return "BTC" if chain == "BITCOIN" else "ETH"

async def fetch_txs(session, addr, chain):
    headers = {"User-Agent": "Mozilla/5.0"}
    if chain == "BITCOIN":
        for attempt in range(4):
            try:
                async with session.get(f"https://mempool.space/api/address/{addr}/txs", headers=headers, timeout=12) as r:
                    if r.status == 200: 
                        res = await r.json()
                        if isinstance(res, list): return res[::-1] # Reverse for chronological
                    elif r.status == 429: await asyncio.sleep(2 ** attempt)
            except: await asyncio.sleep(1)
        return []
    else:
        domain = EVM_DOMAINS.get(chain, "api.etherscan.io")
        api_key = CONFIG["ETHERSCAN_API_KEY"] if chain == "ETHEREUM" else CONFIG.get(f"{chain}SCAN_API_KEY", CONFIG["ETHERSCAN_API_KEY"])
        # sort=asc guarantees chronological forward tracing
        url_native = f"https://{domain}/api?module=account&action=txlist&address={addr}&startblock=0&endblock=99999999&page=1&offset=200&sort=asc&apikey={api_key}"
        url_token = f"https://{domain}/api?module=account&action=tokentxns&address={addr}&startblock=0&endblock=99999999&page=1&offset=200&sort=asc&apikey={api_key}"
        
        combined = []
        try:
            async with session.get(url_native, headers=headers, timeout=10) as r:
                if r.status == 200:
                    data = await r.json()
                    res = data.get("result", [])
                    if isinstance(res, list): combined.extend(res)
            async with session.get(url_token, headers=headers, timeout=10) as rt:
                if rt.status == 200:
                    data = await rt.json()
                    res = data.get("result", [])
                    if isinstance(res, list): combined.extend(res)
        except Exception as e: print(f"API Error: {e}")
        return combined

async def process_bitcoin_txs(addr, txs, depth, carry_val, obf_path, chain, origin_seed):
    if not isinstance(txs, list): return
    for tx in txs:
        if not isinstance(tx, dict): continue
        txid = tx.get("txid", "Unknown")
        ts = tx.get("status", {}).get("block_time", 0)
        timestamp = datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S') if ts else datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
        
        inputs = [i.get("prevout", {}).get("scriptpubkey_address") for i in tx.get("vin", []) if isinstance(i.get("prevout"), dict)]
        inputs = [a for a in inputs if a]
        state.clustering.cluster_inputs(inputs)
        
        if addr in inputs:
            for o in tx.get("vout", []):
                to = o.get("scriptpubkey_address")
                if not to or to == addr: continue
                amt = int(o.get("value", 0)) / 1e8
                if amt < 0.0001: continue
                
                # Check target thresholds to prevent infinite irrelevant spam
                if depth > 5 and amt < 0.05: continue
                
                intent_data = {"action": "PEEL_CHAIN_TRANSFER" if amt < 1.0 else "NATIVE_TRANSFER", "edge_type": "UTXO_TRANSFER", "obf_path": obf_path}
                await process_hop(addr, to, amt, txid, timestamp, depth, chain, origin_seed, intent_data, "BTC")

async def process_evm_txs(addr, txs, depth, carry_val, obf_path, chain, origin_seed):
    if not isinstance(txs, list): return
    for tx in txs:
        if not isinstance(tx, dict): continue
        txid = tx.get("hash", "Unknown")
        to = str(tx.get("to", "") or "").lower()
        f_addr = str(tx.get("from", "") or "").lower()
        
        if not to or f_addr != addr.lower(): continue
        
        intent_data = await classify_tx_intent(tx)
        
        token_sym = tx.get("tokenSymbol", "")
        if token_sym:
            dec = int(tx.get("tokenDecimal", 18) or 18)
            try: amt = float(tx.get("value", "0")) / (10**dec)
            except: amt = 0.0
            ticker = token_sym.upper()
        else:
            try: amt = float(tx.get("value", "0")) / 1e18
            except: amt = 0.0
            ticker = get_asset_ticker(chain)
            
        if amt <= 0.00001: continue
        
        try: ts = datetime.fromtimestamp(int(tx.get("timeStamp", 0) or 0)).strftime('%Y-%m-%d %H:%M:%S')
        except: ts = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
        
        await process_hop(f_addr, to, amt, txid, ts, depth, chain, origin_seed, intent_data, ticker)

async def process_hop(addr, to, amt, txid, timestamp, depth, chain, origin_seed, intent_data, ticker_override=None):
    tx_entities_to = await state.osint.resolve_address(to, chain) 
    tx_entities_from = await state.osint.resolve_address(addr, chain) 
    receiver_entity_lbl = tx_entities_to["label"]
    sender_entity_lbl = tx_entities_from["label"]
    
    entity_class, score = state.cex.classify(to, receiver_entity_lbl)
    
    async with state.state_lock:
        state.inbound_sources[to].add(addr)
        is_consolidation = len(state.inbound_sources[to]) > 1 
        
    cluster_id = state.clustering.assign_cluster(to, f"depth_{depth}_class_{entity_class}") 
    ticker = ticker_override if ticker_override else get_asset_ticker(chain)
    is_terminal = "EXCHANGE" in entity_class or "CUSTODIAL" in entity_class
    
    # Behavior override based on OSINT
    if "Tornado" in receiver_entity_lbl or "Mixer" in receiver_entity_lbl:
        intent_data["action"] = "MIXER_INTERACTION"
        intent_data["obf_path"] = "PROTOCOL_OBFUSCATION"
    elif is_terminal:
        intent_data["action"] = "CEX_DEPOSIT_SWEEP"

    confidence_level = "High-Confidence Analytical Link" if is_consolidation or intent_data["obf_path"] != "NONE" else "Confirmed On-Chain Fact"
    
    if to not in state.visited and depth < MAX_DEPTH and not is_terminal: 
        state.queue.put_nowait((to, depth + 1, amt, intent_data["obf_path"], chain, origin_seed))

    node = {
        "type": "LEDGER", "chain": chain, "ticker": ticker,
        "timestamp": timestamp, "from": addr, "sender_entity": sender_entity_lbl,
        "to": to, "receiver_entity": receiver_entity_lbl, "tx": txid, 
        "amount": amt, "usd": amt * USD_RATES.get(chain, 1), 
        "cluster": cluster_id, "entity_class": entity_class, 
        "is_terminal": is_terminal, "is_consolidation": is_consolidation,
        "confidence": confidence_level, "origin_seed": origin_seed,
        "intent_action": intent_data.get("action", "TRANSFER"),
        "obfuscation_path": intent_data.get("obf_path", "NONE"),
        "edge_type": intent_data.get("edge_type", "TRANSFER")
    }
    
    async with state.state_lock:
        state.ledger.append(node)
        
    for ws in list(clients):
        try: await ws.send_json(node)
        except: clients.discard(ws)

async def engine_worker(session):
    while True: 
        item = await state.queue.get()
        try: 
            addr, depth, carry_val, obf_path, chain, origin_seed = item
            async with state.state_lock:
                if addr in state.visited or depth > MAX_DEPTH: 
                    continue
                state.visited.add(addr)
                
            txs = await fetch_txs(session, addr, chain)
            if txs:
                if chain == "BITCOIN": await process_bitcoin_txs(addr, txs, depth, carry_val, obf_path, chain, origin_seed)
                else: await process_evm_txs(addr, txs, depth, carry_val, obf_path, chain, origin_seed)
        except Exception as e: pass
        finally:
            state.queue.task_done()

async def engine_loop():
    try:
        writer_task = asyncio.create_task(file_writer_task()) 
        async with aiohttp.ClientSession() as session:
            workers = [asyncio.create_task(engine_worker(session)) for _ in range(CONCURRENCY_LIMIT)]
            await state.queue.join()
            for w in workers: w.cancel()
            writer_task.cancel()
            
            thread_safe_file_write(list(state.ledger))
            for ws in list(clients):
                try: await ws.send_json({"type": "COMPLETE"})
                except: pass
    except Exception as e: traceback.print_exc()

class TraceRequest(BaseModel):
    seeds: str
    target_amount: str = ""
    chain_override: str = "AUTO"

@app.post("/api/start_trace")
async def api_start_trace(req: TraceRequest):
    global active_engine_task
    if active_engine_task and not active_engine_task.done(): active_engine_task.cancel()
    seeds_list = [s.strip() for s in req.seeds.split('\n') if s.strip()]
    
    state.__init__()
    state.setup(seeds_list, 80000.0, req.chain_override)
    
    for ws in list(clients):
        try: await ws.send_json({"type": "INIT", "seeds": state.seeds, "seed_chains": state.seed_chains})
        except: pass
        
    active_engine_task = asyncio.create_task(engine_loop())
    return {"status": "started"}

@app.websocket("/ws")
async def ws(websocket: WebSocket):
    await websocket.accept()
    clients.add(websocket)
    try:
        while True: await websocket.receive_text()
    except: clients.discard(websocket)

@app.get("/")
def dashboard():
    html_content = r"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <title>Evidentiary Transaction Graph - LGN-US-2026-0172</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <script src="https://cdn.jsdelivr.net/npm/vis-network@9.1.2/standalone/umd/vis-network.min.js"></script>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;700&display=swap');
            
            body { font-family: 'Inter', sans-serif; background-color: #f8fafc; margin: 0; padding: 0; overflow: hidden; overscroll-behavior: none; }
            .font-mono { font-family: 'JetBrains Mono', monospace; }
            
            #network-graph { 
                width: 100vw; height: 100vh; outline: none; 
                background-image: radial-gradient(#cbd5e1 1px, transparent 1px); background-size: 24px 24px;
                touch-action: none;
            }
            
            .glass-panel { 
                background: rgba(255, 255, 255, 0.95); border: 1px solid #e2e8f0; 
                backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);
                box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.05), 0 8px 10px -6px rgba(0, 0, 0, 0.01); 
            }

            /* Plain text tooltip parsing */
            div.vis-tooltip {
                font-family: 'JetBrains Mono', monospace !important; font-size: 11px !important;
                background-color: #0f172a !important; border: 1px solid #334155 !important;
                box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5) !important; color: #f8fafc !important;
                border-radius: 6px !important; padding: 14px 18px !important;
                white-space: pre-wrap !important; line-height: 1.6 !important; z-index: 100 !important;
            }
            .no-scrollbar::-webkit-scrollbar { display: none; }
            .no-scrollbar { -ms-overflow-style: none; scrollbar-width: none; }
        </style>
    </head>
    <body class="text-slate-800">

        <!-- Top Navigation Bar -->
        <header class="absolute top-0 w-full glass-panel z-20 flex flex-col md:flex-row justify-between items-center px-4 py-3 gap-3 shadow-sm">
            <div class="flex items-center gap-3 w-full md:w-auto">
                <div class="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center shadow-inner shrink-0">
                    <svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"></path></svg>
                </div>
                <div class="flex-grow">
                    <h1 class="text-sm font-black uppercase tracking-wider text-slate-900 leading-tight">Evidentiary Trace</h1>
                    <p class="text-[10px] text-slate-500 font-mono font-semibold truncate">CASE: LGN-US-2026-0172 | LIVE STREAM</p>
                </div>
            </div>
            
            <div class="flex items-center gap-2 w-full md:w-auto overflow-x-auto no-scrollbar pb-1 md:pb-0 justify-between md:justify-end">
                <button onclick="toggleLegend()" class="md:hidden px-3 py-2 bg-slate-100 border border-slate-300 rounded-md text-xs font-bold text-slate-700 flex-shrink-0 flex items-center gap-1 shadow-sm">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16m-7 6h7"></path></svg>
                </button>
                
                <button id="traceBtn" onclick="submitTrace()" class="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 border border-emerald-700 rounded-md text-xs font-bold text-white transition flex-shrink-0 flex items-center gap-2 shadow-md">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"></path><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                    <span class="hidden sm:inline">Start Trace</span>
                    <span class="sm:hidden">Trace</span>
                </button>

                <button onclick="exportCSV()" class="px-3 py-2 bg-slate-800 hover:bg-slate-900 border border-slate-900 rounded-md text-xs font-bold text-white transition flex-shrink-0 flex items-center gap-2 shadow-md">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path></svg>
                    <span class="hidden sm:inline">Download CSV</span>
                    <span class="sm:hidden">CSV</span>
                </button>

                <button onclick="downloadSnapshot()" class="px-3 py-2 bg-blue-600 hover:bg-blue-700 border border-blue-700 rounded-md text-xs font-bold text-white transition shadow-md flex-shrink-0 flex items-center gap-2">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"></path></svg>
                    <span class="hidden sm:inline">Download Image</span>
                    <span class="sm:hidden">Image</span>
                </button>

                <button onclick="network.fit({animation: {duration: 800, easingFunction: 'easeInOutQuad'}})" class="px-3 py-2 bg-white border border-slate-300 rounded-md text-xs font-bold text-slate-700 hover:bg-slate-50 transition flex-shrink-0 flex items-center shadow-sm">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4"></path></svg>
                </button>
            </div>
        </header>

        <main class="relative h-screen w-full pt-28 md:pt-16">
            <div id="network-graph" class="h-full w-full"></div>

            <div id="legend-panel" class="hidden md:block glass-panel absolute top-32 md:top-6 left-4 md:left-6 p-4 rounded-xl z-10 w-[280px] transition-all duration-300 shadow-lg">
                <div class="flex justify-between items-center mb-3 border-b border-slate-200 pb-2">
                    <h3 class="text-[10px] font-black text-slate-500 uppercase tracking-widest">Forensic Legend</h3>
                    <button onclick="toggleLegend()" class="md:hidden text-slate-400 hover:text-slate-600"><svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg></button>
                </div>
                <div class="flex flex-col gap-3">
                    <div class="flex items-center gap-3">
                        <div class="w-8 h-8 rounded-full border-[3px] border-red-500 bg-red-50 flex items-center justify-center shrink-0">
                            <span class="text-xs font-bold text-red-500">O</span>
                        </div>
                        <div>
                            <p class="text-xs font-bold text-slate-800">Origin Seed</p>
                            <p class="text-[9px] text-slate-500">Compromised Victim Wallet</p>
                        </div>
                    </div>
                    <div class="flex items-center gap-3">
                        <div class="w-8 h-8 rounded-full border-[2px] border-slate-300 bg-white flex items-center justify-center shrink-0">
                            <span class="text-xs font-bold text-slate-400">I</span>
                        </div>
                        <div>
                            <p class="text-xs font-bold text-slate-800">Intermediary Node</p>
                            <p class="text-[9px] text-slate-500">Laundering Hop / Peel Chain</p>
                        </div>
                    </div>
                    <div class="flex items-center gap-3">
                        <div class="w-8 h-8 rounded-full border-[3px] border-purple-500 bg-purple-50 flex items-center justify-center shrink-0">
                            <img src="https://cryptologos.cc/logos/tornado-cash-torn-logo.png" class="w-5 h-5">
                        </div>
                        <div>
                            <p class="text-xs font-bold text-slate-800">Mixer Router</p>
                            <p class="text-[9px] text-slate-500">Protocol Obfuscation</p>
                        </div>
                    </div>
                    <div class="flex items-center gap-3">
                        <div class="w-8 h-8 rounded-full border-[3px] border-emerald-500 bg-emerald-50 flex items-center justify-center shrink-0">
                            <img src="https://cryptologos.cc/logos/binance-coin-bnb-logo.png" class="w-5 h-5">
                        </div>
                        <div>
                            <p class="text-xs font-bold text-slate-800">Exchange (CEX)</p>
                            <p class="text-[9px] text-slate-500">Terminal Subpoena Target</p>
                        </div>
                    </div>
                </div>
            </div>

            <div id="alert-box" class="absolute bottom-6 right-4 md:bottom-8 md:right-8 bg-slate-900 border border-slate-700 text-white px-4 py-3 md:px-6 md:py-4 rounded-lg shadow-2xl font-bold text-xs md:text-sm transform translate-y-24 opacity-0 transition-all duration-300 z-50 flex items-center gap-3 pointer-events-none">
                <div class="w-8 h-8 bg-emerald-500/20 rounded-full flex items-center justify-center shrink-0">
                    <svg class="w-5 h-5 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>
                </div>
                <span id="alert-msg">Action Successful.</span>
            </div>

            <div id="loader" class="absolute inset-0 bg-slate-50/90 backdrop-blur-sm flex flex-col items-center justify-center z-50 transition-opacity duration-500 hidden">
                <div class="w-14 h-14 border-4 border-slate-200 border-t-emerald-600 rounded-full animate-spin mb-4 shadow-md"></div>
                <p class="text-sm font-bold text-slate-700 animate-pulse">Tracing Unredacted Ledger...</p>
            </div>
            
            <div class="absolute bottom-4 left-4 z-0 pointer-events-none opacity-40 hidden md:block">
                <p class="text-[10px] font-mono font-bold text-slate-500">Generated by Lionsgate Intelligence Network</p>
            </div>
        </main>

        <script>
            // Target Seeds Input by User
            const targetSeeds = "1NV7GCWYo7Tr3hErJzLRk4n2oV5B88eCNU\nbc1qprtnld4jf43uq6h9y460d76annunqag9dhcv52\n0x7675DC2856fca0C22ed3C57979388FbF236De57F\n0x616C6bb9d5BB443D03a7bD5746404897de106A93";
            window.exportedDataRows = [];

            // Asset Icons
            const getIconUrl = (entity, ticker, chain) => {
                let uE = String(entity||"").toUpperCase();
                let uT = String(ticker||"").toUpperCase();
                if (uE.includes("BINANCE")) return "https://cryptologos.cc/logos/binance-coin-bnb-logo.png";
                if (uE.includes("OKX") || uE.includes("OKB")) return "https://cryptologos.cc/logos/okb-okb-logo.png";
                if (uE.includes("TORNADO") || uE.includes("MIXER")) return "https://cryptologos.cc/logos/tornado-cash-torn-logo.png";
                if (uT === "USDC") return "https://cryptologos.cc/logos/usd-coin-usdc-logo.png";
                if (uT === "USDT") return "https://cryptologos.cc/logos/tether-usdt-logo.png";
                if (chain === "BITCOIN") return "https://cryptologos.cc/logos/bitcoin-btc-logo.png";
                if (chain === "ETHEREUM") return "https://cryptologos.cc/logos/ethereum-eth-logo.png";
                return "https://cdn-icons-png.flaticon.com/512/2601/2601431.png"; // Fallback generic wallet
            };

            const getEdgeIcon = (ticker) => {
                if (ticker === "BTC") return "₿";
                if (ticker === "ETH") return "🔷";
                if (ticker === "USDC" || ticker === "USDT") return "💵";
                return "🪙";
            };

            const THEME = {
                seed: { bg: '#fef2f2', border: '#ef4444' },     
                hop: { bg: '#ffffff', border: '#94a3b8' },      
                mixer: { bg: '#fdf4ff', border: '#a855f7' },    
                terminal: { bg: '#ecfdf5', border: '#10b981' }  
            };

            let nodes = new vis.DataSet();
            let edges = new vis.DataSet();
            let network;

            function toggleLegend() {
                document.getElementById('legend-panel').classList.toggle('hidden');
            }

            function showAlert(msg) {
                const alertBox = document.getElementById('alert-box');
                document.getElementById('alert-msg').innerText = msg;
                alertBox.classList.remove('translate-y-24', 'opacity-0');
                setTimeout(() => { alertBox.classList.add('translate-y-24', 'opacity-0'); }, 3000);
            }

            async function submitTrace() {
                document.getElementById('loader').classList.remove('hidden');
                document.getElementById('traceBtn').innerHTML = "Tracing...";
                try {
                    await fetch('/api/start_trace', {
                        method: 'POST', headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({ seeds: targetSeeds, target_amount: "0", chain_override: "AUTO" })
                    });
                } catch(e) {}
            }

            function exportCSV() {
                if(window.exportedDataRows.length === 0) return showAlert("No trace data available.");
                let csv = "Date/Time (UTC),TX Hash,From Wallet,To Wallet,Receiver Entity,Amount,Asset,Transaction Type,Behavioral Cluster,Confidence\n";
                
                window.exportedDataRows.forEach(r => {
                    let cleanEntity = String(r.receiver_entity).replace(/"/g, '""');
                    csv += `"${r.timestamp}","${r.tx}","${r.from}","${r.to}","${cleanEntity}","${r.amount}","${r.ticker}","${r.intent_action}","${r.cluster}","${r.confidence}"\n`;
                });
                
                const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
                const url = URL.createObjectURL(blob);
                const link = document.createElement("a");
                link.setAttribute("href", url);
                link.setAttribute("download", "LGN-US-2026-0172-Full-Trace.csv");
                document.body.appendChild(link); link.click(); document.body.removeChild(link);
                URL.revokeObjectURL(url);
                showAlert("Full CSV Ledger Downloaded.");
            }

            function initGraph() {
                const container = document.getElementById('network-graph');
                const isMobile = window.innerWidth < 768;

                const options = {
                    layout: {
                        hierarchical: {
                            enabled: true, direction: 'LR', sortMethod: 'directed',
                            levelSeparation: isMobile ? 260 : 420, 
                            nodeSpacing: isMobile ? 140 : 200,
                            treeSpacing: 250, parentCentralization: true
                        }
                    },
                    physics: { enabled: false },
                    interaction: { hover: true, tooltipDelay: 50, zoomView: true, dragView: true },
                    edges: {
                        arrows: { to: { enabled: true, scaleFactor: 0.75, type: 'arrow' } },
                        smooth: { type: 'cubicBezier', forceDirection: 'horizontal', roundness: 0.6 },
                        shadow: { enabled: true, color: 'rgba(0,0,0,0.06)', size: 4, x: 2, y: 2 },
                        font: { face: 'Inter', size: 10, align: 'middle', background: 'rgba(248,250,252,0.95)', strokeWidth: 0, multi: false, color: '#334155' }
                    },
                    nodes: {
                        font: { face: 'Inter', size: 11, color: '#1e293b', align: 'center', multi: false, vadjust: -5 },
                        shadow: { enabled: true, color: 'rgba(0,0,0,0.1)', size: 10, x: 2, y: 4 }, margin: 12
                    }
                };

                network = new vis.Network(container, {nodes, edges}, options);
            }

            function downloadSnapshot() {
                const networkCanvas = document.querySelector('#network-graph canvas');
                if (!networkCanvas) return;

                const tempCanvas = document.createElement('canvas');
                tempCanvas.width = networkCanvas.width;
                tempCanvas.height = networkCanvas.height;
                const ctx = tempCanvas.getContext('2d');

                ctx.fillStyle = '#f8fafc';
                ctx.fillRect(0, 0, tempCanvas.width, tempCanvas.height);
                ctx.fillStyle = '#cbd5e1';
                for(let x=0; x<tempCanvas.width; x+=24) {
                    for(let y=0; y<tempCanvas.height; y+=24) {
                        ctx.beginPath(); ctx.arc(x, y, 1, 0, Math.PI * 2); ctx.fill();
                    }
                }
                ctx.drawImage(networkCanvas, 0, 0);
                ctx.font = "bold 14px 'JetBrains Mono', monospace";
                ctx.fillStyle = "rgba(100, 116, 139, 0.6)"; 
                ctx.fillText("Produced by Lionsgate Intelligence Network - Case: LGN-US-2026-0172", 20, tempCanvas.height - 20);

                tempCanvas.toBlob(function(blob) {
                    const url = URL.createObjectURL(blob);
                    const link = document.createElement('a');
                    link.download = 'LGN-US-2026-0172-Evidentiary-Graph.png';
                    link.href = url;
                    document.body.appendChild(link); link.click(); document.body.removeChild(link);
                    URL.revokeObjectURL(url);
                    showAlert("Graph Snapshot Downloaded.");
                }, 'image/png');
            }

            // WebSocket live connection to graph
            let wsProtocol = window.location.protocol === "https:" ? "wss://" : "ws://";
            let ws = new WebSocket(wsProtocol + window.location.host + "/ws");

            ws.onmessage = (msg) => {
                let d = JSON.parse(msg.data);
                
                if(d.type === "INIT") {
                    nodes.clear(); edges.clear(); window.exportedDataRows = [];
                    return;
                }
                
                if(d.type === "COMPLETE") {
                    document.getElementById('loader').classList.add('hidden');
                    document.getElementById('traceBtn').innerHTML = "Trace Complete";
                    network.fit({animation: {duration: 800, easingFunction: 'easeInOutQuad'}});
                    showAlert("Tracing Completed.");
                    return;
                }

                if (d.type === "LEDGER") {
                    let safeFrom = d.from.length > 8 ? d.from.substring(0,8) + "..." : d.from;
                    let safeTo = d.to.length > 8 ? d.to.substring(0,8) + "..." : d.to;
                    let isSeed = targetSeeds.toLowerCase().includes(d.from.toLowerCase());
                    
                    let bg = isSeed ? THEME.seed.bg : (d.is_terminal ? THEME.terminal.bg : (d.obfuscation_path !== "NONE" ? THEME.mixer.bg : THEME.hop.bg));
                    let border = isSeed ? THEME.seed.border : (d.is_terminal ? THEME.terminal.border : (d.obfuscation_path !== "NONE" ? THEME.mixer.border : THEME.hop.border));
                    let bw = isSeed ? 3 : (d.is_terminal ? 4 : 2);
                    
                    // Plain Text Tooltips ONLY
                    let ttNodeFrom = `[ NODE DOSSIER ]\nADDRESS: ${d.from}\nENTITY: ${d.sender_entity}\nCHAIN: ${d.chain}\nATTRIBUTION: Lionsgate Intel`;
                    let ttNodeTo = `[ NODE DOSSIER ]\nADDRESS: ${d.to}\nENTITY: ${d.receiver_entity}\nCLUSTER: ${d.cluster}\nCHAIN: ${d.chain}\nATTRIBUTION: Lionsgate Intel`;
                    let ttEdge = `[ EVIDENTIARY TX ]\nTXID: ${d.tx}\nDATE: ${d.timestamp}\nBEHAVIOR: ${d.intent_action}\nCONFIDENCE: ${d.confidence}\nATTRIBUTION: Lionsgate Intel`;

                    let iconFrom = getIconUrl(d.sender_entity, d.ticker, d.chain);
                    let iconTo = getIconUrl(d.receiver_entity, d.ticker, d.chain);

                    if (!nodes.get(d.from)) nodes.add({ id: d.from, label: `Origin/Sender\n${safeFrom}`, title: ttNodeFrom, shape: 'circularImage', image: iconFrom, size: isSeed ? 28 : 22, color: { background: bg, border: border }, borderWidth: bw });
                    
                    let toLabel = d.is_terminal ? `CEX Deposit\n${safeTo}` : `Intermediary\n${safeTo}`;
                    if (d.is_consolidation) toLabel += `\n[Recombination]`;
                    
                    if (!nodes.get(d.to)) {
                        let toBg = d.is_terminal ? THEME.terminal.bg : THEME.hop.bg;
                        let toBorder = d.is_terminal ? THEME.terminal.border : THEME.hop.border;
                        if(d.obfuscation_path !== "NONE" || String(d.receiver_entity).toUpperCase().includes("MIXER")) { toBg = THEME.mixer.bg; toBorder = THEME.mixer.border; }
                        nodes.add({ id: d.to, label: toLabel, title: ttNodeTo, shape: 'circularImage', image: iconTo, size: d.is_terminal ? 36 : 24, color: { background: toBg, border: toBorder }, borderWidth: d.is_terminal ? 4 : 2 });
                    } else if(d.is_terminal || d.is_consolidation) {
                        let n = nodes.get(d.to);
                        if (!n.label.includes("[Recombination]")) n.label += `\n[Recombination]`;
                        nodes.update({id: d.to, label: n.label, color: {background: THEME.terminal.bg, border: THEME.terminal.border}, borderWidth: 4, image: iconTo});
                    }

                    let edgeId = d.from + "-" + d.to + "-" + d.tx;
                    if (!edges.get(edgeId)) {
                        let edgeIcon = getEdgeIcon(d.ticker);
                        let edgeLabelStr = `${edgeIcon} ${d.amount.toFixed(4)} ${d.ticker}\n${d.intent_action}`;
                        let eColor = d.is_terminal ? '#10b981' : (d.obfuscation_path !== "NONE" ? '#a855f7' : '#94a3b8');
                        
                        edges.add({ id: edgeId, from: d.from, to: d.to, label: edgeLabelStr, title: ttEdge, font: {color: eColor}, color: { color: eColor, highlight: eColor }, width: d.is_terminal ? 3 : 2 });
                        window.exportedDataRows.push(d);
                    }
                }
            };

            window.addEventListener('resize', () => {
                if(network) {
                    const isMobile = window.innerWidth < 768;
                    network.setOptions({ layout: { hierarchical: { levelSeparation: isMobile ? 260 : 420, nodeSpacing: isMobile ? 140 : 200 } } });
                }
            });

            window.addEventListener('load', initGraph);
        </script>
    </body>
    </html>
    """
    return HTMLResponse(html_content)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, loop="asyncio", ws="websockets", http="h11")