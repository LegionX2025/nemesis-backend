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
from collections import defaultdict
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, Request, BackgroundTasks, WebSocketDisconnect, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse, HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# --- GBIO ONTOLOGY INJECTION ---
try:
    from services.gbio_ontology import (
        GBIOEngine, GBIONode, GBIOEdge, TransferAction, EntityClass, 
        BlockchainNetwork, ThreatLevel, EvidenceRecord, RiskProfile, 
        BehavioralIndicator, AMLFlag, GBIONormalizer
    )
except ImportError:
    from gbio_ontology import (
        GBIOEngine, GBIONode, GBIOEdge, TransferAction, EntityClass, 
        BlockchainNetwork, ThreatLevel, EvidenceRecord, RiskProfile, 
        BehavioralIndicator, AMLFlag, GBIONormalizer
    )

# --- MICROSERVICE IMPORTS (NO MOCKS) ---
from intelligence_pipeline import IntelligencePipeline
from heuristics_engine import HeuristicEngine
from transfer_analyzer import TransferAnalyzer, TransferType
from universal_decoder import UniversalDecoder
from entity_attribution import AttributionEngine
from graph_intelligence import GraphIntelligence
from osint_orchestrator import aggregate_osint
from ml_clustering import run_syndicate_clustering

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

GLOBAL_API_SEMAPHORE = asyncio.Semaphore(15)

# ==============================================================================
# 1. CONFIGURATION & STATE MATRIX
# ==============================================================================
load_dotenv()

class Config:
    _depth_str = os.getenv("TRACE_MAX_DEPTH", "15")
    MAX_DEPTH = 9999 if _depth_str.upper() == "UNLIMITED" else int(_depth_str) if _depth_str.isdigit() else 15
    CONCURRENCY_LIMIT = 50 
    
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
    
    EVM_DOMAINS = {
        "ETHEREUM": "api.etherscan.io", "BSC": "api.bscscan.com", "POLYGON": "api.polygonscan.com", 
        "BASE": "api.basescan.org", "ARBITRUM": "api.arbiscan.io", "AVALANCHE": "api.snowtrace.io",
        "OPTIMISM": "api-optimistic.etherscan.io", "CELO": "api.celoscan.io", "LINEA": "api.lineascan.build",
        "ZKSYNC": "api.zksync.io"
    }
    USD_RATES = { "KASPA": 0.036, "ETHEREUM": 3100.0, "BSC": 580.0, "POLYGON": 0.65, "AVALANCHE": 35.0, "ARBITRUM": 3100.0, "BASE": 3100.0, "CELO": 0.80, "LINEA": 3100.0, "XRP": 0.55, "SOLANA": 140.0, "BITCOIN": 65000.0, "TRON": 0.12, "STELLAR": 0.11 }

class OmniRotator:
    def __init__(self): self.counters = defaultdict(int)
    def get_explorer_key(self, chain):
        keys = [k for k in Config.EXPLORER_KEYS.get(chain, []) if k]
        if not keys: return ""
        idx = self.counters[f"explorer_{chain}"] % len(keys)
        self.counters[f"explorer_{chain}"] += 1
        return keys[idx]

ROTATOR = OmniRotator()
WS_CLIENTS = set()

def detect_input_type(val: str):
    val = val.strip()
    if val.startswith("0x") and len(val) == 66: return "EVM_TX_HASH"
    elif val.startswith("0x") and len(val) == 42: return "EVM_ADDRESS"
    elif val.startswith("1") or val.startswith("3") or val.startswith("bc1"): return "BTC_ADDRESS"
    elif len(val) >= 32 and len(val) <= 44 and not val.startswith("T"): return "SOL_ADDRESS"
    elif val.startswith("T") and len(val) == 34: return "TRON_ADDRESS"
    return "UNKNOWN"

def detect_chain(val: str, override: str = "AUTO"):
    if override != "AUTO": return override.upper()
    itype = detect_input_type(val)
    if itype in ["EVM_TX_HASH", "EVM_ADDRESS"]: return "ETHEREUM"
    elif itype == "BTC_ADDRESS": return "BITCOIN"
    elif itype == "SOL_ADDRESS": return "SOLANA"
    elif itype == "TRON_ADDRESS": return "TRON"
    return "UNKNOWN"

def get_asset_ticker(chain: str) -> str:
    tickers = {"KASPA": "KAS", "BSC": "BNB", "POLYGON": "MATIC", "AVALANCHE": "AVAX", "CELO": "CELO", "XRP": "XRP", "SOLANA": "SOL", "BITCOIN": "BTC", "TRON": "TRX"}
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
        self.target_asset_amount = float('inf') # Defaults to Infinity exhaustive tracing
        self.seeds = []
        self.tx_seeds = []
        self.queue = asyncio.Queue()
        self.broadcast_queue = asyncio.Queue() 
        self.state_lock = asyncio.Lock()
        self.max_depth = 0
        self.graph_metrics = {}

async def ws_broadcaster(state, ws_list):
    """⚡ HIGH PERFORMANCE BATCH BROADCASATER ⚡"""
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
# 3. TRACING PROVIDERS (INCLUDING TX HASH RESOLVER AND NFT EXTRACTORS)
# ==============================================================================

async def resolve_evm_tx(session, tx_hash, chain):
    """Resolves an EVM Transaction Hash to origin endpoints and value."""
    api_key = ROTATOR.get_explorer_key(chain)
    chain_id_map = { "ETHEREUM": 1, "BSC": 56, "POLYGON": 137, "BASE": 8453, "ARBITRUM": 42161, "AVALANCHE": 43114, "OPTIMISM": 10, "LINEA": 59144, "ZKSYNC": 324 }
    chain_id = chain_id_map.get(chain.upper(), 1)
    url = f"https://api.etherscan.io/v2/api?chainid={chain_id}&module=proxy&action=eth_getTransactionByHash&txhash={tx_hash}&apikey={api_key}"
    try:
        async with session.get(url, timeout=10) as r:
            data = await r.json()
            tx = data.get("result")
            if tx and tx.get("from"):
                val = int(tx.get("value", "0"), 16) / 1e18
                return {
                    "hash": tx_hash,
                    "from": tx.get("from", ""),
                    "to": tx.get("to", ""),
                    "value": val,
                    "tokenSymbol": get_asset_ticker(chain),
                    "timeStamp": int(datetime.now().timestamp()),
                    "is_tx": True
                }
    except Exception as e:
        logger.warning(f"Could not resolve TX Hash {tx_hash} on {chain}: {e}")
    return None

async def fetch_chain_logs(session, addr, chain):
    """
    Advanced Omni-Fetcher: Collects internal, native, ERC20, ERC721 (NFT), and ERC1155 events.
    """
    chain_upper = chain.upper()
    events = []
    
    if chain_upper in Config.EVM_DOMAINS:
        api_key = ROTATOR.get_explorer_key(chain_upper)
        chain_id_map = { "ETHEREUM": 1, "BSC": 56, "POLYGON": 137, "BASE": 8453, "ARBITRUM": 42161, "AVALANCHE": 43114, "OPTIMISM": 10, "CELO": 42220, "LINEA": 59144, "ZKSYNC": 324 }
        chain_id = chain_id_map.get(chain_upper, 1)
        
        # Comprehensive Transfer Acquisition
        actions = ["txlist", "txlistinternal", "tokentx", "tokennfttx", "token1155tx"]
        
        async def fetch_action(action):
            url = f"https://api.etherscan.io/v2/api?chainid={chain_id}&module=account&action={action}&address={addr}&startblock=0&endblock=99999999&page=1&offset=100&sort=desc&apikey={api_key}"
            try:
                async with GLOBAL_API_SEMAPHORE:
                    async with session.get(url, timeout=10) as r:
                        if r.status == 200:
                            data = await r.json()
                            if data.get("status") == "1":
                                txs = data.get("result", [])
                                action_events = []
                                for tx in txs:
                                    if action in ["tokennfttx", "token1155tx"]:
                                        action_events.append({"event_type": "TRANSFERRED_NFT", "tx": tx})
                                    elif action == "txlistinternal":
                                        action_events.append({"event_type": "INTERNAL_TRANSFER", "tx": tx})
                                    elif not tx.get("to"): 
                                        action_events.append({"event_type": "MINT", "tx": tx})
                                    else: 
                                        action_events.append({"event_type": "TRANSFER", "tx": tx})
                                return action_events
            except Exception as e:
                logger.error(f"[!] Explorer Fetch Failed ({action}) on {chain_upper}: {e}")
            return []
            
        tasks = [asyncio.create_task(fetch_action(a)) for a in actions]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for res in results:
            if isinstance(res, list): events.extend(res)
            
    elif chain_upper == "TRON":
        try:
            url = f"https://api.trongrid.io/v1/accounts/{addr}/transactions/trc20?limit=200"
            async with session.get(url, timeout=10) as r:
                if r.status == 200:
                    data = await r.json()
                    for tx in data.get("data", []):
                        events.append({"event_type": "TRANSFER", "tx": {"hash": tx.get("transaction_id"), "from": tx.get("from"), "to": tx.get("to"), "value": float(tx.get("value", 0)), "timeStamp": int(tx.get("block_timestamp", 0))/1000}})
        except: pass
        
    elif chain_upper == "SOLANA":
        try:
            url = f"https://api.mainnet-beta.solana.com"
            payload = {"jsonrpc":"2.0","id":1, "method":"getSignaturesForAddress", "params":[addr, {"limit":100}]}
            async with session.post(url, json=payload, timeout=10) as r:
                if r.status == 200:
                    data = await r.json()
                    for sig in data.get("result", []):
                         events.append({"event_type": "TRANSFER", "tx": {"hash": sig.get("signature"), "from": addr, "to": "UNKNOWN_SOL", "value": 0, "timeStamp": sig.get("blockTime")}})
        except: pass
        
    return events

# ==============================================================================
# 4. TRACING LOGIC (GBIO ENGINE INJECTION)
# ==============================================================================

async def process_hop(session, source_entity, target_entity, amt, tx_data, timestamp, depth, chain, origin_seed, event_type, state, ws_list):
    if state.target_reached or amt <= 0.0000001: return
    txid = tx_data.get("hash", "")
    
    # GBIO NODE CONSTRUCTION
    try: b_net = BlockchainNetwork(chain.upper())
    except: b_net = BlockchainNetwork.UNKNOWN
    source_node = GBIONode(identifier=source_entity, network=b_net)
    target_node = GBIONode(identifier=target_entity, network=b_net)
    
    evidence = EvidenceRecord(
        source_provider="Omni_Trace_Engine",
        transaction_hash=txid,
        raw_payload=tx_data,
        confidence_score=1.0
    )

    # Detect NFTs
    if event_type == "TRANSFERRED_NFT":
        ticker = tx_data.get("tokenSymbol", "NFT") + f" #{tx_data.get('tokenID', '')}"
        usd_value = 0.0
        action = TransferAction.TRANSFERRED_NFT
    else:
        ticker = tx_data.get("computed_ticker", get_asset_ticker(chain))
        usd_value = tx_data.get("computed_usd", amt * Config.USD_RATES.get(chain, 1.0))
        
        action = TransferAction.SENT_TO
        if event_type == "INTERNAL_TRANSFER": action = TransferAction.INTERNAL_TRANSFER
        elif event_type == "SWAP": action = TransferAction.SWAPPED_TO
        elif event_type == "MINT": action = TransferAction.MINTED
        elif event_type == "BRIDGE": action = TransferAction.BRIDGED_TO
    
    heuristic_data = HeuristicEngine.enrich_hop_metadata(target_entity, chain, amt, txs=None)
    if heuristic_data["entity_type"] == "EXCHANGE": target_node.entity_class = EntityClass.EXCHANGE_DEPOSIT
    elif heuristic_data["entity_type"] == "MIXER": target_node.entity_class = EntityClass.MIXER_ROUTER
    elif heuristic_data["entity_type"] == "BRIDGE": target_node.entity_class = EntityClass.BRIDGE_ENDPOINT

    # GBIO Construct
    gbio_edge = GBIOEngine.construct_edge(
        action=action,
        source=source_node,
        target=target_node,
        asset=ticker,
        amount=amt,
        usd_value=usd_value,
        evidence=evidence,
        timestamp=datetime.fromtimestamp(int(timestamp)) if isinstance(timestamp, (int, float)) else datetime.now(timezone.utc)
    )

    is_terminal = gbio_edge.is_terminal_hop
    
    if is_terminal:
        async with state.state_lock:
            state.total_landed_asset += usd_value
            # Infinite tracing bypasses the target_reached flag
            if state.total_landed_asset >= state.target_asset_amount: state.target_reached = True
            
        if gbio_edge.action == TransferAction.BRIDGED_TO:
            for cross_chain in Config.EVM_DOMAINS.keys():
                if cross_chain != chain:
                    if f"{cross_chain}_{source_entity}" not in state.visited:
                        state.queue.put_nowait((source_entity, depth + 1, amt, cross_chain, origin_seed))
    else:
        if f"{chain}_{target_entity}" not in state.visited: 
            state.queue.put_nowait((target_entity, depth + 1, amt, chain, origin_seed))

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
            
        logger.info(f"[WORKER-{worker_id:02d}] [DEPTH {depth}/{Config.MAX_DEPTH}] Mining {addr[:8]}... on {chain}.")
        events = await fetch_chain_logs(session, addr, chain)
        
        for ev in events:
            if state.target_reached: break
            tx = ev["tx"]
            action_type = ev.get("event_type", "TRANSFER")
            
            to = str(tx.get("to", "")).lower()
            f_addr = str(tx.get("from", "")).lower()
            if not to or (to == addr.lower() and f_addr == addr.lower()): continue
            
            # NFT Parsing vs Standard Float
            if action_type == "TRANSFERRED_NFT":
                amt = 1.0
            else:
                try:
                    decimals = int(tx.get("tokenDecimal", 18))
                    amt = float(tx.get("value", "0")) / (10 ** decimals)
                except: amt = 0.0
                
            if amt <= 0.0000001: continue
            
            ticker = tx.get("tokenSymbol", get_asset_ticker(chain))
            usd_rate = Config.USD_RATES.get(chain, 1.0)
            if ticker.upper() in ["USDC", "USDT", "DAI", "BUSD"]: usd_rate = 1.0
            elif ticker.upper() == "WETH": usd_rate = Config.USD_RATES.get("ETHEREUM", 3100.0)
            elif ticker.upper() == "WBTC": usd_rate = Config.USD_RATES.get("BITCOIN", 65000.0)
            tx["computed_usd"] = amt * usd_rate
            tx["computed_ticker"] = ticker
            
            ts = tx.get("timeStamp", 0)
            
            await process_hop(session, f_addr, to, amt, tx, ts, depth, chain, origin_seed, action_type, state, ws_list)
            
        state.queue.task_done()

async def run_trace_engine(state, ws_list):
    logger.info(f"[TRACE] Initializing Omni-Directional GBIO Matrix.")
    headers = {'User-Agent': 'Mozilla/5.0'}
    async with aiohttp.ClientSession(headers=headers) as session:
        
        # RESOLVE TRANSACTION SEEDS FIRST
        for tx_hash in state.tx_seeds:
            logger.info(f"[TRACE] Resolving Origin Seed TX: {tx_hash}")
            target_chain = "ETHEREUM" # Assume Ethereum first, fallback logic later
            chains_to_try = list(Config.EVM_DOMAINS.keys())
            
            for c in chains_to_try:
                resolved = await resolve_evm_tx(session, tx_hash, c)
                if resolved and resolved.get("to"):
                    usd_val = resolved["value"] * Config.USD_RATES.get(c, 3000)
                    
                    # Auto-compute target amount if unset (infinity)
                    if state.target_asset_amount == float('inf') or state.target_asset_amount == 1000.0:
                        state.target_asset_amount = usd_val * 1.5 # Padding
                        
                    await process_hop(session, resolved["from"], resolved["to"], resolved["value"], resolved, resolved["timeStamp"], 0, c, tx_hash, "TRANSFER", state, ws_list)
                    
                    # Propagate both directions
                    state.queue.put_nowait((resolved["to"], 1, resolved["value"], c, tx_hash))
                    state.queue.put_nowait((resolved["from"], 1, resolved["value"], c, tx_hash))
                    break
        
        # RESOLVE WALLET SEEDS
        for seed in state.address_seeds: 
            detected = detect_chain(seed)
            if detected == "ETHEREUM":
                # EVM: Blanket broadcast across all networks to find cross-chain assets instantly
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

@app.get("/")
async def serve_landing(): return FileResponse("landing.html")

@app.get("/tracer")
@app.get("/tracer.html")
async def serve_tracer(): return FileResponse("tracer.html")

@app.get("/nemesis_id")
@app.get("/nemesis_id.html")
async def serve_nemesis_id(): return FileResponse("nemesis_id.html")

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
                    
                    state.address_seeds = []
                    state.tx_seeds = []
                    
                    import re
                    for s in raw_seeds:
                        for tok in re.split(r'[\s,\"]+', s):
                            tok = tok.strip()
                            if not tok: continue
                            
                            itype = detect_input_type(tok)
                            if itype == "EVM_TX_HASH":
                                if tok not in state.tx_seeds: state.tx_seeds.append(tok)
                            elif "ADDRESS" in itype:
                                if tok not in state.address_seeds: state.address_seeds.append(tok)
                                    
                    state.seeds = state.address_seeds + state.tx_seeds
                    if not state.seeds: continue
                    
                    # Target Loss Auto-Computation Parameter
                    try: 
                        amt_str = str(data.get("target_amount", "")).strip()
                        if amt_str and amt_str != "0":
                            state.target_asset_amount = float(amt_str)
                        else:
                            state.target_asset_amount = float('inf') # Infinite Mode Active
                    except: 
                        state.target_asset_amount = float('inf')
                    
                    chain = detect_chain(state.seeds[0], data.get("network", "AUTO"))
                    ticker = get_asset_ticker(chain)
                    init_msg = {"type": "INIT", "target_amount": state.target_asset_amount if state.target_asset_amount != float('inf') else "AUTO_COMPUTE", "seeds": state.seeds, "ticker": ticker, "usd_value": 0}
                    
                    ws_set = {websocket}
                    try: await websocket.send_json(init_msg)
                    except: pass
                    
                    asyncio.create_task(run_trace_engine(state, ws_set))
            except Exception as e:
                logger.error(f"WS error processing message: {e}")
    except: WS_CLIENTS.discard(websocket)

if __name__ == "__main__":
    uvicorn.run("nemesis_corev2:app", host="127.0.0.1", port=8000, reload=False)