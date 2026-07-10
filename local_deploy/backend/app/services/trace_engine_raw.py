import os\nimport asyncio\nimport json\nimport csv\nimport time\nfrom datetime import datetime, timezone\nfrom collections import defaultdict\nimport certifi\nimport aiohttp\nimport logging\nfrom motor.motor_asyncio import AsyncIOMotorClient\nlogger = logging.getLogger('TraceEngine')\n\nimport certifi
import socket
import asyncio
import csv
import json
import traceback
import threading
import aiohttp
import logging
from concurrent.futures import ThreadPoolExecutor

# Configure enterprise logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("OmniChainEngine")
from datetime import datetime, timedelta, timezone
from collections import defaultdict
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn
from motor.motor_asyncio import AsyncIOMotorClient
import time

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

# Runtime healthcheck removed for production grade. Ensure dependencies are installed via requirements.txt

import pandas as pd
import numpy as np
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler

# ==============================================================================
# 🔬 LIONSGATE FORENSIC ENGINE - NEMESIS OMNI-CHAIN (EVIDENTIARY EDITION)
# ==============================================================================

MAX_DEPTH = 99999 
CONCURRENCY_LIMIT = 20 # Reduced for Etherscan rate limits
CSV_FILE = "LFR_OmniChain_Trace.csv"
JSON_FILE = "LFR_OmniChain_Trace.json"

FILE_WRITE_LOCK = threading.Lock()
IO_POOL = ThreadPoolExecutor(max_workers=20)

CONFIG = {
    "ETHERSCAN_API_KEY": os.getenv("ETHERSCAN_API_KEY", "AYQRQWFDJRK8WAX2ICJ8U4JUSYXZT5J7II"),
    "POLYGONSCAN_API_KEY": os.getenv("POLYGONSCAN_API_KEY", "YUXEUN58W2X5YYQZ3R8M33XN626B5X6JQA"),
    "GEMINI_API_KEY": os.getenv("GEMINI_API_KEY", ""),
    "MONGO_URI": os.getenv("MONGO_URI", ""),
    "TOKENVIEW_API_KEY": os.getenv("TOKENVIEW_API_KEY", "Rhl2uJqCsPkNaog2oL4q"),
    "OKLINK_API_KEY": os.getenv("OKLINK_API_KEY", "")
}

EVM_DOMAINS = {
    "ETHEREUM": "api.etherscan.io", "BSC": "api.bscscan.com",
    "POLYGON": "api.polygonscan.com", "BASE": "api.basescan.org"
}

USD_RATES = {
    "ETHEREUM": 3100.00, "BITCOIN": 65000.00, "TRON": 0.12, "POLYGON": 0.70, "BSC": 580.0
}

KNOWN_ENTITIES = {
    "bc1qm341sc65zpw791xes69zkqmk6ee3ewf0j77s3h": "Binance Deposit",
    "0x28c6c06298d514db089934071355e5743bf21d60": "Binance 14 (Cold)",
    "0xd90e2f925da726b50c4ed8d0fb90ad053324f31b": "Tornado Cash Router",
    "tx4s14f3p8vj9yyw1r7fuvz7v6m7g9r5v4": "Binance TRON Hot Wallet"
}

SIGNATURE_REGISTRY = {
    "a9059cbb": "Transfer", "23b872dd": "TransferFrom", "095ea7b3": "Approve",
    "38ed1739": "SwapExactTokensForTokens (DEX)", "18cbafe5": "SwapExactTokensForETH (DEX)",
    "7ff36ab5": "SwapExactETHForTokens (DEX)", "5c11d795": "SwapTokensSupportingFee (DEX)",
    "3d12a85a": "DepositFor (Bridge)", "a3bc6e0e": "BridgeIn", "8b9e4f93": "BridgeOut",
    "b6b55f25": "Deposit (Mixer)", "21a0adb6": "Withdraw (Mixer)", "e3ceb028": "Transact (Railgun)",
    "e523f4f1": "CEX Hot Wallet Sweep"
}

mongo_client = None
mongo_db = None

async def init_mongodb():
    global mongo_client, mongo_db
    if not CONFIG["MONGO_URI"]: return
    try:
        mongo_client = AsyncIOMotorClient(CONFIG["MONGO_URI"], serverSelectionTimeoutMS=5000, tlsCAFile=certifi.where())
        mongo_db = mongo_client["blockchain"]
        await mongo_client.admin.command('ping')
        print("      ✅ [MONGO DB] Connected to Lionsgate Graph Database successfully.", flush=True)
    except:
        mongo_db = None

def detect_chain(val: str, override: str = "AUTO") -> str:
    if override and override != "AUTO": return override.upper()
    val = val.strip()
    if val.startswith("bc1") or val.startswith("1") or val.startswith("3"): return "BITCOIN"
    elif val.startswith("T") and len(val) == 34: return "TRON"
    elif val.startswith("0x"): return "EVM_AUTO"
    return "ETHEREUM"

import re

async def fetch_oklink_label(session, chain: str, address: str) -> str:
    cmap = {"BTC": "btc", "ETH": "eth", "POLYGON": "polygon", "BSC": "bsc", "TRX": "trx", "TRON": "trx"}
    cname = cmap.get(chain.upper())
    if not cname: return None
    url = f"https://www.oklink.com/{cname}/address/{address}"
    try:
        async with session.get(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"}, timeout=4.0) as resp:
            if resp.status == 200:
                html = await resp.text()
                match = re.search(r'class="[^"]*text-ellipsis[^"]*"[^>]*>([\s\S]*?)<\/', html, re.IGNORECASE)
                if match:
                    raw_text = match.group(1)
                    clean_text = re.sub(r'<!--.*?-->', '', raw_text)
                    clean_text = re.sub(r'<[^>]+>', '', clean_text)
                    label = clean_text.replace('#', '').strip()
                    if label and len(label) > 2 and "0x" not in label and not label.lower().startswith("bc1") and label.lower() != "address": return label
                match_json = re.search(r'"entityName"\s*:\s*"([^"]+)"', html)
                if match_json: return match_json.group(1)
                match_tag = re.search(r'"addressTag"\s*:\s*"([^"]+)"', html)
                if match_tag: return match_tag.group(1)
    except: pass
    return None

async def fetch_wallet_label(session, addr, chain):
    addr_lower = addr.lower()
    if addr_lower in KNOWN_ENTITIES:
        return KNOWN_ENTITIES[addr_lower]
        
    label = "Unknown Wallet"
    if chain == "TRON":
        try:
            async with session.get(f"https://apilist.tronscan.org/api/accountv2?address={addr}", timeout=5) as r:
                if r.status == 200:
                    d = await r.json()
                    if d.get("name"): label = d["name"]
                    elif d.get("project", {}).get("name"): label = d["project"]["name"]
        except: pass
    elif CONFIG["OKLINK_API_KEY"]:
        try:
            headers = {"Ok-Access-Key": CONFIG["OKLINK_API_KEY"]}
            chain_short = "eth" if chain == "ETHEREUM" else "bsc" if chain == "BSC" else "btc" if chain == "BITCOIN" else "trx"
            url = f"https://www.oklink.com/api/v5/explorer/address/address-summary?chainShortName={chain_short}&address={addr}"
            async with session.get(url, headers=headers, timeout=5) as r:
                if r.status == 200:
                    d = await r.json()
                    tags = d.get("data", [{}])[0].get("contractName") or d.get("data", [{}])[0].get("labelName")
                    if tags: label = tags
        except: pass

    if label == "Unknown Wallet":
        oklink_tag = await fetch_oklink_label(session, chain, addr)
        if oklink_tag: label = oklink_tag

    KNOWN_ENTITIES[addr_lower] = label
    return label

def thread_safe_file_write(ledger_data):
    unified_data = []
    for row in ledger_data:
        unified_data.append({
            "Date/Time (UTC)": row.get("timestamp"),
            "TX Hash": row.get("tx"),
            "From Wallet": row.get("from"),
            "To Wallet": row.get("to"),
            "Receiver Entity": row.get("receiver_entity"),
            "Amount": f"{row.get('amount', 0):.4f} {row.get('ticker', '')}",
            "Transaction Type": f"{row.get('intent_action', '')} / {row.get('edge_type', '')}",
            "Behavioral Cluster": row.get("cluster"),
            "Confidence": row.get("confidence")
        })

    with FILE_WRITE_LOCK:
        try:
            with open(JSON_FILE, "w", encoding="utf-8") as f: 
                json.dump(unified_data, f, indent=4)
            with open(CSV_FILE, "w", newline="", encoding="utf-8") as f: 
                writer = csv.DictWriter(f, fieldnames=["Date/Time (UTC)", "TX Hash", "From Wallet", "To Wallet", "Receiver Entity", "Amount", "Transaction Type", "Behavioral Cluster", "Confidence"])
                writer.writeheader()
                writer.writerows(unified_data)
        except Exception as e:
            logger.error(f"File write failed: {e}")

async def classify_tx_intent(tx: dict) -> dict:
    input_data = tx.get("input", "")
    method = input_data[:10].lower().replace("0x", "") if input_data else ""
    intent = {"action": "TOKEN_TRANSFER", "edge_type": "TRANSFER", "obf_path": "NONE"}
    if not input_data or input_data == "0x" or len(input_data) < 8: return intent

    if method in SIGNATURE_REGISTRY:
        sig_val = SIGNATURE_REGISTRY[method]
        intent["action"] = sig_val
        if "DEX" in sig_val: intent["edge_type"] = "SWAP"; intent["obf_path"] = "DEX_ROUTING"
        elif "Bridge" in sig_val: intent["edge_type"] = "BRIDGE_HOP"; intent["obf_path"] = "BRIDGE"
        elif "Mixer" in sig_val or "Railgun" in sig_val: intent["edge_type"] = "MIXER"; intent["obf_path"] = "MIXER"
        elif "Sweep" in sig_val: intent["edge_type"] = "CEX_SWEEP"; intent["obf_path"] = "CUSTODIAL_SETTLEMENT"
    return intent

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
        if address in self.address_to_cluster: return self.address_to_cluster[address]
        new_cid = f"SYS-ACTOR-{self.cluster_id_counter:03d}"
        self.address_to_cluster[address] = new_cid
        self.cluster_id_counter += 1
        return new_cid

class CEX:
    def __init__(self):
        self.cex_keywords = ["MEXC", "BINANCE", "KRAKEN", "OKX", "COINBASE", "KUCOIN", "HOT WALLET", "HUOBI"]
        self.mixer_keywords = ["MIXER", "TORNADO CASH", "RAILGUN"]
        self.bridge_keywords = ["BRIDGE", "STARGATE", "MULTICHAIN"]
    
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
        self.seeds = []
        self.seed_chains = {}
        self.target_asset_amount = 0.0
        self.queue = asyncio.Queue()
        self.state_lock = asyncio.Lock()
        self.inbound_sources = defaultdict(set)
        self.node_stats = defaultdict(lambda: {"in_count":0, "out_count":0, "in_amt":0.0, "out_amt":0.0})
        self.start_date = ""
        self.end_date = ""
        
    def setup(self, seeds, target_amount, default_chain="AUTO", start_date="", end_date=""):
        self.seeds = seeds; self.target_asset_amount = target_amount
        self.start_date = start_date; self.end_date = end_date
        for seed in seeds:
            chain = detect_chain(seed, default_chain)
            self.seed_chains[seed] = chain
            self.queue.put_nowait((seed, 0, target_amount, "NONE", chain, seed)) 

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_mongodb()
    yield


app.mount("/static", StaticFiles(directory="."), name="static")




def get_asset_ticker(chain: str) -> str:
    if chain == "BITCOIN": return "BTC"
    elif chain == "TRON": return "TRX"
    elif chain == "POLYGON": return "MATIC"
    return "ETH"

async def fetch_txs(session, addr, chain):
    headers = {"User-Agent": "Mozilla/5.0"}
    


    if chain == "BITCOIN":
        for attempt in range(4):
            try:
                async with session.get(f"https://mempool.space/api/address/{addr}/txs", headers=headers, timeout=12) as r:
                    if r.status == 200: return {"type": "btc", "data": await r.json(), "actual_chain": "BITCOIN"}
                    elif r.status == 429: await asyncio.sleep(2 ** attempt)
                    else:
                        async with session.get(f"https://blockstream.info/api/address/{addr}/txs", headers=headers, timeout=12) as r2:
                             if r2.status == 200: return {"type": "btc", "data": await r2.json(), "actual_chain": "BITCOIN"}
                             else: await asyncio.sleep(2)
            except: await asyncio.sleep(2)
        return {"type": "btc", "data": [], "actual_chain": "BITCOIN"}
        
    elif chain == "TRON":
        all_txs = []
        try:
            async with session.get(f"https://apilist.tronscan.org/api/transaction", params={"address": addr, "limit": 100, "sort": "-timestamp"}, headers=headers, timeout=12) as r:
                if r.status == 200:
                    d = await r.json()
                    all_txs.extend(d.get("data", []))
        except: pass
        try:
            url = f"https://usdt.tokenview.io/api/usdt/addresstxlist/{addr}/1/50?apikey={CONFIG['TOKENVIEW_API_KEY']}"
            async with session.get(url, headers=headers, timeout=12) as r:
                if r.status == 200:
                    d = await r.json()
                    if d.get("data"):
                        data_arr = d["data"]
                        if isinstance(data_arr, dict) and "data" in data_arr: all_txs.extend(data_arr["data"])
                        elif isinstance(data_arr, list): all_txs.extend(data_arr)
        except: pass
        return {"type": "tron", "data": all_txs, "actual_chain": "TRON"}
        
    else:
        chains_to_try = [chain] if chain in EVM_DOMAINS else ["ETHEREUM", "POLYGON", "BSC", "BASE"]
        actual_chain = chain
        all_txs = []
        
        for c in chains_to_try:
            domain = EVM_DOMAINS.get(c, "api.etherscan.io")
            api_key = CONFIG.get(f"{c}SCAN_API_KEY", CONFIG["ETHERSCAN_API_KEY"])
            url_native = f"https://{domain}/api?module=account&action=txlist&address={addr}&startblock=0&endblock=99999999&page=1&offset=200&sort=desc&apikey={api_key}"
            url_token = f"https://{domain}/api?module=account&action=tokentxns&address={addr}&startblock=0&endblock=99999999&page=1&offset=200&sort=desc&apikey={api_key}"
            
            for url in [url_native, url_token]:
                for attempt in range(4):
                    try:
                        async with session.get(url, headers=headers, timeout=10) as r:
                            if r.status == 200:
                                data = await r.json()
                                if data.get("status") == "1":
                                    all_txs.extend(data.get("result", []))
                                    break
                                elif data.get("message") == "NOTOK" and "rate limit" in str(data.get("result", "")).lower():
                                    await asyncio.sleep(1 + attempt) 
                                    continue
                                else:
                                    break # Fast fail on 'No transactions found' or 'Invalid API Key'
                    except: await asyncio.sleep(1)
                    
            if all_txs:
                actual_chain = c
                break
                
        return {"type": "evm", "data": all_txs, "actual_chain": actual_chain}

async def process_bitcoin_txs(session, addr, txs, depth, carry_val, obf_path, chain, origin_seed):
    for tx in txs:
        txid = tx.get("txid", "Unknown")
        ts = tx.get("status", {}).get("block_time", 0)
        timestamp = datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S') if ts else datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
        
        inputs = [i.get("prevout", {}).get("scriptpubkey_address") for i in tx.get("vin", []) if i.get("prevout", {}).get("scriptpubkey_address")]
        state.clustering.cluster_inputs(inputs)
        
        if state.start_date and timestamp[:10] < state.start_date: continue
        if state.end_date and timestamp[:10] > state.end_date: continue

        is_sender = any(i.get("prevout", {}).get("scriptpubkey_address") == addr for i in tx.get("vin", []))
        if is_sender:
            for o in tx.get("vout", []):
                to = o.get("scriptpubkey_address")
                if not to or to == addr: continue
                amt = int(o.get("value", 0)) / 1e8
                if amt < 0.000001: continue
                
                intent_data = {"action": "NATIVE_TRANSFER", "edge_type": "UTXO_TRANSFER", "obf_path": obf_path}
                await process_hop(session, addr, to, amt, txid, timestamp, depth, chain, origin_seed, intent_data, "BTC")

async def process_tron_txs(session, addr, txs, depth, carry_val, obf_path, chain, origin_seed):
    for tx in txs:
        from_addr = tx.get("ownerAddress") or tx.get("fromAddress") or tx.get("from") or tx.get("sender")
        to = tx.get("toAddress") or tx.get("to") or tx.get("receiver")
        
        if not to or to == addr or from_addr != addr: continue
        
        txid = tx.get("hash") or tx.get("txID") or tx.get("transactionHash") or tx.get("transactionid") or tx.get("txid")
        
        amt = 0.0
        if "amount" in tx and tx.get("amount") is not None:
            try: amt = float(tx.get("amount")) / 1_000_000
            except ValueError: amt = 0.0
        elif "volume" in tx:
            try: amt = float(tx.get("volume"))
            except ValueError: amt = 0.0
            
        if amt <= 0.000001: continue
            
        ts = tx.get("block_timestamp") or tx.get("timestamp") or tx.get("time") or tx.get("rawData", {}).get("timestamp")
        try:
            if isinstance(ts, (int, float)):
                ts_seconds = ts / 1000 if ts > 1e10 else ts
                ts_iso = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(ts_seconds))
            else: ts_iso = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
        except: ts_iso = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
        
        if state.start_date and ts_iso[:10] < state.start_date: continue
        if state.end_date and ts_iso[:10] > state.end_date: continue

        ticker = "USDT" if "volume" in tx else "TRX"
        intent_data = {"action": "TRON_TRANSFER", "edge_type": "TRANSFER", "obf_path": "NONE"}
        
        await process_hop(session, addr, to, amt, txid, ts_iso, depth, chain, origin_seed, intent_data, ticker)

async def process_evm_txs(session, addr, txs, depth, carry_val, obf_path, chain, origin_seed):
    for tx in txs:
        txid = tx.get("hash", "Unknown")
        to = str(tx.get("to", "")).lower()
        f_addr = str(tx.get("from", "")).lower()
        addr_lower = addr.lower()
        
        if not to or to == addr_lower or f_addr != addr_lower: continue
        
        intent_data = await classify_tx_intent(tx)
        
        token_sym = tx.get("tokenSymbol", "")
        if token_sym:
            dec = int(tx.get("tokenDecimal", 18))
            try: amt = float(tx.get("value", "0")) / (10**dec)
            except: amt = 0.0
            ticker = token_sym.upper()
        else:
            try: amt = float(tx.get("value", "0")) / 1e18
            except: amt = 0.0
            ticker = get_asset_ticker(chain)
            
        if amt <= 0.000001: continue
        
        try: ts = datetime.fromtimestamp(int(tx.get("timeStamp", 0))).strftime('%Y-%m-%d %H:%M:%S')
        except: ts = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
        
        if state.start_date and ts[:10] < state.start_date: continue
        if state.end_date and ts[:10] > state.end_date: continue

        await process_hop(session, addr, to, amt, txid, ts, depth, chain, origin_seed, intent_data, ticker)

async def process_hop(session, addr, to, amt, txid, timestamp, depth, chain, origin_seed, intent_data, ticker_override=None):
    receiver_entity_lbl = await fetch_wallet_label(session, to, chain)
    sender_entity_lbl = await fetch_wallet_label(session, addr, chain)
    ticker = ticker_override if ticker_override else get_asset_ticker(chain)
    
    print(f"[{chain}] {addr[:8]}... -> {to[:8]}... | {amt:.4f} {ticker} | {receiver_entity_lbl}")
    
    entity_class, score = state.cex.classify(to, receiver_entity_lbl)
    
    async with state.state_lock:
        state.inbound_sources[to].add(addr)
        state.node_stats[addr]["out_count"] += 1
        state.node_stats[addr]["out_amt"] += amt
        state.node_stats[to]["in_count"] += 1
        state.node_stats[to]["in_amt"] += amt
        
        is_consolidation = len(state.inbound_sources[to]) > 1 
        
    cluster_id = state.clustering.assign_cluster(to, f"depth_{depth}_class_{entity_class}") 
    is_terminal = "EXCHANGE" in entity_class or "CUSTODIAL" in entity_class
    
    if is_terminal or "MIXER" in entity_class: confidence_level = "Confirmed On-Chain Fact"
    elif is_consolidation: confidence_level = "High-Confidence Analytical Assessment (Recombination)"
    else: confidence_level = "High-Confidence Analytical Assessment"
    
    if to not in state.visited and depth < MAX_DEPTH: 
        state.queue.put_nowait((to, depth + 1, amt, "NONE", chain, origin_seed))

    node = {
        "type": "LEDGER", "chain": chain, "ticker": ticker,
        "timestamp": timestamp, "from": addr, "sender_entity": sender_entity_lbl,
        "to": to, "receiver_entity": receiver_entity_lbl, "tx": txid, 
        "amount": amt, "usd": amt * USD_RATES.get(chain, 1), 
        "cluster": cluster_id, "entity_class": entity_class, 
        "is_terminal": is_terminal, "is_consolidation": is_consolidation,
        "confidence": confidence_level, "origin_seed": origin_seed,
        "intent_action": intent_data.get("action", "TRANSFER"),
        "edge_type": intent_data.get("edge_type", "TRANSFER"),
        "attributions": "Linkage confirmed via path mapping",
        "intelligence": "Threat actor operational timing"
    }
    
    async with state.state_lock:
        state.ledger.append(node)
        
    if mongo_db is not None:
        try:
            dt_stamp = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
            asyncio.create_task(mongo_db.edges.insert_one({
                "from": addr, "to": to, "edge_type": intent_data.get("edge_type", "TRANSFER"),
                "tx_hash": txid, "chain": chain, "asset": ticker, "amount": str(amt),
                "confidence": confidence_level, "timestamp": dt_stamp, "is_terminal": is_terminal
            }))
        except: pass

    for ws in list(clients):
        try: await ws.send_json(node)
        except: clients.discard(ws)

async def execute_dbscan_clustering():
    if len(state.node_stats) < 2: return
    features = []
    nodes = list(state.node_stats.keys())
    
    for n in nodes:
        stats = state.node_stats[n]
        features.append([stats["in_amt"], stats["out_amt"], stats["in_count"], stats["out_count"]])
        
    try:
        # Optimization: Don't run DBSCAN if features are all uniform zeros
        if not features or all(all(v == 0 for v in row) for row in features): return
        
        scaler = StandardScaler()
        scaled_features = scaler.fit_transform(features)
        db = DBSCAN(eps=0.5, min_samples=2).fit(scaled_features)
        
        updates = []
        for idx, cluster_label in enumerate(db.labels_):
            n = nodes[idx]
            stats = state.node_stats[n]
            is_holding = stats["in_count"] > 0 and stats["out_count"] == 0 and n not in state.seeds
            
            c_id = f"Threat Actor Syndicate Alpha-{cluster_label}" if cluster_label != -1 else "Unclustered"
            updates.append({"node": n, "cluster_id": c_id, "is_holding": is_holding})
            
        for ws in list(clients):
            try: await ws.send_json({"type": "DBSCAN_UPDATE", "data": updates})
            except: pass
    except Exception as e:
        print(f"Clustering failed: {e}")

async def engine_worker(session):
    while True: 
        try: 
            item = await asyncio.wait_for(state.queue.get(), timeout=10.0)
        except asyncio.TimeoutError: 
            if state.queue.empty(): break
            continue
        
        addr, depth, carry_val, obf_path, chain, origin_seed = item
        
        async with state.state_lock:
            if addr in state.visited or depth > MAX_DEPTH: 
                state.queue.task_done(); continue
            state.visited.add(addr)
            
        res = await fetch_txs(session, addr, chain)
        txs = res["data"]
        chain_type = res["type"]
        actual_chain = res.get("actual_chain", chain)
        
        if txs:
            if chain_type == "btc": await process_bitcoin_txs(session, addr, txs, depth, carry_val, obf_path, actual_chain, origin_seed)
            elif chain_type == "tron": await process_tron_txs(session, addr, txs, depth, carry_val, obf_path, actual_chain, origin_seed)
            else: await process_evm_txs(session, addr, txs, depth, carry_val, obf_path, actual_chain, origin_seed)
        
        state.queue.task_done()

async def engine_loop():
    try:
        async with aiohttp.ClientSession() as session:
            print("\n" + "="*60)
            print(" 🚀 [MULTI-CHAIN TRACE INITIALIZED - PARALLEL FETCHING]")
            for seed in state.seeds:
                chain = state.seed_chains.get(seed, "ETHEREUM")
                print(f"    📡 [HYBRID] Tracing {chain} seed simultaneously: {seed}")
            print("="*60 + "\n", flush=True)

            workers = [asyncio.create_task(engine_worker(session)) for _ in range(CONCURRENCY_LIMIT)]
            await state.queue.join()
            for w in workers: w.cancel()
            
            await execute_dbscan_clustering()
            
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(IO_POOL, thread_safe_file_write, list(state.ledger))
            
            for ws in list(clients):
                try: await ws.send_json({"type": "COMPLETE"})
                except: pass

    except Exception as e: traceback.print_exc()

class TraceRequest(BaseModel):
    seeds: str
    target_amount: str = ""
    start_date: str = ""
    end_date: str = ""
    chain_override: str = "AUTO"

\n\n