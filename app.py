import sys
import os
import logging
import certifi
import warnings
warnings.simplefilter('ignore', FutureWarning)
import subprocess
import importlib.util
import asyncio
import aiohttp
import json
from adapters.ankr_adapter import AnkrAdapter
from adapters.bitquery_adapter import BitqueryAdapter
from adapters.tatum_adapter import TatumAdapter

# --- NEMESIS AI & AUTO-LEARN ---
try:
    from core.nemesis_llm import nemesis_ai_engine
    from services.auto_ingest import ingest_engine
    ingest_engine.start()
except Exception as e:
    print(f"[BOOT] NEMESIS AI Modules failed to load: {e}")
from collections import defaultdict
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, Request, BackgroundTasks, WebSocketDisconnect, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse, HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import csv
import io
import zipfile
import asyncpg
from google import genai

# --- GBIO ONTOLOGY INJECTION ---
try:
    from services.gbio_ontology import (
        GBIOEngine, GBIONode, GBIOEdge, TransferAction, EntityClass, 
        BlockchainNetwork, ThreatLevel, EvidenceRecord, RiskProfile, 
        BehavioralIndicator, AMLFlag, GBIONormalizer
    )
except ImportError:
    # If placed in root during refactor
    from gbio_ontology import (
        GBIOEngine, GBIONode, GBIOEdge, TransferAction, EntityClass, 
        BlockchainNetwork, ThreatLevel, EvidenceRecord, RiskProfile, 
        BehavioralIndicator, AMLFlag, GBIONormalizer
    )

# --- MOCK IMPORTS FOR COMPATIBILITY ---
class MockIntelligencePipeline:
    @staticmethod
    async def run(addr): return {"nodes": [{"properties": {"name": "Test Entity"}}], "edges": []}
IntelligencePipeline = MockIntelligencePipeline

class MockHeuristicEngine:
    @staticmethod
    def enrich_hop_metadata(addr, chain, amt, txs=None): return {"entity_type": "UNKNOWN", "heuristic_flags": []}
HeuristicEngine = MockHeuristicEngine

class MockTransferAnalyzer:
    @staticmethod
    def classify_transfer(tx, a, b):
        class T:
            value = "TRANSFER"
        return T()
TransferAnalyzer = MockTransferAnalyzer

class MockUniversalDecoder:
    @staticmethod
    async def process_transaction(session, tx_data, chain): return {"protocol": "Unknown", "decoded": {"type": "Transfer"}}
UniversalDecoder = MockUniversalDecoder

class MockAttributionEngine:
    @staticmethod
    def generate_entity_dossier(target_entity, chain, txs): return {"risk_score": 10, "aml_flags": []}
AttributionEngine = MockAttributionEngine

class MockGraphIntelligence:
    def build_graph_from_edges(self, edges): pass
    def compute_pagerank(self): return {}
    def detect_cross_chain_correlations(self): return []
GraphIntelligence = MockGraphIntelligence

async def aggregate_osint(addr, a, b, chain): return {"entity_name": "Wallet"}
def run_syndicate_clustering(edges): return {}

# --- PYTHON 3.13 WINDOWS EVENT LOOP KERNEL PATCH ---
if os.name == 'nt':
    import asyncio
    asyncio.WindowsSelectorEventLoopPolicy = asyncio.WindowsProactorEventLoopPolicy
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    import socket
    _orig_getpeername = socket.socket.getpeername
    def _safe_getpeername(self):
        try: return _orig_getpeername(self)
        except OSError as e:
            if getattr(e, 'winerror', None) == 10014: return ('0.0.0.0', 0)
            raise
    socket.socket.getpeername = _safe_getpeername

os.environ['SSL_CERT_FILE'] = certifi.where()
os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()

# Unified Global Logger
log_formatter = logging.Formatter('%(asctime)s [%(levelname)s] [NEMESIS] %(message)s')
logger = logging.getLogger("NEMESIS_CORE")
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setFormatter(log_formatter)
logger.addHandler(ch)

GLOBAL_API_SEMAPHORE = asyncio.Semaphore(10)

# ==============================================================================
# 1. CONFIGURATION & STATE MATRIX
# ==============================================================================
load_dotenv()

class Config:
    _depth_str = os.getenv("TRACE_MAX_DEPTH", "15")
    MAX_DEPTH = 9999 if _depth_str.upper() == "UNLIMITED" else int(_depth_str) if _depth_str.isdigit() else 15
    CONCURRENCY_LIMIT = 50 # Lowered to prevent lockups, optimized for batching
    
    # Generic Parsers
    TATUM_KEYS = [k.strip() for k in os.getenv("TATUM_API_KEY", os.getenv("VITE_TATUM_API_KEY", "")).split(",") if k.strip()]
    INFURA_KEYS = [k.strip() for k in os.getenv("INFURA_API_KEY", os.getenv("VITE_INFURA_API_KEY", "")).split(",") if k.strip()]
    _all_gemini = [k.strip().replace('"', '').replace("'", "") for k in os.getenv("GEMINI_API_KEYS", os.getenv("VITE_GEMINI_API_KEYS", "")).split(",") if k.strip()]
    GEMINI_KEYS = [k for k in _all_gemini if k.startswith("AIza") or k.startswith("AQ.")]
    
    EXPLORER_KEYS = {
        "ETHEREUM": [k.strip() for k in os.getenv("ETHERSCAN_API_KEY", os.getenv("VITE_ETHERSCAN_API_KEY", "")).split(",") if k.strip()],
        "BSC": [k.strip() for k in os.getenv("BSCSCAN_API_KEY", os.getenv("VITE_BSCSCAN_API_KEY", "")).split(",") if k.strip()],
        "POLYGON": [k.strip() for k in os.getenv("POLYGONSCAN_API_KEY", os.getenv("VITE_POLYGONSCAN_API_KEY", "")).split(",") if k.strip()],
        "AVALANCHE": [k.strip() for k in os.getenv("SNOWTRACE_API_KEY", os.getenv("VITE_SNOWTRACE_API_KEY", "")).split(",") if k.strip()],
        "ARBITRUM": [k.strip() for k in os.getenv("ARBISCAN_API_KEY", os.getenv("VITE_ARBISCAN_API_KEY", "")).split(",") if k.strip()],
        "OPTIMISM": [k.strip() for k in os.getenv("OPTIMISMSCAN_API_KEY", os.getenv("VITE_OPTIMISMSCAN_API_KEY", "")).split(",") if k.strip()],
        "BASE": [k.strip() for k in os.getenv("BASESCAN_API_KEY", os.getenv("VITE_BASESCAN_API_KEY", "")).split(",") if k.strip()],
        "CELO": [k.strip() for k in os.getenv("CELOSCAN_API_KEY", os.getenv("VITE_CELOSCAN_API_KEY", "")).split(",") if k.strip()],
        "LINEA": [k.strip() for k in os.getenv("LINEASCAN_API_KEY", os.getenv("VITE_LINEASCAN_API_KEY", "")).split(",") if k.strip()],
        "TRON": [os.getenv("TRONSCAN_API_KEY", os.getenv("VITE_TRONSCAN_API_KEY", ""))]
    }
    
    GETBLOCK_KEYS = [k.strip() for k in os.getenv("GETBLOCK_ETH_KEY", os.getenv("VITE_GETBLOCK_ETH_KEY", "")).split(",") if k.strip()] + [k.strip() for k in os.getenv("GETBLOCK_BTC_KEY", os.getenv("VITE_GETBLOCK_BTC_KEY", "")).split(",") if k.strip()]
    VALIDATION_KEYS = [k.strip() for k in os.getenv("VALIDATION_ETH", os.getenv("VITE_VALIDATION_ETH", "")).split(",") if k.strip()] + [k.strip() for k in os.getenv("VALIDATION_BTC", os.getenv("VITE_VALIDATION_BTC", "")).split(",") if k.strip()]
    PUBLICNODE_KEYS = [k.strip() for k in os.getenv("PUBLICNODE_BASE_WSS", os.getenv("VITE_PUBLICNODE_BASE_WSS", "")).split(",") if k.strip()]
    EVM_DOMAINS = {
        "ETHEREUM": "api.etherscan.io", "BSC": "api.bscscan.com", "POLYGON": "api.polygonscan.com", 
        "BASE": "api.basescan.org", "ARBITRUM": "api.arbiscan.io", "AVALANCHE": "api.snowtrace.io",
        "OPTIMISM": "api-optimistic.etherscan.io", "CELO": "api.celoscan.io", "LINEA": "api.lineascan.build"
    }
    USD_RATES = { "KASPA": 0.036, "ETHEREUM": 3100.0, "BSC": 580.0, "POLYGON": 0.65, "AVALANCHE": 35.0, "ARBITRUM": 3100.0, "BASE": 3100.0, "CELO": 0.80, "LINEA": 3100.0, "XRP": 0.55, "SOLANA": 140.0, "BITCOIN": 65000.0, "TRON": 0.12, "STELLAR": 0.11 }
    NEON_URI = os.getenv("NEON_DATABASE_URL", "")
    BITQUERY_API_TOKEN = os.getenv("BITQUERY_API_TOKEN", "")
    BITQUERY_APIV2_TOKEN = os.getenv("BITQUERY_APIV2_TOKEN", os.getenv("VITE_BITQUERY_APIV2_TOKEN", ""))
    CLOUDFLARE_ACCOUNT_ID = os.getenv("CLOUDFLARE_ACCOUNT_ID", "")
    CLOUDFLARE_API_TOKEN = os.getenv("CLOUDFLARE_API_TOKEN", "")

class OmniRotator:
    def __init__(self): self.counters = defaultdict(int)
    def get_explorer_key(self, chain):
        keys = [k for k in Config.EXPLORER_KEYS.get(chain, []) if k]
        if not keys: return ""
        idx = self.counters[f"explorer_{chain}"] % len(keys)
        self.counters[f"explorer_{chain}"] += 1
        return keys[idx]
    def get_service_key(self, service_name):
        keys = getattr(Config, f"{service_name.upper()}_KEYS", [])
        if not keys: return ""
        idx = self.counters[f"service_{service_name}"] % len(keys)
        self.counters[f"service_{service_name}"] += 1
        return keys[idx]

ROTATOR = OmniRotator()
WS_CLIENTS = set()

def detect_chain(val: str, override: str = "AUTO"):
    if override != "AUTO": return override.upper()
    val = val.strip()
    if val.startswith("kaspa:") or (len(val) == 64 and not val.startswith("0x")): return "KASPA"
    elif val.startswith("r") and 25 <= len(val) <= 35: return "XRP" 
    elif val.startswith("G") and len(val) == 56: return "STELLAR"
    elif len(val) >= 32 and len(val) <= 44 and not val.startswith("0x") and not val.startswith("bc1") and not val.startswith("T"): return "SOLANA" 
    elif val.startswith("0x"): return "ETHEREUM"
    elif val.startswith("T") and len(val) == 34: return "TRON"
    elif val.startswith("1") or val.startswith("3") or val.startswith("bc1"): return "BITCOIN"
    return "UNKNOWN"

def get_asset_ticker(chain: str) -> str:
    tickers = {"KASPA": "KAS", "BSC": "BNB", "POLYGON": "MATIC", "AVALANCHE": "AVAX", "CELO": "CELO", "XRP": "XRP", "SOLANA": "SOL", "BITCOIN": "BTC", "TRON": "TRX", "STELLAR": "XLM"}
    if chain in ["ETHEREUM", "ARBITRUM", "OPTIMISM", "BASE", "LINEA"]: return "ETH"
    return tickers.get(chain, "ASSET")

# ==============================================================================
# 2. STATE QUEUES & BATCH BROADCASTERS
# ==============================================================================

class SOCState:
    def __init__(self):
        self.visited = set()
        self.state_edges = []
        self.total_landed_asset = 0.0
        self.target_reached = False
        self.target_asset_amount = 0.0
        self.seeds = []
        self.queue = asyncio.Queue()
        self.broadcast_queue = asyncio.Queue() # HIGH PERFORMANCE BUFFER
        self.state_lock = asyncio.Lock()
        self.max_depth = 0
        self.graph_metrics = {}

async def ws_broadcaster(state, ws_list):
    """
    ⚡ HIGH PERFORMANCE BATCH BROADCASATER ⚡
    Pulls edges from the memory queue and blasts them to the frontend in arrays.
    """
    buffer = []
    while not state.target_reached or not state.broadcast_queue.empty():
        try:
            edge = await asyncio.wait_for(state.broadcast_queue.get(), timeout=0.25)
            buffer.append(edge)
            state.broadcast_queue.task_done()
        except asyncio.TimeoutError:
            pass 

        if buffer and (len(buffer) >= 50 or state.broadcast_queue.empty()):
            payload = {"type": "LEDGER_BATCH", "data": buffer}
            for ws in list(ws_list):
                try: await ws.send_json(payload)
                except Exception: ws_list.discard(ws)
            buffer.clear()

# ==============================================================================
# 3. TRACING PROVIDERS (Abridged for spacing, keeps core flow)
# ==============================================================================

async def fetch_chain_logs(session, addr, chain):
    """Simulated DB/API fetch to keep flow intact. Fetching all tx types."""
    chain_upper = chain.upper()
    events = []
    if chain_upper in Config.EVM_DOMAINS:
        domain = Config.EVM_DOMAINS[chain_upper]
        api_key = ROTATOR.get_explorer_key(chain_upper)
        
        # We need normal transactions, ERC20 transfers, and Internal transactions to get full visibility
        actions = ["txlist", "tokentx", "txlistinternal"]
        
        for action in actions:
            url = f"https://{domain}/api?module=account&action={action}&address={addr}&startblock=0&endblock=99999999&page=1&offset=100&sort=desc&apikey={api_key}"
            try:
                async with GLOBAL_API_SEMAPHORE:
                    async with session.get(url, timeout=10) as r:
                        if r.status == 200:
                            data = await r.json()
                            if data.get("status") == "1":
                                for tx in data.get("result", []):
                                    events.append({"event_type": "TRANSFER", "tx": tx})
            except Exception as e:
                logger.error(f"Error fetching {action} for {addr} on {chain}: {e}")
                
    return events

# ==============================================================================
# 4. TRACING LOGIC (GBIO ENGINE INJECTION)
# ==============================================================================

async def process_hop(session, source_entity, target_entity, amt, tx_data, timestamp, depth, chain, origin_seed, event_type, state, ws_list):
    if state.target_reached or amt <= 0.0001: return
    txid = tx_data.get("hash", "")
    
    # 1. GBIO NODE CONSTRUCTION
    try: b_net = BlockchainNetwork(chain.upper())
    except: b_net = BlockchainNetwork.UNKNOWN
    
    source_node = GBIONode(identifier=source_entity, network=b_net)
    target_node = GBIONode(identifier=target_entity, network=b_net)
    
    # 2. EVIDENCE RECORDING
    evidence = EvidenceRecord(
        source_provider="Omni_Trace_Engine",
        transaction_hash=txid,
        raw_payload=tx_data,
        confidence_score=1.0
    )

    ticker = tx_data.get("computed_ticker", get_asset_ticker(chain))
    usd_value = tx_data.get("computed_usd", amt * Config.USD_RATES.get(chain, 1.0))
    
    # 3. GBIO EDGE MAPPING
    action = TransferAction.SENT_TO
    if event_type == "SWAP": action = TransferAction.SWAPPED_TO
    elif event_type == "MINT": action = TransferAction.MINTED
    elif event_type == "BRIDGE": action = TransferAction.BRIDGED_TO
    
    # Let the Engine validate and construct the semantic edge
    gbio_edge = GBIOEngine.construct_edge(
        action=action,
        source=source_node,
        target=target_node,
        asset=ticker,
        amount=amt,
        usd_value=usd_value,
        evidence=evidence,
        timestamp=datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S') if isinstance(timestamp, str) else datetime.now(timezone.utc)
    )

    is_terminal = gbio_edge.is_terminal_hop
    
    if is_terminal:
        async with state.state_lock:
            state.total_landed_asset += usd_value
            if state.total_landed_asset >= state.target_asset_amount: state.target_reached = True
            
        if gbio_edge.action == TransferAction.BRIDGED_TO:
            for cross_chain in Config.EVM_DOMAINS.keys():
                if cross_chain != chain:
                    if f"{cross_chain}_{source_entity}" not in state.visited:
                        state.queue.put_nowait((source_entity, depth + 1, amt, cross_chain, origin_seed))
    else:
        if f"{chain}_{target_entity}" not in state.visited: 
            state.queue.put_nowait((target_entity, depth + 1, amt, chain, origin_seed))
        if f"{chain}_{source_entity}" not in state.visited:
            state.queue.put_nowait((source_entity, depth + 1, amt, chain, origin_seed))

    # Package for frontend
    frontend_edge = {
        "edge_type": gbio_edge.action.value, 
        "timestamp": timestamp, "chain": chain, "ticker": ticker,
        "tx": txid, "from": source_entity, "to": target_entity, "receiver_entity": target_node.entity_class.value, 
        "gbio_class": target_node.entity_class.value, "threat_level": target_node.threat_level.value,
        "amount": amt, "usd_value": usd_value, "is_terminal": is_terminal, 
        "depth": depth, "origin_seed": origin_seed
    }
    
    async with state.state_lock:
        state.state_edges.append(frontend_edge)
        state.max_depth = max(state.max_depth, depth)
        
    state.broadcast_queue.put_nowait(frontend_edge)

async def engine_worker(session, state, ws_list, worker_id=0):
    while not state.target_reached:
        try: item = await asyncio.wait_for(state.queue.get(), timeout=2.0)
        except: continue
        addr, depth, carry_val, chain, origin_seed = item
        
        visited_key = f"{chain}_{addr}"
        async with state.state_lock:
            if visited_key in state.visited or depth > Config.MAX_DEPTH: 
                state.queue.task_done(); continue
            state.visited.add(visited_key)
            
        logger.info(f"[WORKER-{worker_id:02d}] Fetching data for {addr[:8]}... on {chain}.")
        events = await fetch_chain_logs(session, addr, chain)
        
        for ev in events:
            if state.target_reached: break
            tx = ev["tx"]
            to = str(tx.get("to", "")).lower()
            f_addr = str(tx.get("from", "")).lower()
            if not to or (to == addr.lower() and f_addr == addr.lower()): continue
            try:
                decimals = int(tx.get("tokenDecimal", 18))
                amt = float(tx.get("value", "0")) / (10 ** decimals)
            except: amt = 0.0
            if amt <= 0.001: continue
            
            ticker = tx.get("tokenSymbol", get_asset_ticker(chain))
            usd_rate = Config.USD_RATES.get(chain, 1.0)
            if ticker.upper() in ["USDC", "USDT", "DAI", "BUSD", "TETHER USD", "USD COIN"]: usd_rate = 1.0
            elif ticker.upper() == "WETH": usd_rate = Config.USD_RATES.get("ETHEREUM", 3100.0)
            elif ticker.upper() == "WBTC": usd_rate = Config.USD_RATES.get("BITCOIN", 65000.0)
            tx["computed_usd"] = amt * usd_rate
            tx["computed_ticker"] = ticker
            
            try: ts = datetime.fromtimestamp(int(tx.get("timeStamp", 0))).strftime('%Y-%m-%d %H:%M:%S')
            except: ts = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
            
            await process_hop(session, f_addr, to, amt, tx, ts, depth, chain, origin_seed, ev["event_type"], state, ws_list)
            
        state.queue.task_done()

async def run_trace_engine(state, ws_list):
    logger.info(f"[TRACE] Initializing Omni-Directional GBIO Matrix.")
    headers = {'User-Agent': 'Mozilla/5.0'}
    async with aiohttp.ClientSession(headers=headers) as session:
        for seed in state.seeds: 
            detected = detect_chain(seed)
            if detected == "ETHEREUM":
                for cross_chain in Config.EVM_DOMAINS.keys():
                    state.queue.put_nowait((seed, 0, state.target_asset_amount, cross_chain, seed))
            else:
                state.queue.put_nowait((seed, 0, state.target_asset_amount, detected, seed))
            
        workers = [asyncio.create_task(engine_worker(session, state, ws_list, i)) for i in range(Config.CONCURRENCY_LIMIT)]
        broadcaster = asyncio.create_task(ws_broadcaster(state, ws_list))
        
        await state.queue.join()
        await state.broadcast_queue.join()
        
        for w in workers: w.cancel()
        broadcaster.cancel()

        for ws in list(ws_list):
            try: await ws.send_json({"type": "COMPLETE"})
            except: pass

# ==============================================================================
# 5. FASTAPI ROUTES
# ==============================================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 BOOTING NEMESIS COMMANDER")
    yield

app = FastAPI(title="Lionsgate Nemesis Pro", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

class TraceRequest(BaseModel):
    seeds: str
    target_amount: str = "1000"
    chain_override: str = "AUTO"

@app.get("/")
async def serve_landing(): return FileResponse("cloudflare_frontend/index.html")

@app.get("/tracer")
@app.get("/tracer.html")
async def serve_tracer(): return FileResponse("cloudflare_frontend/tracer.html")

@app.get("/nemesis_id")
@app.get("/nemesis_id.html")
async def serve_nemesis_id(): return FileResponse("cloudflare_frontend/nemesis_id.html")

@app.get("/api/dossier/full")
async def get_dossier_full(address: str):
    return {"status": "success", "data": {"profile": {}, "aml": {}, "transactions": {}, "counterparties": {}, "intelligence": {}}}

@app.get("/api/report/generate")
async def generate_full_report(address: str):
    return FileResponse("cloudflare_frontend/report_template.html")

@app.get("/api/export/package")
async def export_legal_package(address: str):
    return JSONResponse({"status": "error", "message": "Legal export requires Tier-1 clearance."})

# --- NEMESIS AI ENDPOINTS ---
@app.get("/nemesis_ai")
async def serve_nemesis_ai(): return FileResponse("cloudflare_frontend/nemesis_ai.html")

@app.get("/api/ai/ingest_status")
async def get_ingest_status():
    try:
        return JSONResponse(ingest_engine.get_status())
    except:
        return JSONResponse({"status": "OFFLINE"})

@app.post("/api/ai/chat")
async def ai_chat(request: Request):
    data = await request.json()
    msg = data.get("message", "")
    session = data.get("session_id", "default_session")
    try:
        reply = nemesis_ai_engine.chat(session, msg)
        return JSONResponse({"reply": reply})
    except Exception as e:
        return JSONResponse({"reply": f"AI Engine Error: {e}"})

@app.post("/api/generate_narrative")
async def generate_narrative(req: dict):
    return {"narrative": "Stolen funds landed at CEX endpoints."}

@app.get("/api/node/ai")
async def node_ai(address: str):
    return {"status": "success", "data": {}}

@app.websocket("/api/ws/trace")
async def ws_trace(websocket: WebSocket):
    await websocket.accept()
    WS_CLIENTS.add(websocket)
    try:
        while True: 
            text = await websocket.receive_text()
            try:
                data = json.loads(text)
                if data.get("type") in ["START_TRACE", "START"]:
                    state = SOCState()
                    raw_seeds = data.get("seeds", [])
                    actual_seeds = []
                    
                    import re
                    for s in raw_seeds:
                        for tok in re.split(r'[\s,\"]+', s):
                            tok = tok.strip()
                            if tok and tok not in actual_seeds:
                                actual_seeds.append(tok)
                                    
                    state.seeds = actual_seeds
                    if not state.seeds: continue
                    try: state.target_asset_amount = float(data.get("target_amount", 1000))
                    except: state.target_asset_amount = 1000.0
                    
                    chain = detect_chain(state.seeds[0], data.get("network", "AUTO"))
                    ticker = get_asset_ticker(chain)
                    init_msg = {"type": "INIT", "target_amount": state.target_asset_amount, "seeds": state.seeds, "ticker": ticker, "usd_value": state.target_asset_amount}
                    
                    ws_set = {websocket}
                    try: await websocket.send_json(init_msg)
                    except: pass
                    
                    asyncio.create_task(run_trace_engine(state, ws_set))
            except Exception as e:
                logger.error(f"WS error processing message: {e}")
    except: WS_CLIENTS.discard(websocket)

if __name__ == "__main__":
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=False)