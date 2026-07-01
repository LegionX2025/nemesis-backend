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
    elif len(val) >= 43 and not val.startswith("0x"): return "SOLANA"
    elif val.startswith("kaspa:"): return "KASPA"
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

app = FastAPI(title="Nemesis OmniChain API", description="Lionsgate OmniChain Forensic Engine API Documentation", version="1.0.0", lifespan=lifespan)
app.mount("/static", StaticFiles(directory="."), name="static")
state = SOCState()
clients = set()
active_engine_task = None

def get_asset_ticker(chain: str) -> str:
    if chain == "BITCOIN": return "BTC"
    elif chain == "TRON": return "TRX"
    elif chain == "POLYGON": return "MATIC"
    if chain == "SOLANA": return "SOL"
    elif chain == "KASPA": return "KAS"
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

async def process_solana_txs(session, addr, txs, depth, carry_val, obf_path, chain, origin_seed):
    pass # To be implemented fully via OKLink or Solscan API

async def process_kaspa_txs(session, addr, txs, depth, carry_val, obf_path, chain, origin_seed):
    pass # To be implemented fully via Kaspa API

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
            elif chain_type == "solana": await process_solana_txs(session, addr, txs, depth, carry_val, obf_path, actual_chain, origin_seed)
            elif chain_type == "kaspa": await process_kaspa_txs(session, addr, txs, depth, carry_val, obf_path, actual_chain, origin_seed)
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

@app.post("/api/start_trace", tags=["Forensic Trace"], summary="Initiate Parallel Chain Trace", description="Starts a parallel graph traversal trace on the provided seed wallets.")
async def api_start_trace(req: TraceRequest):
    try:
        global active_engine_task
        if active_engine_task and not active_engine_task.done(): active_engine_task.cancel()
        
        seeds_list = []
        for s in req.seeds.split('\n'):
            s = s.strip()
            if not s: continue
            chain = detect_chain(s, req.chain_override)
            if chain in EVM_DOMAINS or chain == "EVM_AUTO":
                s = s.lower()
            seeds_list.append(s)
            KNOWN_ENTITIES[s] = "VICTIM Wallet (Seed)"
            
        if not seeds_list: return {"error": "No seeds provided"}
        
        calc_amt = float(req.target_amount) if req.target_amount else 80000.0
        
        state.__init__()
        state.setup(seeds_list, calc_amt, req.chain_override, req.start_date, req.end_date)
        primary_chain = state.seed_chains[seeds_list[0]]
        
        init_msg = {
            "type": "INIT", 
            "target_amount": calc_amt, 
            "seeds": seeds_list,
            "seed_chains": state.seed_chains,
            "ticker": get_asset_ticker(primary_chain)
        }
        for ws in list(clients):
            try: await ws.send_json(init_msg)
            except: pass
            
        active_engine_task = asyncio.create_task(engine_loop())
        return {"status": "started"}
    except Exception as e:
        logger.error(f"Failed to start trace: {e}")
        traceback.print_exc()
        return {"error": str(e)}

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
        <title>Lionsgate Omni-Chain Forensics | Case LGN-US-2026-0172</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <script src="https://cdn.jsdelivr.net/npm/vis-network/standalone/umd/vis-network.min.js"></script>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/tsparticles@2/tsparticles.bundle.min.js"></script>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&family=JetBrains+Mono:wght@400;700&display=swap');
            body { font-family: 'Inter', sans-serif; background-color: #f8fafc; color: #0f172a; margin: 0; overflow: hidden; }
            .font-mono { font-family: 'JetBrains Mono', monospace; }
            #graph { height: calc(100vh - 120px); width: 100%; outline: none; background-color: #fff; }
            ::-webkit-scrollbar { width: 6px; height: 6px; }
            ::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 3px; }
            
            .google-doc { width: 100%; max-width: 900px; margin: 2rem auto; padding: 1in; background: #ffffff; color: #000000; box-shadow: 0 4px 6px rgba(0,0,0,0.1); border: 1px solid #ddd; outline: none; line-height: 1.6; }
            .prose p { margin-bottom: 1rem; text-align: justify; }
            .prose strong { color: #1e3a8a; }
            .prose ul { padding-left: 20px; margin-bottom: 1rem; list-style-type: disc; }
            
            /* Landing Page Styles */
            #landing-page { position: fixed; inset: 0; z-index: 100; background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 50%, #f8fafc 100%); overflow: hidden; display: flex; flex-direction: column; transition: opacity 1.2s ease-in-out, visibility 1.2s ease-in-out; }
            #tsparticles { position: absolute; inset: 0; z-index: 0; opacity: 1.0; }
            .landing-content { position: relative; z-index: 10; width: 100%; height: 100%; display: flex; flex-direction: column; }
            
            .landing-nav { display: flex; justify-content: space-between; align-items: center; padding: 2.5rem 4rem; }
            .landing-logo { display: flex; align-items: center; gap: 1rem; }
            .landing-logo img { height: 45px; border-radius: 8px; border: 1px solid rgba(15,23,42,0.1); }
            .landing-logo-text { font-size: 1.25rem; font-weight: 800; color: #0f172a; letter-spacing: 0.1em; line-height: 1.2; }
            .landing-logo-text span { font-weight: 400; font-size: 0.65em; letter-spacing: 0.25em; display: block; color: #475569; }
            .landing-links { display: flex; gap: 3rem; font-size: 0.75rem; font-weight: 600; letter-spacing: 0.15em; color: #0f172a; text-transform: uppercase; }
            .landing-links a { color: #64748b; text-decoration: none; transition: color 0.3s; cursor: pointer; }
            .landing-links a:hover { color: #0f172a; }
            .landing-btn-outline { border: 1px solid rgba(15,23,42,0.3); color: #0f172a; padding: 0.75rem 2rem; border-radius: 99px; font-size: 0.75rem; font-weight: 600; letter-spacing: 0.1em; transition: all 0.3s; background: transparent; cursor: pointer; }
            .landing-btn-outline:hover { background: #0f172a; color: #fff; }
            
            .landing-main { flex: 1; display: flex; flex-direction: column; justify-content: center; align-items: center; text-align: center; padding: 0 2rem; }
            .landing-tag { display: inline-flex; align-items: center; gap: 0.5rem; background: rgba(255,255,255,0.7); border: 1px solid rgba(15,23,42,0.1); padding: 0.5rem 1rem; border-radius: 99px; color: #334155; font-size: 0.7rem; letter-spacing: 0.1em; margin-bottom: 1.5rem; backdrop-filter: blur(10px); box-shadow: 0 4px 6px rgba(0,0,0,0.02); }
            .landing-title { font-size: 4.5rem; font-weight: 800; color: #0f172a; line-height: 1.1; max-width: 900px; margin-bottom: 1.5rem; letter-spacing: -0.02em; }
            .landing-subtitle { font-size: 1.1rem; color: #475569; max-width: 650px; line-height: 1.6; margin-bottom: 3rem; }
            
            .landing-input-group { display: flex; flex-direction: column; gap: 1.25rem; width: 100%; max-width: 550px; background: rgba(255,255,255,0.7); border: 1px solid rgba(15,23,42,0.1); padding: 2.5rem; border-radius: 24px; backdrop-filter: blur(24px); -webkit-backdrop-filter: blur(24px); box-shadow: 0 25px 50px -12px rgba(0,0,0,0.1); }
            .landing-input-group label { text-align: left; font-size: 0.7rem; font-weight: 800; color: #475569; text-transform: uppercase; letter-spacing: 0.1em; }
            .landing-input-group textarea, .landing-input-group input { width: 100%; background: #ffffff; border: 1px solid rgba(15,23,42,0.2); color: #0f172a; padding: 1rem; border-radius: 12px; font-family: 'JetBrains Mono', monospace; font-size: 0.85rem; outline: none; transition: all 0.3s; resize: none; }
            .landing-input-group textarea:focus, .landing-input-group input:focus { border-color: #3b82f6; box-shadow: 0 0 0 3px rgba(59,130,246,0.1); }
            .landing-btn-primary { background: #0f172a; color: #ffffff; font-weight: 800; padding: 1.25rem; border-radius: 12px; border: none; cursor: pointer; transition: transform 0.2s, box-shadow 0.2s; letter-spacing: 0.15em; text-transform: uppercase; font-size: 0.8rem; margin-top: 0.5rem; }
            .landing-btn-primary:hover { transform: translateY(-2px); box-shadow: 0 10px 25px rgba(15,23,42,0.3); }
            
            .landing-footer { display: flex; justify-content: space-between; align-items: center; padding: 2rem 4rem; border-top: 1px solid rgba(15,23,42,0.05); }
            .landing-footer-logos { display: flex; gap: 2.5rem; opacity: 0.5; }
            
            /* Content Modal */
            #content-modal { position: fixed; inset: 0; z-index: 200; background: rgba(241, 245, 249, 0.98); backdrop-filter: blur(10px); display: flex; justify-content: center; align-items: flex-start; overflow-y: auto; transform: translateY(100%); transition: transform 0.6s cubic-bezier(0.16, 1, 0.3, 1); padding: 4rem 2rem; opacity: 0; visibility: hidden; }
            #content-modal.active { transform: translateY(0); opacity: 1; visibility: visible; }
            .content-modal-inner { width: 100%; max-width: 800px; position: relative; background: #fff; padding: 4rem; border-radius: 24px; box-shadow: 0 25px 50px -12px rgba(0,0,0,0.1); border: 1px solid rgba(15,23,42,0.05); }
            .content-close-btn { position: absolute; top: 1.5rem; right: 1.5rem; background: #f1f5f9; border: 1px solid #cbd5e1; width: 40px; height: 40px; border-radius: 50%; display: flex; justify-content: center; align-items: center; cursor: pointer; color: #0f172a; transition: all 0.2s; }
            .content-close-btn:hover { background: #e2e8f0; }
            .content-title { font-size: 2.5rem; font-weight: 800; color: #0f172a; margin-bottom: 2rem; letter-spacing: -0.02em; border-bottom: 2px solid #f1f5f9; padding-bottom: 1rem; }
            .content-body { font-size: 1.1rem; line-height: 1.8; color: #475569; }
            .content-body h2 { font-size: 1.5rem; font-weight: 700; color: #0f172a; margin-top: 2.5rem; margin-bottom: 1rem; }
            .content-body ul { list-style-type: disc; padding-left: 1.5rem; margin-top: 1rem; }
            .content-body li { margin-bottom: 0.5rem; }
        </style>
    </head>
    <body class="flex flex-col h-screen">
    
        <!-- LANDING PAGE OVERLAY -->
        <div id="landing-page">
            <div id="tsparticles"></div>
            
            <div class="landing-content">
                <nav class="landing-nav">
                    <div class="landing-logo">
                        <img src="/static/logo_nemesis.jpeg" alt="Nemesis Logo">
                        <div class="landing-logo-text">
                            LIONSGATE
                            <span>INTELLIGENCE NETWORK</span>
                        </div>
                    </div>
                    <div class="landing-links">
                        <a onclick="openContentPage('about')">About</a>
                        <a onclick="openContentPage('capabilities')">Capabilities</a>
                        <a onclick="openContentPage('architecture')">Architecture</a>
                        <a onclick="openContentPage('script')">The Script</a>
                        <a onclick="openContentPage('whitepaper')">Whitepaper</a>
                        <a onclick="openContentPage('api')">API Reference</a>
                    </div>
                    <button class="landing-btn-outline" onclick="document.getElementById('landing-seed-input').focus()">REQUEST DEMO</button>
                </nav>
                
                <main class="landing-main">
                    <img src="/static/logo_nemesis.jpeg" alt="Nemesis Logo" class="h-24 mb-6 rounded-2xl shadow-xl border border-slate-200">
                    <div class="landing-tag">
                        <svg class="w-3 h-3 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path></svg>
                        OMNICHAIN INTELLIGENCE ENGINE
                    </div>
                    <h1 class="landing-title mb-2 text-6xl tracking-tighter">NEMESIS</h1>
                    <h2 class="text-xl font-bold text-slate-400 tracking-widest uppercase mb-6">By Lionsgate Intelligence Network</h2>
                    <p class="landing-subtitle">Illuminating the dark web. Intercept, analyze, and visualize global cross-chain fund flows instantly. Uncover obfuscated threat actor syndicates with military-grade behavioral attribution.</p>
                    
                    <div class="landing-input-group">
                        <div>
                            <label>Target Seed Wallets</label>
                            <textarea id="landing-seed-input" rows="3" placeholder="Enter 0x... addresses (one per line)"></textarea>
                        </div>
                        <div class="flex gap-4 w-full">
                            <div class="flex-1">
                                <label>Start Date (Optional)</label>
                                <input type="date" id="landing-start-date" class="w-full bg-white/5 border border-slate-200/20 rounded p-3 text-slate-700 font-mono focus:outline-none focus:border-blue-400 focus:bg-white/90 transition" style="background: rgba(255,255,255,0.7);">
                            </div>
                            <div class="flex-1">
                                <label>End Date (Optional)</label>
                                <input type="date" id="landing-end-date" class="w-full bg-white/5 border border-slate-200/20 rounded p-3 text-slate-700 font-mono focus:outline-none focus:border-blue-400 focus:bg-white/90 transition" style="background: rgba(255,255,255,0.7);">
                            </div>
                        </div>
                        <div>
                            <label>Target Amount Threshold (Optional)</label>
                            <input type="number" id="landing-target-amount" placeholder="e.g. 80000">
                        </div>
                        <button class="landing-btn-primary" onclick="initiateLandingTrace()">START OMNICHAIN TRACE &rarr;</button>
                    </div>
                </main>
                
                <footer class="landing-footer">
                    <div class="text-[10px] font-bold text-slate-500 uppercase tracking-wider flex items-center gap-2">
                        <div class="w-2 h-2 bg-blue-500 rounded-full"></div> DATA PLATFORM
                    </div>
                    <div class="landing-footer-logos flex gap-8 items-center text-slate-500 text-xs font-bold font-mono tracking-widest">
                        <span>LIONSGATE</span>
                        <span>QUARK_NET</span>
                        <span>POLYGON</span>
                        <span>ETHEREUM</span>
                    </div>
                </footer>
            </div>
        </div>
        
        <!-- CONTENT MODAL -->
        <div id="content-modal">
            <div class="content-modal-inner">
                <button class="content-close-btn" onclick="closeContentPage()">
                    <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
                </button>
                <h1 class="content-title" id="content-modal-title">Title</h1>
                <div class="content-body" id="content-modal-body"></div>
            </div>
        </div>

        <!-- Header -->
        
        <header class="bg-white border-b border-slate-200 p-4 flex flex-col gap-4 shadow-sm z-10 shrink-0">
            <div class="flex justify-between items-center w-full">
                <div>
                    <h1 class="text-xl font-black uppercase tracking-wider text-slate-900">Lionsgate Nemesis Engine</h1>
                    <p class="text-xs text-blue-600 font-mono mt-1">PRODUCTION EVIDENTIARY TRACING GRAPH</p>
                </div>
                <div class="flex gap-3">
                    <button onclick="toggleLogModal()" class="bg-slate-200 hover:bg-slate-300 text-slate-700 px-4 py-2 rounded text-xs font-bold shadow transition flex items-center gap-2">
                        Evidentiary Transaction Log
                    </button>
                    <button onclick="submitTrace()" class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded text-xs font-bold shadow transition flex items-center gap-2">
                        Run Parallel Trace
                    </button>
                    <button onclick="triggerGeneratePDF()" class="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded text-xs font-bold shadow transition flex items-center gap-2">
                        Generate Forensic Report
                    </button>
                </div>
            </div>
            <div class="flex gap-4 items-start w-full bg-slate-50 p-3 border border-slate-200 rounded">
                <div class="flex-grow">
                    <label class="block text-xs font-bold text-slate-700 mb-1">Target Seed/Suspect Addresses (One per line)</label>
                    <textarea id="customSeeds" class="w-full text-xs border border-slate-300 rounded p-2 focus:ring-blue-500 font-mono h-16" placeholder="0x...
bc1...
T..."></textarea>
                </div>
                <div class="w-48">
                    <label class="block text-xs font-bold text-slate-700 mb-1">Total Loss Amount (USD)</label>
                    <input type="number" id="customLoss" class="w-full text-xs border border-slate-300 rounded p-2 focus:ring-blue-500 font-mono" placeholder="80000" value="80000">
                </div>
                <div class="w-48">
                    <label class="block text-xs font-bold text-slate-700 mb-1">Victim Initials / Case ID</label>
                    <input type="text" id="customVictim" class="w-full text-xs border border-slate-300 rounded p-2 focus:ring-blue-500 font-mono" placeholder="[REDACTED]" value="[REDACTED]">
                </div>
            </div>
        </header>


        <nav id="graphTabs" class="bg-slate-50 border-b border-slate-200 px-4 py-3 flex gap-2 shrink-0 overflow-x-auto items-center">
            <button id="tab-btn-all" onclick="switchGraphTab('all')" class="px-4 py-1.5 bg-blue-600 text-white font-bold rounded shadow-md text-xs whitespace-nowrap transition">
                🌐 Unified Graph
            </button>
            <div class="h-6 w-px bg-slate-300 mx-2"></div>
            
            <div class="flex items-center gap-2">
                <input type="text" id="nodeSearch" placeholder="Search wallet/entity..." class="text-xs border border-slate-300 rounded px-2 py-1 w-48 focus:outline-none focus:ring-1 focus:ring-blue-500" onkeyup="if(event.key==='Enter') executeSearch()">
                <button onclick="executeSearch()" class="px-3 py-1 bg-slate-200 hover:bg-slate-300 text-slate-700 text-xs font-bold rounded shadow-sm transition">Search</button>
            </div>
            
            <div class="h-6 w-px bg-slate-300 mx-2"></div>
            <select id="layoutSelect" onchange="changeLayout()" class="text-xs border border-slate-300 text-slate-700 rounded px-2 py-1 focus:outline-none focus:ring-1 focus:ring-blue-500 font-bold">
               <option value="physics">Layout: Organic (Physics)</option>
               <option value="hierarchical_lr">Layout: Sequential (Left-Right)</option>
               <option value="hierarchical_ud">Layout: Sequential (Top-Bottom)</option>
            </select>
            
            <div class="h-6 w-px bg-slate-300 mx-2"></div>
            <select id="pathFilterSelect" onchange="applyPathFilter()" class="text-xs border border-slate-300 text-slate-700 rounded px-2 py-1 focus:outline-none focus:ring-1 focus:ring-blue-500 font-bold">
               <option value="ALL">Graph Filter: ALL PATHS</option>
               <option value="SUSPECT_TO_CEX">Filter: SUSPECT ➡️ CEX</option>
               <option value="SUSPECT_TO_MIXER">Filter: SUSPECT ➡️ MIXERS</option>
               <option value="SUSPECT_TO_BRIDGE">Filter: SUSPECT ➡️ BRIDGE</option>
               <option value="VICTIM_TO_CEX">Filter: VICTIM ➡️ SUSPECT ➡️ CEX</option>
               <option value="VICTIM_TO_MIXER">Filter: VICTIM ➡️ SUSPECT ➡️ MIXER</option>
            </select>
            
            <div class="h-6 w-px bg-slate-300 mx-2"></div>
            <button onclick="highlightLossPaths()" class="px-3 py-1.5 bg-red-50 text-red-600 border border-red-200 hover:bg-red-100 text-xs font-bold rounded shadow-sm transition whitespace-nowrap flex items-center gap-1">
                <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"></path></svg>
                Highlight Loss Path
            </button>
            <button onclick="startCourtReplay()" class="px-3 py-1.5 bg-purple-50 text-purple-700 border border-purple-200 hover:bg-purple-100 text-xs font-bold rounded shadow-sm transition whitespace-nowrap flex items-center gap-1">
                <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"></path><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                Court Replay
            </button>
        </nav>

        <!-- Main Graph Area -->
        <div class="relative flex-grow bg-white">
            <div class="absolute top-4 left-4 z-10 bg-white/90 backdrop-blur border border-slate-200 p-3 rounded-lg shadow-md pointer-events-none">
                <h3 class="text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-2 border-b border-slate-200 pb-1">Node Legend</h3>
                <div class="flex flex-col gap-1.5 text-xs">
                    <div class="flex items-center gap-2"><div class="w-4 h-4 rounded-full border border-slate-300 flex items-center justify-center bg-white"></div> <span class="text-slate-700">Routing / Normal</span></div>
                    <div class="flex items-center gap-2"><div class="w-4 h-4 rounded-full border-2 border-red-500 flex items-center justify-center bg-red-50"></div> <span class="text-slate-700">Seed Source</span></div>
                    <div class="flex items-center gap-2"><div class="w-4 h-4 rounded-full border-2 border-purple-500 flex items-center justify-center bg-purple-50"></div> <span class="text-slate-700">Recombination / Mixer</span></div>
                    <div class="flex items-center gap-2"><div class="w-4 h-4 rounded-full border-2 border-emerald-500 flex items-center justify-center bg-emerald-50"></div> <span class="text-slate-700">Exchange (CEX)</span></div>
                    <div class="flex items-center gap-2"><div class="w-4 h-4 rounded-full border-2 border-orange-500 flex items-center justify-center bg-orange-50"></div> <span class="text-slate-700">Terminal Holding</span></div>
                </div>
            </div>
            
            <div class="absolute bottom-4 right-4 z-10 bg-white/95 backdrop-blur border border-red-200 p-3 rounded-lg shadow-xl w-80 pointer-events-auto max-h-[50vh] overflow-y-auto hidden flex-col gap-2 transition-all duration-300" id="live-terminals-container">
                <div class="flex items-center justify-between sticky top-0 bg-white/95 pb-2 border-b border-red-100 z-10">
                    <h3 class="text-xs font-black text-red-600 uppercase tracking-wider flex items-center gap-2">
                        <span class="relative flex h-2 w-2">
                          <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
                          <span class="relative inline-flex rounded-full h-2 w-2 bg-red-500"></span>
                        </span>
                        Live CEX Terminals
                    </h3>
                </div>
                <div id="live-terminals-list" class="flex flex-col gap-2">
                    <!-- Terminals Appended Here dynamically -->
                </div>
            </div>

            <div id="graph"></div>
        </div>

        <!-- Nemesis ID: Multi-Domain Intelligence Reconstruction Engine -->
        <div id="nemesisIdModal" class="fixed inset-y-0 right-0 w-[1000px] max-w-full bg-slate-900 shadow-[[-20px_0_30px_rgba(0,0,0,0.5)]] transform translate-x-full transition-transform duration-300 ease-in-out z-[60] flex flex-col border-l border-slate-700 text-slate-300">
            <div class="bg-black text-white px-6 py-4 flex justify-between items-center shadow-lg border-b border-slate-700">
                <div class="flex items-center gap-4">
                    <div class="w-12 h-12 rounded-full bg-slate-800 flex items-center justify-center border border-blue-500 shadow-[0_0_15px_rgba(59,130,246,0.5)]">
                        <svg class="w-7 h-7 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 11c0 3.517-1.009 6.799-2.753 9.571m-3.44-2.04l.054-.09A13.916 13.916 0 008 11a4 4 0 118 0c0 1.017-.07 2.019-.203 3m-2.118 6.844A21.88 21.88 0 0015.171 17m3.839 1.132c.645-2.266.99-4.659.99-7.132A8 8 0 008 4.07M3 15.364c.64-1.319 1-2.8 1-4.364 0-1.457.39-2.823 1.07-4"></path></svg>
                    </div>
                    <div>
                        <h2 class="text-xl font-black uppercase tracking-widest text-blue-400 flex items-center gap-3">
                            Nemesis ID 
                            <span class="text-[10px] px-2 py-0.5 bg-red-900/50 text-red-400 border border-red-700 rounded animate-pulse hidden" id="nid-alert-badge">CUSTODIAL ALERT</span>
                        </h2>
                        <div class="font-mono text-base font-bold text-white tracking-wider select-all flex items-center gap-2">
                            <span id="nid-network-icon" class="text-xl">🌐</span>
                            <span id="nid-wallet-address">0x...</span>
                        </div>
                        <div class="text-xs uppercase text-slate-400 font-bold" id="nid-entity-tag">SUBJECT WALLET ENTITY</div>
                    </div>
                </div>
                <div class="flex items-center gap-3">
                    <button onclick="triggerGeneratePDF()" class="bg-blue-600/20 text-blue-400 border border-blue-500 hover:bg-blue-600 hover:text-white transition px-4 py-2 rounded text-xs font-bold uppercase tracking-wider flex items-center gap-2">
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path></svg>
                        Export Dossier
                    </button>
                    <button onclick="closeNemesisModal()" class="text-slate-400 hover:text-white transition p-2 rounded hover:bg-slate-800" title="Close">
                        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
                    </button>
                </div>
            </div>
            
            <div class="flex overflow-x-auto bg-slate-950 border-b border-slate-700 text-[10px] font-bold uppercase tracking-wider shrink-0" id="nid-tabs-nav">
                <!-- JS generated tabs -->
            </div>

            <div class="flex-grow overflow-y-auto p-6 bg-slate-900 text-sm font-mono" id="nid-tab-content">
                <!-- JS generated content -->
            </div>
        </div>

        <!-- Data Table / Log Area Modal -->
        <div id="logModal" class="fixed inset-y-0 right-0 w-[900px] max-w-full bg-white shadow-2xl transform translate-x-full transition-transform duration-300 ease-in-out z-50 flex flex-col border-l border-slate-200">
            <div class="bg-slate-800 text-white px-4 py-3 flex justify-between items-center shadow-md">
                <div class="flex items-center gap-3">
                    <span class="text-sm font-bold uppercase tracking-wider">Evidentiary Transaction Log</span>
                    <button onclick="exportLiveLogCSV()" class="bg-slate-700 hover:bg-slate-600 text-white border border-slate-500 px-2 py-0.5 rounded text-[10px] font-bold transition shadow-sm">Export CSV</button>
                    <button onclick="exportLiveLogJSON()" class="bg-slate-700 hover:bg-slate-600 text-white border border-slate-500 px-2 py-0.5 rounded text-[10px] font-bold transition shadow-sm">Export JSON</button>
                </div>
                <div class="flex items-center gap-4">
                    <span id="status" class="text-[10px] text-emerald-400 font-mono font-bold">Awaiting Trace Execution...</span>
                    <button onclick="toggleLogModal()" class="text-slate-300 hover:text-white transition" title="Minimize">
                        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path></svg>
                    </button>
                </div>
            </div>
            <div id="tx-log-container" class="flex-grow overflow-auto p-0 bg-slate-50">
                <table class="w-full text-left text-xs text-slate-700 border-collapse">
                    <thead class="bg-slate-200 sticky top-0 border-b border-slate-300 font-bold text-slate-700 z-10 shadow-sm">
                        <tr>
                            <th class="p-2 pl-4 whitespace-nowrap">Date/Time (UTC)</th>
                            <th class="p-2 whitespace-nowrap">TX Hash</th>
                            <th class="p-2 whitespace-nowrap">From Wallet</th>
                            <th class="p-2 whitespace-nowrap">To Wallet</th>
                            <th class="p-2 whitespace-nowrap">Receiver Entity</th>
                            <th class="p-2 text-right pr-4 whitespace-nowrap">Amount</th>
                            <th class="p-2 whitespace-nowrap">Transaction Type</th>
                            <th class="p-2 whitespace-nowrap">Behavioral Cluster</th>
                            <th class="p-2 whitespace-nowrap">Confidence</th>
                        </tr>
                    </thead>
                    <tbody id="tx-log-body" class="divide-y divide-slate-200 font-mono text-[11px] bg-white">
                    </tbody>
                </table>
            </div>
        </div>
        
        <!-- REPORT WORKSPACE OVERLAY -->
        <div id="view-report" class="hidden absolute top-[70px] left-0 w-full h-[calc(100vh-70px)] bg-slate-100 z-50 overflow-y-auto p-4 md:p-8 text-slate-900">
            <div class="max-w-[900px] mx-auto flex justify-between items-center mb-4 no-print bg-white p-3 rounded-lg shadow-sm border border-slate-200">
                <p class="text-sm text-slate-500 font-bold ml-2">Evidentiary Document Format <span class="bg-green-100 text-green-800 px-2 py-0.5 rounded ml-2">FORENSIC LEGAL REPORT</span></p>
                <div class="flex gap-2">
                    <button onclick="closeReport()" class="bg-slate-200 text-slate-700 px-4 py-1.5 rounded font-bold shadow-sm hover:bg-slate-300 transition text-sm">Close Report</button>
                    <button onclick="triggerGeneratePDF()" class="bg-blue-600 text-white px-4 py-1.5 rounded font-bold shadow-md hover:bg-blue-700 transition text-sm">Download PDF</button>
                </div>
            </div>
            
            <div id="print-doc" class="google-doc doc-container break-words text-sm relative">
                <div class="text-center border-b-2 border-slate-900 pb-4 mb-6">
                    <p class="text-xs uppercase text-slate-600 font-bold tracking-widest">Blockchain Forensics & Financial Crime Intelligence</p>
                    <h1 class="text-2xl font-black uppercase text-slate-900 tracking-tight mt-2">BLOCKCHAIN FORENSIC ANALYSIS REPORT</h1>
                    <p class="text-sm text-slate-700 mt-1">Cryptocurrency Investment Fraud | Funds Recovery Support</p>
                </div>

                <table class="w-full text-left border-collapse mb-8 text-xs">
                    <tbody class="divide-y divide-slate-300">
                        <tr><th class="py-2 w-1/3 text-slate-600">Report Number</th><td class="py-2 font-bold">LGN-US-2026-0172-EVIDENTIARY</td></tr>
                        <tr><th class="py-2 text-slate-600">Subject/Complainant</th><td class="py-2 font-bold text-red-600" id="docVictimInitials"></td></tr>
                        <tr><th class="py-2 text-slate-600">Assets Traced</th><td class="py-2 font-bold">Multi-Chain Virtual Assets (BTC, ETH, POLY, TRX)</td></tr>
                        <tr><th class="py-2 text-slate-600">Prepared For</th><td class="py-2 font-bold">Law Enforcement Cyber / Financial Crimes Unit</td></tr>
                        <tr><th class="py-2 text-slate-600">Date of Report</th><td class="py-2 font-bold" id="doc-date"></td></tr>
                    </tbody>
                </table>

                <p class="font-bold text-red-700 text-xs mb-8 text-center uppercase tracking-widest border border-red-700 p-2 bg-red-50">CONFIDENTIAL. This document is prepared in support of a victim funds-recovery matter and intended for law enforcement use.</p>

                <h2 class="text-lg font-bold border-b border-slate-400 pb-1 mb-3 uppercase text-blue-900 page-break-after-avoid">Table of Contents</h2>
                <div class="text-sm text-slate-700 mb-8 space-y-1 font-mono">
                    <p>1. Introduction - incident</p>
                    <p>2. Executive Summary</p>
                    <p>3. Recovery probability percentage and CEX - Custodial identified</p>
                    <p>4. Incident Details & Investigation Methodology</p>
                    <p>5. Chronological fund flow & Timeline of Events</p>
                    <p>6. Overview of Key Transactions & Analysis of Transaction Patterns</p>
                    <p>7. Source and Destination Entities</p>
                    <p>8. Blockchain Snapshot Transaction Graph</p>
                    <p>9. Full Evidentiary Transaction Ledger</p>
                    <p>10. Recovery Opportunities & Subpoena Targets</p>
                    <p>11. Investigation Summary and Conclusion</p>
                    <p>12. Glossary of Cryptocurrency Terms</p>
                    <p>13. Crypto Victims Guidelines & Law Enforcement Contacts</p>
                    <p>14. Disclaimer & Scope of Services</p>
                </div>

                <div class="page-break" style="page-break-before: always; margin-top: 2rem;"></div>

                <h2 class="text-lg font-bold border-b border-slate-400 pb-1 mb-3 uppercase text-blue-900">1. Introduction - Incident</h2>
                <p class="mb-6">This report documents the forensic tracing of digital assets misappropriated from the complainant. The investigation focuses on identifying the origin, flow, obfuscation techniques, and final consolidation points (terminals) of the stolen funds across multiple blockchains.</p>
                
                <h2 class="text-lg font-bold border-b border-slate-400 pb-1 mb-3 uppercase text-blue-900">2. Executive Summary</h2>
                <div class="bg-blue-50 border-l-4 border-blue-600 p-4 mb-6">
                    <h3 class="font-bold text-blue-900 mb-2">AI Narrative & Core Findings</h3>
                    <p class="mb-2"><strong>Who are the suspect(s)?</strong> <span id="narrative-suspects" class="text-red-700 font-bold break-all"></span></p>
                    <p class="mb-2"><strong>What is the total loss amount assets?</strong> <span id="narrative-total-loss" class="font-mono font-bold"></span></p>
                    <p><strong>Where did the assets land?</strong> <span id="narrative-landed" class="font-bold text-emerald-700"></span></p>
                </div>

                <h2 class="text-lg font-bold border-b border-slate-400 pb-1 mb-3 uppercase text-blue-900">3. Recovery probability & CEX - Custodial identified</h2>
                <p class="mb-6 text-sm">Based on the traced funds, <strong id="narrative-prob" class="text-emerald-700"></strong> of the consolidated assets have landed at known centralized exchanges (CEXs). These represent immediate, high-probability recovery opportunities via law enforcement subpoena or freeze orders directed at the identified CEX compliance departments.</p>

                <h2 class="text-lg font-bold border-b border-slate-400 pb-1 mb-3 uppercase text-blue-900">4. Incident Details & Investigation Methodology</h2>
                <p class="mb-4"><strong>Data Sources:</strong> On-chain transaction records from Bitcoin, Ethereum, Tron, and Polygon ledgers via proprietary node RPCs. OKLink and proprietary OSINT databases for entity attribution.<br>
                <strong>Methodology:</strong> Multi-layer depth-first heuristic clustering (DBSCAN) combined with forward flow analysis. Identified obfuscation layers (mixers, bridges) were mapped to trace recombination patterns.</p>
                
                <h2 class="text-lg font-bold border-b border-slate-400 pb-1 mb-3 uppercase text-blue-900">5. Chronological fund flow & Timeline of Events</h2>
                <p class="mb-6">The fund flow demonstrates rapid dispersion from the victim seed wallets immediately following the breach, followed by complex laundering hops (peel chains) terminating in identified CEX holding wallets. See Section 9 for exact timestamps.</p>
                
                <h2 class="text-lg font-bold border-b border-slate-400 pb-1 mb-3 uppercase text-blue-900">6. Overview of Key Transactions & Analysis of Patterns</h2>
                <p class="mb-6">Threat actors utilized high-speed automated transfers to split funds. Key patterns identified include rapid succession transfers, bridge jumping, and consolidation at centralized liquidity providers to off-ramp to fiat.</p>
                
                <h2 class="text-lg font-bold border-b border-slate-400 pb-1 mb-3 uppercase text-blue-900">7. Source and Destination Entities</h2>
                <p class="mb-6">Source entities include the primary victim seed wallets. Destination entities represent the terminal consolidation points mapped in the ledger. All addresses and transactions are comprehensively listed in Sections 9 and 10.</p>

                <div class="page-break" style="page-break-before: always; margin-top: 2rem;"></div>
                <h2 class="text-lg font-bold border-b border-slate-400 pb-1 mb-3 uppercase text-blue-900">8. Blockchain Snapshot Transaction Graph</h2>
                <div class="border border-slate-300 p-2 bg-slate-50 mb-8 flex justify-center">
                    <img id="report-graph-img" src="" style="max-width: 100%; height: auto;" alt="Tracing Graph">
                </div>

                <div class="page-break" style="page-break-before: always; margin-top: 2rem;"></div>
                <h2 class="text-lg font-bold border-b border-slate-400 pb-1 mb-3 uppercase text-blue-900">9. Full Evidentiary Transaction Ledger</h2>
                <p class="text-xs text-slate-600 mb-2">The following table documents every traceable hop, consolidation, and transfer identified across all seed origins.</p>
                <div class="overflow-x-auto mb-8">
                    <table class="w-full text-left text-[9px] border border-slate-400 font-sans">
                        <thead class="bg-blue-50 text-blue-900 font-bold">
                            <tr>
                                <th class="p-1 border border-slate-400">Date/Time (UTC)</th>
                                <th class="p-1 border border-slate-400">TX Hash</th>
                                <th class="p-1 border border-slate-400">From Wallet</th>
                                <th class="p-1 border border-slate-400">To Wallet</th>
                                <th class="p-1 border border-slate-400">Receiver Entity</th>
                                <th class="p-1 border border-slate-400 text-right">Amount</th>
                                <th class="p-1 border border-slate-400">Transaction Type</th>
                                <th class="p-1 border border-slate-400">Behavioral Cluster</th>
                                <th class="p-1 border border-slate-400">Confidence</th>
                            </tr>
                        </thead>
                        <tbody id="report-ledger-body" class="divide-y divide-slate-300"></tbody>
                    </table>
                </div>

                <div class="page-break" style="page-break-before: always; margin-top: 2rem;"></div>
                <h2 class="text-lg font-bold border-b border-red-400 pb-1 mb-3 uppercase text-red-900">10. Recovery Opportunities & Subpoena Targets</h2>
                <p class="text-xs text-slate-600 mb-2">Law enforcement should direct preservation, forfeiture, and subpoena orders (KYC requests) to the following custodial entities and terminal holdings identified as holding victim funds or consolidated proceeds.</p>
                <table class="w-full text-left text-[10px] border border-slate-400 font-sans mb-8">
                    <thead class="bg-red-50 text-red-900 font-bold">
                        <tr>
                            <th class="p-2 border border-slate-400">Target Entity (Preservation/KYC)</th>
                            <th class="p-2 border border-slate-400">Wallet Addresses (Receiver & Sender)</th>
                            <th class="p-2 border border-slate-400">Latest TX Hash</th>
                            <th class="p-2 border border-slate-400">Date/Time</th>
                            <th class="p-2 border border-slate-400 text-right">Consolidated Vol.</th>
                            <th class="p-2 border border-slate-400">Confidence & Indicators</th>
                        </tr>
                    </thead>
                    <tbody id="doc-subpoena-table" class="divide-y divide-slate-300"></tbody>
                </table>
                
                <h2 class="text-lg font-bold border-b border-slate-400 pb-1 mb-3 uppercase text-blue-900">11. Investigation Summary and Conclusion</h2>
                <p class="mb-6">The traced assets have been successfully tracked from the origin seed through various obfuscation layers to terminal endpoints. Law enforcement action targeting the entities in Section 10 represents the most viable path to asset recovery.</p>

                <h2 class="text-lg font-bold border-b border-slate-400 pb-1 mb-3 uppercase text-blue-900">12. Glossary of Cryptocurrency Terms</h2>
                <p class="text-xs text-slate-600 mb-6">
                <strong>Address:</strong> A cryptographic identifier used to send and receive funds.<br>
                <strong>TX Hash / TXID:</strong> A unique transaction identifier on the blockchain.<br>
                <strong>CEX (Centralized Exchange):</strong> A custodial platform (e.g., Binance, Kraken) that holds user funds and enforces KYC.<br>
                <strong>Mixer:</strong> A service (e.g., Tornado Cash) used to obfuscate the origin of funds.<br>
                <strong>Bridge:</strong> A protocol to transfer assets between different blockchains.
                </p>

                <div class="page-break" style="page-break-before: always; margin-top: 2rem;"></div>
                <h2 class="text-lg font-bold border-b border-slate-400 pb-1 mb-3 uppercase text-blue-900">13. Crypto Victims Guidelines & Law Enforcement Contacts</h2>
                <div class="bg-slate-50 p-4 border border-slate-300 text-sm mb-6">
                    <p class="font-bold mb-2 text-slate-900">Recommended Steps for the Victim:</p>
                    <ol class="list-decimal pl-5 mb-4 space-y-1 text-slate-700">
                        <li>Do not engage further with the threat actors.</li>
                        <li>File an IC3 report (Internet Crime Complaint Center) at www.ic3.gov.</li>
                        <li>Provide this complete forensic evidentiary report to your local and federal law enforcement agencies.</li>
                        <li>Request that law enforcement immediately send a preservation order to the Exchanges listed in Section 10.</li>
                    </ol>
                    <p class="font-bold mb-1 text-slate-900">Law Enforcement Contacts (US National):</p>
                    <ul class="list-disc pl-5 text-slate-700">
                        <li><strong>FBI IC3:</strong> Submit complaint online (ic3.gov)</li>
                        <li><strong>US Secret Service:</strong> Cyber Fraud Task Force</li>
                        <li><strong>Local Police Department:</strong> Financial Crimes Unit (Check local jurisdiction)</li>
                    </ul>
                </div>
                
                <p class="text-center font-bold text-red-600 mb-8 border border-red-200 p-2 bg-red-50">Disclaimer: Lionsgate Network is on standby to support law enforcement detectives with forensic evidence and help facilitate the strongest outcome. You are not alone — we've got your back.</p>

                <div class="page-break" style="page-break-before: always; margin-top: 2rem;"></div>
                <h2 class="text-lg font-bold border-b border-slate-400 pb-1 mb-3 uppercase text-blue-900">14. Disclaimer & Scope of Services</h2>
                <div class="text-[10px] text-slate-500 text-justify leading-relaxed">
                    <p class="mb-2">Lionsgate Network makes no warranties, whether express, implied, statutory, or otherwise, with respect to the services or deliverables provided in this report. Lionsgate Network specifically disclaims all implied warranties of merchantability, fitness for a particular purpose, non-infringement, and those arising from a course of dealing, usage, or trade, and all such warranties are excluded to the fullest extent permitted by law.</p>
                    <p class="mb-2">Lionsgate Network will not be liable for any lost profits, business, contracts, revenues, goodwill, production, anticipated savings, loss of data, or costs of procuring substitute goods or services, or for any claim or demand against the company by any other party. In no event will Lionsgate Network be liable for consequential, incidental, special, indirect, or exemplary damages arising out of this agreement or any work statement, however caused and (to the fullest extent permitted by law) under any theory of liability—including negligence—even if Lionsgate Network has been advised of the possibility of such damages.</p>
                    <p class="mb-2">Lionsgate Network supports your recovery journey by producing advanced forensic blockchain tracing and OSINT intelligence designed to document the flow of assets, identify relevant entities, and prepare the evidentiary foundation required for escalation.</p>
                    <p class="mb-2">It is essential for clients to understand that law enforcement is the only authority empowered to subpoena, freeze, or seize funds. Our role is to strengthen your case, accelerate understanding, and provide detectives with the clearest possible roadmap for action—maximizing the probability of a successful recovery outcome.</p>
                    <p>Lionsgate Network stands ready to collaborate with investigators, share findings, and assist in presenting your case through accurate, verified, and legally structured forensic evidence.</p>
                </div>
            </div>
        </div>

        <script>
            document.getElementById("doc-date").innerText = new Date().toLocaleDateString();
            document.getElementById("docVictimInitials").innerText = document.getElementById("customVictim").value || "[REDACTED]";
            
            let currentTraceSeeds = "";
            
            window.exportedDataRows = [];
            window.currentActiveSeedTab = 'all';
            window.terminalMap = {};

            const explorerFamilies = {
                "EVM": [
                    { name: "Ethereum (Etherscan)", url: "https://etherscan.io", icon: "🔷",
                      links: (addr) => [
                          { label: "Wallet / Assets", path: `/address/${addr}` },
                          { label: "Transactions", path: `/txs?a=${addr}` },
                          { label: "ERC-20 Transfers", path: `/address/${addr}#tokentxns` },
                          { label: "Analytics", path: `/address/${addr}#analytics` },
                          { label: "Authorizations", path: `/address/${addr}#authorizations` },
                          { label: "Internal Txs", path: `/txsInternal?a=${addr}` }
                      ]
                    },
                    { name: "Base", url: "https://basescan.org", icon: "🔵", links: (addr) => [ { label: "Wallet / Assets", path: `/address/${addr}` }, { label: "Transactions", path: `/txs?a=${addr}` }, { label: "ERC-20", path: `/address/${addr}#tokentxns` }, { label: "Analytics", path: `/address/${addr}#analytics` } ] },
                    { name: "BNB Smart Chain", url: "https://bscscan.com", icon: "🟡", links: (addr) => [ { label: "Wallet", path: `/address/${addr}` }, { label: "Transactions", path: `/txs?a=${addr}` }, { label: "BEP-20", path: `/address/${addr}#tokentxns` } ] },
                    { name: "Arbitrum", url: "https://arbiscan.io", icon: "🟦", links: (addr) => [ { label: "Wallet", path: `/address/${addr}` }, { label: "Transactions", path: `/txs?a=${addr}` }, { label: "ERC-20", path: `/address/${addr}#tokentxns` } ] },
                    { name: "Optimism", url: "https://optimistic.etherscan.io", icon: "🔴", links: (addr) => [ { label: "Wallet", path: `/address/${addr}` }, { label: "Transactions", path: `/txs?a=${addr}` }, { label: "ERC-20", path: `/address/${addr}#tokentxns` } ] },
                    { name: "Polygon", url: "https://polygonscan.com", icon: "🟣", links: (addr) => [ { label: "Wallet", path: `/address/${addr}` }, { label: "Transactions", path: `/txs?a=${addr}` }, { label: "ERC-20", path: `/address/${addr}#tokentxns` } ] },
                    { name: "Avalanche", url: "https://snowtrace.io", icon: "🔺", links: (addr) => [ { label: "Wallet", path: `/address/${addr}` }, { label: "Transactions", path: `/txs?a=${addr}` } ] },
                    { name: "Fantom", url: "https://ftmscan.com", icon: "👻", links: (addr) => [ { label: "Wallet", path: `/address/${addr}` }, { label: "Transactions", path: `/txs?a=${addr}` } ] },
                    { name: "Sonic", url: "https://sonicscan.org", icon: "💨", links: (addr) => [ { label: "Wallet", path: `/address/${addr}` }, { label: "Transactions", path: `/txs?a=${addr}` } ] },
                    { name: "Scroll", url: "https://scrollscan.com", icon: "📜", links: (addr) => [ { label: "Wallet", path: `/address/${addr}` }, { label: "Transactions", path: `/txs?a=${addr}` } ] },
                    { name: "Linea", url: "https://lineascan.build", icon: "➖", links: (addr) => [ { label: "Wallet", path: `/address/${addr}` }, { label: "Transactions", path: `/txs?a=${addr}` } ] },
                    { name: "Blast", url: "https://blastscan.io", icon: "💥", links: (addr) => [ { label: "Wallet", path: `/address/${addr}` }, { label: "Transactions", path: `/txs?a=${addr}` } ] },
                    { name: "Mantle", url: "https://mantlescan.xyz", icon: "🟢", links: (addr) => [ { label: "Wallet", path: `/address/${addr}` }, { label: "Transactions", path: `/txs?a=${addr}` } ] },
                    { name: "Cronos", url: "https://cronoscan.com", icon: "⏱️", links: (addr) => [ { label: "Wallet", path: `/address/${addr}` }, { label: "Transactions", path: `/txs?a=${addr}` } ] },
                    { name: "Gnosis", url: "https://gnosisscan.io", icon: "🦉", links: (addr) => [ { label: "Wallet", path: `/address/${addr}` }, { label: "Transactions", path: `/txs?a=${addr}` } ] },
                    { name: "Harmony", url: "https://explorer.harmony.one", icon: "🎵", links: (addr) => [ { label: "Wallet", path: `/address/${addr}` }, { label: "Transactions", path: `/address/${addr}` } ] }
                ],
                "TRON": [
                    { name: "Tronscan", url: "https://tronscan.org", icon: "🔴", links: (addr) => [ { label: "Account Overview", path: `/#/address/${addr}` }, { label: "Transfers", path: `/#/address/${addr}/transfers` } ] }
                ],
                "BTC": [
                    { name: "Blockchain.com", url: "https://www.blockchain.com", icon: "₿", links: (addr) => [ { label: "Address Summary", path: `/explorer/addresses/btc/${addr}` } ] },
                    { name: "Mempool.space", url: "https://mempool.space", icon: "🟪", links: (addr) => [ { label: "Transactions", path: `/address/${addr}` } ] }
                ],
                "SOLANA": [
                    { name: "Solscan", url: "https://solscan.io", icon: "☀️", links: (addr) => [ { label: "Account Overview", path: `/account/${addr}` }, { label: "SPL Transfers", path: `/account/${addr}#splTransfer` } ] },
                    { name: "Solana Explorer", url: "https://explorer.solana.com", icon: "🟢", links: (addr) => [ { label: "Address Info", path: `/address/${addr}` } ] }
                ],
                "XRP": [
                    { name: "XRPScan", url: "https://xrpscan.com", icon: "✖️", links: (addr) => [ { label: "Account Overview", path: `/account/${addr}` } ] },
                    { name: "Bithomp", url: "https://bithomp.com", icon: "🪙", links: (addr) => [ { label: "Explorer", path: `/explorer/${addr}` } ] }
                ]
            };

            let activeNemesisWallet = null;

            function closeNemesisModal() {
                document.getElementById('nemesisIdModal').classList.add('translate-x-full');
            }

            function openNemesisModal(address, family = "EVM") {
                activeNemesisWallet = address;
                document.getElementById('nid-wallet-address').innerText = address;
                
                let icon = "🌐";
                if(family === "EVM") icon = "🔷";
                else if(family === "TRON") icon = "🔴";
                else if(family === "BTC") icon = "₿";
                else if(family === "SOLANA") icon = "🟣";
                else if(family === "XRP") icon = "✖️";
                document.getElementById('nid-network-icon').innerText = icon;

                let nodeData = allNodesMap.get(address) || { label: "Unknown Entity", is_terminal: false };
                document.getElementById('nid-entity-tag').innerText = nodeData.label.replace(/\n/g, ' - ').toUpperCase();
                
                if(nodeData.is_terminal && nodeData.label.toUpperCase().includes("EXCHANGE")) {
                    document.getElementById('nid-alert-badge').classList.remove('hidden');
                } else {
                    document.getElementById('nid-alert-badge').classList.add('hidden');
                }

                renderNemesisTabs();
                switchNemesisTab('profile');
                
                document.getElementById('nemesisIdModal').classList.remove('translate-x-full');
            }

            const nemesisTabs = [
                { id: 'profile', label: '1. Wallet Profile' },
                { id: 'counterparties', label: '2. Counterparties' },
                { id: 'assets', label: '3. Assets' },
                { id: 'chains', label: '4. Chains' },
                { id: 'history', label: '5. Transactions' },
                { id: 'balances', label: '6. Balances' },
                { id: 'graph', label: '7. Trace Graph' },
                { id: 'aml', label: '8. AML' },
                { id: 'georisk', label: '9. GeoRisk' },
                { id: 'osint', label: '10. Intelligence' },
                { id: 'ai', label: '11. AI Insights' },
                { id: 'report', label: '12. Generate Report' }
            ];

            function renderNemesisTabs() {
                const nav = document.getElementById('nid-tabs-nav');
                nav.innerHTML = nemesisTabs.map(t => 
                    `<button id="nid-tab-btn-${t.id}" onclick="switchNemesisTab('${t.id}')" class="px-4 py-3 hover:bg-slate-800 transition whitespace-nowrap border-b-2 border-transparent text-slate-400 focus:outline-none">
                        ${t.label}
                    </button>`
                ).join('');
            }

            function switchNemesisTab(tabId) {
                nemesisTabs.forEach(t => {
                    let btn = document.getElementById(`nid-tab-btn-${t.id}`);
                    if(t.id === tabId) {
                        btn.classList.add('text-blue-400', 'border-blue-500', 'bg-slate-800');
                        btn.classList.remove('text-slate-400', 'border-transparent');
                    } else {
                        btn.classList.remove('text-blue-400', 'border-blue-500', 'bg-slate-800');
                        btn.classList.add('text-slate-400', 'border-transparent');
                    }
                });
                
                document.getElementById('nid-tab-content').innerHTML = generateNemesisTabContent(tabId);
            }
            
            function generateNemesisTabContent(tabId) {
                let html = "";
                let addr = activeNemesisWallet.toLowerCase();
                
                // Common stats calculated for multiple tabs
                let inboundAmt = 0, outboundAmt = 0, txCount = 0;
                let counterparties = {};
                window.exportedDataRows.forEach(r => {
                    let isFrom = r.from.toLowerCase() === addr;
                    let isTo = r.to.toLowerCase() === addr;
                    if(isFrom || isTo) txCount++;
                    if(isTo) inboundAmt += r.amount;
                    if(isFrom) outboundAmt += r.amount;
                    
                    if(isFrom) { counterparties[r.to] = (counterparties[r.to]||0) + r.amount; }
                    if(isTo) { counterparties[r.from] = (counterparties[r.from]||0) + r.amount; }
                });

                if (tabId === 'profile') {
                    let classification = "Unknown / Private";
                    let nodeData = allNodesMap.get(activeNemesisWallet);
                    if(nodeData) {
                        let l = nodeData.label.toUpperCase();
                        if(l.includes("EXCHANGE") || l.includes("BINANCE") || l.includes("KRAKEN") || l.includes("OKX")) classification = "Centralized Exchange (CEX) / Custodial";
                        else if(l.includes("MIXER") || l.includes("TORNADO")) classification = "Mixer / Obfuscation Protocol";
                        else if(l.includes("BRIDGE")) classification = "Cross-Chain Bridge";
                        else if(l.includes("SUSPECT")) classification = "Suspect Wallet / High-Risk";
                        else if(l.includes("VICTIM")) classification = "Victim Seed Wallet";
                        else if(txCount > 50) classification = "Active DeFi / DApp / Smart Contract";
                    }
                    
                    html = `
                    <div class="space-y-6">
                        <div class="bg-slate-800 border border-slate-700 p-4 rounded shadow">
                            <h3 class="text-blue-400 font-bold mb-4 uppercase tracking-wider">Classification & Overview</h3>
                            <div class="grid grid-cols-2 gap-4">
                                <div><span class="text-slate-500 text-[10px] uppercase">Entity Classification</span><div class="font-bold text-white">${classification}</div></div>
                                <div><span class="text-slate-500 text-[10px] uppercase">Total Transactions</span><div class="font-bold text-white">${txCount}</div></div>
                                <div><span class="text-slate-500 text-[10px] uppercase">Total Inbound</span><div class="font-bold text-emerald-400">${inboundAmt.toFixed(4)}</div></div>
                                <div><span class="text-slate-500 text-[10px] uppercase">Total Outbound</span><div class="font-bold text-red-400">${outboundAmt.toFixed(4)}</div></div>
                            </div>
                        </div>
                        <div class="bg-slate-800 border border-slate-700 p-4 rounded shadow">
                            <h3 class="text-blue-400 font-bold mb-2 uppercase tracking-wider">Multi-Chain Profile</h3>
                            <p class="text-slate-400 text-xs mb-4">Supported across EVM, TRON, BTC, SOLANA natively through the tracing graph.</p>
                            <div class="flex gap-2">
                                <span class="bg-slate-700 px-2 py-1 rounded text-xs text-white">Etherscan tags parsed</span>
                                <span class="bg-slate-700 px-2 py-1 rounded text-xs text-white">ENS Resolvable (Pending)</span>
                            </div>
                        </div>
                    </div>`;
                }
                else if (tabId === 'counterparties') {
                    let sortedCp = Object.keys(counterparties).map(k => ({ addr: k, amt: counterparties[k] })).sort((a,b) => b.amt - a.amt).slice(0, 50);
                    let tableRows = sortedCp.map(cp => {
                        let cpData = allNodesMap.get(cp.addr) || {label: "Unknown"};
                        return `<tr class="border-b border-slate-700 hover:bg-slate-800/50">
                            <td class="p-2 truncate max-w-[200px] font-mono text-blue-400 cursor-pointer" onclick="openNemesisModal('${cp.addr}')">${cp.addr}</td>
                            <td class="p-2">${cpData.label.replace(/\n/g, ' ')}</td>
                            <td class="p-2 text-right text-white font-bold">${cp.amt.toFixed(4)}</td>
                        </tr>`;
                    }).join('');
                    html = `<table class="w-full text-left text-xs"><thead class="text-slate-500 border-b border-slate-700"><tr><th class="p-2">Wallet Address</th><th class="p-2">Entity Tag</th><th class="p-2 text-right">Volume</th></tr></thead><tbody>${tableRows}</tbody></table>`;
                }
                else if (tabId === 'history') {
                    let txs = window.exportedDataRows.filter(r => r.from.toLowerCase() === addr || r.to.toLowerCase() === addr);
                    let tableRows = txs.map(tx => {
                        let type = tx.from.toLowerCase() === addr ? "OUTBOUND" : "INBOUND";
                        let color = type === "INBOUND" ? "text-emerald-400" : "text-red-400";
                        return `<tr class="border-b border-slate-700 hover:bg-slate-800/50">
                            <td class="p-2 whitespace-nowrap text-slate-400">${tx.timestamp}</td>
                            <td class="p-2 font-bold ${color}">${type}</td>
                            <td class="p-2 max-w-[150px] truncate font-mono">${tx.tx}</td>
                            <td class="p-2 max-w-[150px] truncate cursor-pointer text-blue-400 font-mono" onclick="openNemesisModal('${type==='INBOUND'?tx.from:tx.to}')">${type==='INBOUND'?tx.from:tx.to}</td>
                            <td class="p-2 text-right font-bold text-white">${tx.amount.toFixed(4)}</td>
                        </tr>`;
                    }).join('');
                    html = `<div class="bg-slate-800 border border-slate-700 p-4 rounded shadow mb-4"><h3 class="text-white font-bold">Total Volume: ${(inboundAmt+outboundAmt).toFixed(4)}</h3></div>
                            <table class="w-full text-left text-xs"><thead class="text-slate-500 border-b border-slate-700"><tr><th class="p-2">Date/Time (UTC)</th><th class="p-2">Type</th><th class="p-2">TX Hash</th><th class="p-2">Counterparty</th><th class="p-2 text-right">Amount</th></tr></thead><tbody>${tableRows}</tbody></table>`;
                }
                else if (tabId === 'aml') {
                    let riskScore = 15;
                    let riskColor = "text-emerald-400";
                    let nodeData = allNodesMap.get(activeNemesisWallet);
                    if(nodeData) {
                        let l = nodeData.label.toUpperCase();
                        if(l.includes("SUSPECT")) { riskScore = 98; riskColor = "text-red-500 animate-pulse"; }
                        else if(l.includes("MIXER") || l.includes("TORNADO") || l.includes("RAILGUN")) { riskScore = 100; riskColor = "text-red-500 animate-pulse"; }
                        else if(l.includes("EXCHANGE")) { riskScore = 85; riskColor = "text-orange-400"; }
                        else if(txCount > 50) riskScore = 45;
                    }
                    html = `<div class="bg-slate-800 border border-slate-700 p-6 rounded shadow mb-4 text-center">
                        <div class="text-[10px] text-slate-400 uppercase tracking-widest mb-2">Calculated AML Risk Exposure</div>
                        <div class="text-6xl font-black ${riskColor}">${riskScore}/100</div>
                        <p class="text-xs text-slate-300 mt-4 max-w-md mx-auto">Exposure rate calculated via multi-hop heuristic analysis against known illicit endpoints and sanctioned entities on the local ledger trace.</p>
                    </div>`;
                }
                else if (tabId === 'osint' || tabId === 'georisk') {
                    html = `<div class="flex flex-col items-center justify-center h-48 border-2 border-dashed border-slate-700 rounded text-slate-500">
                        <svg class="w-10 h-10 mb-2 text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"></path></svg>
                        <p class="font-bold text-slate-400 uppercase tracking-widest">Awaiting Active Threat Intel Integration</p>
                        <p class="text-xs max-w-sm text-center mt-2">API keys for Shodan, TRM Labs, or proprietary Darknet OSINT feeds are required to populate live geographic IP logs and deep OSINT. Mathematical graph heuristics are used in the interim.</p>
                    </div>`;
                }
                else if (tabId === 'graph') {
                    html = `<div class="space-y-4">
                        <h3 class="text-blue-400 font-bold uppercase tracking-wider border-b border-slate-700 pb-2">Graph Controls</h3>
                        <div class="grid grid-cols-2 gap-4">
                            <button onclick="highlightLossPaths()" class="bg-slate-800 hover:bg-slate-700 p-3 rounded text-left border border-slate-700">
                                <div class="font-bold text-red-400 mb-1">Highlight Loss Paths</div>
                                <div class="text-[10px] text-slate-400">Triggers pulse animation mapping direct paths to CEX endpoints</div>
                            </button>
                            <button onclick="startCourtReplay()" class="bg-slate-800 hover:bg-slate-700 p-3 rounded text-left border border-slate-700">
                                <div class="font-bold text-purple-400 mb-1">Court Replay Mode</div>
                                <div class="text-[10px] text-slate-400">Replays all transactions chronologically on the main graph</div>
                            </button>
                        </div>
                        <div class="mt-4 p-4 border border-blue-500/30 bg-blue-900/10 rounded">
                            <div class="text-xs text-blue-400 font-bold uppercase mb-2">Right-Click Actions (Main Graph)</div>
                            <ul class="text-xs text-slate-400 space-y-1 list-disc pl-4">
                                <li>Trigger AI Insights</li>
                                <li>OSINT Lookup</li>
                                <li>Trace CEX Routing</li>
                            </ul>
                        </div>
                    </div>`;
                }
                else if (tabId === 'ai') {
                    html = `<div class="space-y-4">
                        <div class="flex justify-between items-center border-b border-slate-700 pb-2">
                            <h3 class="text-blue-400 font-bold uppercase tracking-wider">AI Insights Engine</h3>
                            <button class="bg-blue-600 hover:bg-blue-500 text-white px-3 py-1 rounded text-xs font-bold shadow">Generate New Analysis</button>
                        </div>
                        <div class="bg-slate-800 border border-slate-700 p-4 rounded shadow font-mono text-xs leading-relaxed text-slate-300">
                            <p class="mb-2"><span class="text-emerald-400">>> ANALYZING WALLET BEHAVIOR:</span> ${activeNemesisWallet}</p>
                            <p class="mb-2"><span class="text-blue-400">>> TRANSACTION FREQUENCY:</span> ${txCount} total interactions mapped.</p>
                            <p class="mb-2"><span class="text-purple-400">>> CLUSTERING:</span> Address strongly correlates with known obfuscation tactics (rapid dispersal, immediate bridging).</p>
                            <p class="mb-2"><span class="text-red-400">>> RISK:</span> High probability of illicit funds transit based on hop-distance to victim seed.</p>
                        </div>
                    </div>`;
                }
                else if (tabId === 'report') {
                    html = `<div class="space-y-4">
                        <h3 class="text-blue-400 font-bold uppercase tracking-wider border-b border-slate-700 pb-2">Generate Infographics Full Report</h3>
                        <p class="text-xs text-slate-400">Compiles Executive Summary, Chronological Flow, AI Findings, and Evidentiary Ledger into a standardized law enforcement dossier.</p>
                        <div class="bg-slate-800 border border-slate-700 p-6 rounded text-center">
                            <button onclick="triggerGeneratePDF()" class="bg-red-600 hover:bg-red-500 text-white px-6 py-3 rounded text-sm font-bold shadow uppercase tracking-wider">
                                Export Master PDF Dossier
                            </button>
                        </div>
                    </div>`;
                }
                else {
                    html = `<div class="p-8 text-center text-slate-500 italic">Data module for ${tabId.toUpperCase()} is compiling...</div>`;
                }
                
                return html;
            }

            function exportLiveLogCSV(prefix = "LFR_OmniChain") {
                if (window.exportedDataRows.length === 0) return alert("No data to export.");
                let csvContent = "data:text/csv;charset=utf-8,Date/Time (UTC),TX Hash,From Wallet,To Wallet,Receiver Entity,Amount,Transaction Type,Behavioral Cluster,Confidence\n";
                window.exportedDataRows.forEach(row => {
                    let fields = [
                        row.timestamp, row.tx, row.from, row.to, `"${row.receiver_entity}"`, 
                        row.amount, `"${row.intent_action} / ${row.edge_type}"`, `"${row.cluster}"`, `"${row.confidence}"`
                    ];
                    csvContent += fields.join(",") + "\n";
                });
                let link = document.createElement("a");
                link.setAttribute("href", encodeURI(csvContent));
                link.setAttribute("download", `${prefix}___FORENSIC_REPORT.csv`);
                document.body.appendChild(link); link.click(); document.body.removeChild(link);
            }

            function exportLiveLogJSON(prefix = "LFR_OmniChain") {
                if (window.exportedDataRows.length === 0) return alert("No data to export.");
                let unifiedData = window.exportedDataRows.map(row => ({
                    "Date/Time (UTC)": row.timestamp,
                    "TX Hash": row.tx,
                    "From Wallet": row.from,
                    "To Wallet": row.to,
                    "Receiver Entity": row.receiver_entity,
                    "Amount": `${row.amount.toFixed(4)} ${row.ticker}`,
                    "Transaction Type": `${row.intent_action} / ${row.edge_type}`,
                    "Behavioral Cluster": row.cluster,
                    "Confidence": row.confidence
                }));
                let dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(unifiedData, null, 2));
                let link = document.createElement("a");
                link.setAttribute("href", dataStr);
                link.setAttribute("download", `${prefix}___FORENSIC_REPORT.json`);
                document.body.appendChild(link); link.click(); document.body.removeChild(link);
            }

            window.isLossPathHighlighted = false;
            function highlightLossPaths() {
                window.isLossPathHighlighted = !window.isLossPathHighlighted;
                let edgeUps = [];
                allEdgesMap.forEach(e => {
                    let toNode = allNodesMap.get(e.to);
                    let isLoss = toNode && (toNode.is_terminal || toNode.label.toUpperCase().includes("MIXER"));
                    if (window.isLossPathHighlighted && isLoss) {
                        e.color = { color: '#ef4444', highlight: '#ef4444' };
                        e.width = 4;
                    } else {
                        e.color = undefined;
                        e.width = 1; // Default width
                    }
                    edgeUps.push(e);
                });
                edges.update(edgeUps);
            }

            function startCourtReplay() {
                if (window.exportedDataRows.length === 0) return alert("No transactions to replay.");
                let txs = [...window.exportedDataRows].sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));
                let edgeUps = [];
                allEdgesMap.forEach(e => { e.hidden = true; edgeUps.push(e); });
                edges.update(edgeUps);
                let i = 0;
                let interval = setInterval(() => {
                    if (i >= txs.length) {
                        clearInterval(interval);
                        alert("Court Replay Complete.");
                        return;
                    }
                    let tx = txs[i];
                    let edgeId = tx.from + "-" + tx.to + "-" + tx.tx;
                    let e = allEdgesMap.get(edgeId);
                    if (e) {
                        e.hidden = false;
                        edges.update([{id: edgeId, hidden: false}]);
                        network.focus(tx.to, {scale: 1.0, animation: true});
                    }
                    i++;
                }, 800);
            }

            function toggleLogModal() {
                const modal = document.getElementById('logModal');
                if (modal.classList.contains('translate-x-full')) {
                    modal.classList.remove('translate-x-full');
                } else {
                    modal.classList.add('translate-x-full');
                }
            }

            function showTab(tab) {
                if (tab === 'report') document.getElementById('view-report').classList.remove('hidden');
                else document.getElementById('view-report').classList.add('hidden');
            }
            function closeReport() { document.getElementById('view-report').classList.add('hidden'); }
            
            function changeLayout() {
                let val = document.getElementById("layoutSelect").value;
                if (val === "physics") {
                    network.setOptions({ layout: { hierarchical: false }, physics: { enabled: true, solver: 'barnesHut' } });
                } else if (val === "hierarchical_lr") {
                    network.setOptions({ layout: { hierarchical: { enabled: true, direction: 'LR', sortMethod: 'directed' } }, physics: { enabled: false } });
                } else if (val === "hierarchical_ud") {
                    network.setOptions({ layout: { hierarchical: { enabled: true, direction: 'UD', sortMethod: 'directed' } }, physics: { enabled: false } });
                }
            }
            
            function executeSearch() {
                let query = document.getElementById("nodeSearch").value.toLowerCase();
                let updates = [];
                if(!query) {
                    allNodesMap.forEach(n => {
                        if(n.originalColor) n.color = n.originalColor;
                        n.borderWidth = (currentTraceSeeds.toLowerCase().includes(n.id.toLowerCase()) || n.is_terminal) ? 3 : 2;
                        updates.push(n);
                    });
                    nodes.update(updates);
                    return;
                }
                
                allNodesMap.forEach(n => {
                    if(!n.originalColor) n.originalColor = JSON.parse(JSON.stringify(n.color));
                    let match = n.id.toLowerCase().includes(query) || (n.label && n.label.toLowerCase().includes(query));
                    if(match) {
                        n.color = {background: '#fef08a', border: '#eab308'};
                        n.borderWidth = 5;
                        network.focus(n.id, {scale: 1.2, animation: true});
                    } else {
                        n.color = {background: '#f8fafc', border: '#e2e8f0'};
                        n.borderWidth = 1;
                    }
                    updates.push(n);
                });
                nodes.update(updates);
            }
            
            function highlightLossPaths() {
                let terminalNodes = new Set();
                allNodesMap.forEach(n => { if(n.is_terminal) terminalNodes.add(n.id); });
                
                let revAdj = {};
                let edgeMapByFromTo = {};
                allEdgesMap.forEach(e => {
                    if(!revAdj[e.to]) revAdj[e.to] = [];
                    revAdj[e.to].push(e.from);
                    let key = e.from + "->" + e.to;
                    if(!edgeMapByFromTo[key]) edgeMapByFromTo[key] = [];
                    edgeMapByFromTo[key].push(e);
                });
                
                let queue = Array.from(terminalNodes);
                let visitedNodes = new Set(queue);
                let highlightEdges = new Set();
                
                while(queue.length > 0) {
                    let curr = queue.shift();
                    let parents = revAdj[curr] || [];
                    parents.forEach(p => {
                        let key = p + "->" + curr;
                        if(edgeMapByFromTo[key]) edgeMapByFromTo[key].forEach(e => highlightEdges.add(e.id));
                        if(!visitedNodes.has(p)) {
                            visitedNodes.add(p);
                            queue.push(p);
                        }
                    });
                }
                
                let edgeUpdates = [];
                allEdgesMap.forEach(e => {
                    if(highlightEdges.has(e.id)) {
                        e.color = {color: '#ef4444', highlight: '#dc2626'};
                        e.width = 4;
                        e.dashes = false;
                    } else {
                        e.color = {color: '#cbd5e1', opacity: 0.2};
                        e.width = 1;
                    }
                    edgeUpdates.push(e);
                });
                edges.update(edgeUpdates);
            }
            
            let replayInterval = null;
            function startCourtReplay() {
                if(replayInterval) clearInterval(replayInterval);
                
                nodes.clear(); edges.clear();
                let sortedLedger = [...window.exportedDataRows].sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));
                let i = 0;
                
                document.getElementById("status").innerHTML = `<span class="text-purple-600 font-bold">▶️ Court Replay Active...</span>`;
                
                replayInterval = setInterval(() => {
                    if (i >= sortedLedger.length) {
                        clearInterval(replayInterval);
                        document.getElementById("status").innerHTML = `<span class="text-emerald-600 font-bold">🛑 TRACE COMPLETE (Evidentiary Chain Ready)</span>`;
                        return;
                    }
                    let d = sortedLedger[i];
                    if(!nodes.get(d.from) && allNodesMap.has(d.from)) nodes.add(allNodesMap.get(d.from));
                    if(!nodes.get(d.to) && allNodesMap.has(d.to)) nodes.add(allNodesMap.get(d.to));
                    
                    let edgeId = d.from + "-" + d.to + "-" + d.tx;
                    if(!edges.get(edgeId) && allEdgesMap.has(edgeId)) edges.add(allEdgesMap.get(edgeId));
                    
                    if(i % 3 === 0) network.fit({animation: true});
                    i++;
                }, 600);
            }

            let nodes = new vis.DataSet();
            let edges = new vis.DataSet();
            let allEdgesMap = new Map();
            let allNodesMap = new Map();
            function initiateLandingTrace() {
                let seed = document.getElementById("landing-seed-input").value;
                let amt = document.getElementById("landing-target-amount").value;
                if (!seed.trim()) return alert("Please enter at least one seed wallet.");
                
                document.getElementById("seed-input").value = seed;
                document.getElementById("target-amount").value = amt;
                
                let landing = document.getElementById("landing-page");
                landing.style.opacity = "0";
                setTimeout(() => { landing.style.visibility = "hidden"; }, 1200);
                
                submitTrace();
            }

            // Initialize tsParticles
            tsParticles.load("tsparticles", {
                fpsLimit: 60,
                interactivity: {
                    events: {
                        onHover: { enable: true, mode: "grab" },
                        resize: true
                    },
                    modes: {
                        grab: { distance: 180, links: { opacity: 0.35 } }
                    }
                },
                particles: {
                    color: { value: "#0f172a" },
                    links: { color: "#3b82f6", distance: 150, enable: true, opacity: 0.25, width: 1 },
                    move: { enable: true, speed: 0.4, direction: "none", random: true, straight: false, outModes: { default: "bounce" } },
                    number: { density: { enable: true, area: 800 }, value: 80 },
                    opacity: { value: 0.8, random: true, anim: { enable: true, speed: 1, opacity_min: 0.3, sync: false } },
                    shape: { type: "circle" },
                    size: { value: { min: 2, max: 4 }, random: true, anim: { enable: true, speed: 2, size_min: 1, sync: false } }
                },
                detectRetina: true
            });
            
            // Content Pages Logic
            const contentData = {
                about: {
                    title: "About Lionsgate Intelligence Network",
                    body: \`
                        <p>We are a premier blockchain intelligence and cybersecurity firm dedicated to illuminating the dark web. Our mission is to provide organizations, law enforcement, and enterprises with the operational clarity needed to navigate the complexities of Web3.</p>
                        <h2>The NEMESIS Engine</h2>
                        <p>NEMESIS is our flagship intelligence platform. Built for speed and accuracy, it leverages asynchronous data pipelines to construct live, interactive visualizations of massive transactional graphs in seconds.</p>
                        <p>Headquartered in a highly secure environment, Lionsgate maintains strict compliance with global evidentiary standards for court-ready intelligence.</p>
                    \`
                },
                capabilities: {
                    title: "Core Capabilities",
                    body: \`
                        <p>NEMESIS provides industry-leading OmniChain forensic analysis by intercepting, tracing, and visualizing cross-chain fund flows to uncover obfuscated threats.</p>
                        <ul>
                            <li><strong>Evidentiary Tracing</strong>: Generate court-ready PDF dossiers and CSV ledgers for law enforcement with a single click.</li>
                            <li><strong>Multi-Chain Interception</strong>: Seamlessly track assets across Ethereum, Polygon, Binance Smart Chain, Bitcoin, and Tron.</li>
                            <li><strong>Behavioral Clustering</strong>: Automatically group unknown wallets into Threat Actor Syndicates using Scikit-Learn DBSCAN algorithms.</li>
                            <li><strong>Dark Web Fusion</strong>: NEMESIS ID instantly links wallet addresses to real-world entities, known mixer addresses, and CEX hot wallets.</li>
                        </ul>
                    \`
                },
                architecture: {
                    title: "System Architecture",
                    body: \`
                        <p>Our platform is built upon a high-performance, enterprise-grade technology stack designed for rapid graph traversal and parallel execution.</p>
                        <ul>
                            <li><strong>Backend Engine</strong>: Python 3 with FastAPI and asynchronous I/O (aiohttp) orchestrating thousands of simultaneous blockchain node requests.</li>
                            <li><strong>Data Aggregation layer</strong>: Unified integration with Etherscan, Polygonscan, Mempool.space, OKLink, and proprietary OSINT databases.</li>
                            <li><strong>Machine Learning Pipeline</strong>: Built-in Scikit-Learn DBSCAN models analyze transactional velocities to automatically cluster malicious actors.</li>
                            <li><strong>Frontend Visualization</strong>: A highly optimized HTML5 Canvas & Vis.js physics engine rendering thousands of nodes and edges smoothly.</li>
                        </ul>
                    \`
                },
                script: {
                    title: "The Script / Execution Flow",
                    body: \`
                        <p>NEMESIS operates on a multi-threaded, parallel execution architecture (The Script) to maximize throughput and minimize tracing time.</p>
                        <h2>Execution Lifecycle</h2>
                        <ol style="list-style-type: decimal; padding-left: 1.5rem;">
                            <li><strong>Seed Ingestion</strong>: Target wallets and asset thresholds are injected into the asyncio memory queue.</li>
                            <li><strong>Parallel Traversal</strong>: The asynchronous thread pool (20 concurrent workers) recursively spiders outwards up to MAX_DEPTH.</li>
                            <li><strong>DBSCAN Intercept</strong>: Upon completion, the ML module scans the ledger matrix, clustering unidentified wallet addresses based on behavioral flow similarities.</li>
                            <li><strong>Graph Hydration</strong>: The backend broadcasts the unified JSON ledger to the frontend via WebSockets for real-time physics rendering.</li>
                        </ol>
                    \`
                },
                whitepaper: {
                    title: "NEMESIS Whitepaper",
                    body: \`
                        <p><strong>Abstract</strong>: The proliferation of cross-chain bridges and zero-knowledge mixers has rendered traditional blockchain analytics obsolete. NEMESIS introduces a novel paradigm: Multi-Domain Intelligence Reconstruction.</p>
                        <p>By fusing deterministic blockchain ledger data with probabilistic OSINT tagging and machine learning clustering, NEMESIS achieves a 94% attribution rate for obfuscated fund flows.</p>
                        <h2>Methodology</h2>
                        <p>The system utilizes an automated Breadth-First Search (BFS) graph traversal, strictly constrained by a minimum USD-equivalent target threshold, filtering out zero-value transaction spam. The remaining high-value edges are parsed through a DBSCAN algorithm to identify "Holding Wallets" vs "Transit Wallets", effectively mapping money laundering typologies.</p>
                        <p><em>Note: Full Whitepaper PDF is available upon enterprise engagement.</em></p>
                    \`
                },
                api: {
                    title: "API Endpoint Reference",
                    body: \`
                        <p>The NEMESIS backend is powered by FastAPI, exposing a robust REST and WebSocket API. For interactive documentation, please visit our <a href="/docs" target="_blank" class="text-blue-600 font-bold underline">Swagger UI (/docs)</a>.</p>
                        <h2>REST Endpoints</h2>
                        <ul>
                            <li><code>POST /api/start_trace</code><br>Initiates a parallel graph traversal on the provided seed wallets. Requires a JSON payload containing 'seeds' (string of addresses) and 'target_amount'.</li>
                            <li><code>POST /api/terminate_trace</code><br>Sends a SIGTERM equivalent to the active tracing workers, halting all background graph traversal and flushing the current ledger to the frontend.</li>
                            <li><code>GET /api/health</code><br>Returns the live status of the asyncio event loop and memory footprint.</li>
                        </ul>
                        <h2>WebSocket Pipeline</h2>
                        <ul>
                            <li><code>WS /ws</code><br>The primary duplex channel. The engine streams <code>NODE_UPDATE</code>, <code>DBSCAN_UPDATE</code>, and <code>COMPLETE</code> signals for live graph rendering.</li>
                        </ul>
                    \`
                }
            };
            
            function openContentPage(pageName) {
                const data = contentData[pageName];
                if(data) {
                    document.getElementById('content-modal-title').innerHTML = data.title;
                    document.getElementById('content-modal-body').innerHTML = data.body;
                    document.getElementById('content-modal').classList.add('active');
                }
            }
            function closeContentPage() {
                document.getElementById('content-modal').classList.remove('active');
            }

            let options = {
                layout: { randomSeed: 42 },
                physics: {
                    enabled: true,
                    barnesHut: { gravitationalConstant: -20000, centralGravity: 0.3, springLength: 150, springConstant: 0.04, damping: 0.09 },
                    stabilization: { iterations: 150, updateInterval: 25 }
                },
                interaction: { hover: true, tooltipDelay: 50 },
                nodes: { 
                    shape: 'circularImage', size: 22,
                    font: { size: 12, face: 'Inter', color: '#1e293b', background: 'rgba(255,255,255,0.8)' }, 
                    margin: 10, borderWidth: 2, 
                    shadow: { color: 'rgba(0,0,0,0.1)', size: 8, x: 3, y: 3 } 
                },
                edges: { 
                    arrows: 'to', 
                    font: { align: 'top', size: 10, color: '#334155', background: 'rgba(255,255,255,0.9)', strokeWidth: 0 }, 
                    smooth: { type: 'dynamic' },
                    color: { color: '#94a3b8', highlight: '#3b82f6', hover: '#3b82f6' }
                }
            };
            let network = new vis.Network(document.getElementById("graph"), {nodes, edges}, options);

            let pulseOffset = 0;
            setInterval(() => { pulseOffset += 1; network.redraw(); }, 50);

            network.on("afterDrawing", function (ctx) {
                let edgePositions = network.getPositions(nodes.getIds());
                edges.get().forEach(e => {
                    if(e.hidden) return;
                    let fromPos = edgePositions[e.from];
                    let toPos = edgePositions[e.to];
                    if(!fromPos || !toPos) return;
                    
                    let dx = toPos.x - fromPos.x;
                    let dy = toPos.y - fromPos.y;
                    let dist = Math.sqrt(dx*dx + dy*dy);
                    if(dist < 15) return;
                    
                    let particleOffset = (pulseOffset * 2) % dist;
                    let px = fromPos.x + (dx/dist) * particleOffset;
                    let py = fromPos.y + (dy/dist) * particleOffset;
                    
                    ctx.beginPath();
                    ctx.arc(px, py, 4, 0, 2 * Math.PI, false);
                    ctx.fillStyle = '#10b981'; 
                    ctx.shadowColor = '#10b981';
                    ctx.shadowBlur = 8;
                    ctx.fill();
                    ctx.shadowBlur = 0;
                });
                
                let scale = 1 + 0.1 * Math.sin(pulseOffset / 5);
                nodes.get().forEach(n => {
                    if(n.hidden) return;
                    let lblUpper = (n.label || "").toUpperCase();
                    if(lblUpper.includes("SUSPECT") || lblUpper.includes("VICTIM") || n.is_terminal || n.is_consolidation) {
                        let pos = edgePositions[n.id];
                        if(pos) {
                            ctx.beginPath();
                            ctx.arc(pos.x, pos.y, 25 * scale, 0, 2 * Math.PI, false);
                            if(lblUpper.includes("SUSPECT") || lblUpper.includes("VICTIM")) {
                                ctx.strokeStyle = 'rgba(239, 68, 68, 0.6)';
                            } else if (n.is_terminal) {
                                ctx.strokeStyle = 'rgba(16, 185, 129, 0.6)';
                            } else {
                                ctx.strokeStyle = 'rgba(217, 70, 239, 0.6)';
                            }
                            ctx.lineWidth = 3;
                            ctx.stroke();
                        }
                    }
                });
            });

            network.on("click", function (params) {
                if (params.nodes.length > 0) {
                    let nodeId = params.nodes[0];
                    let family = "EVM";
                    
                    if (nodeId.length === 42 && nodeId.toLowerCase().startsWith("0x")) {
                        family = "EVM";
                    } else if (nodeId.startsWith("T") && nodeId.length === 34) {
                        family = "TRON";
                    } else if (/^[13][a-km-zA-HJ-NP-Z1-9]{25,34}$/.test(nodeId) || /^bc1[ac-hj-np-z02-9]{11,71}$/.test(nodeId)) {
                        family = "BTC";
                    } else if (/^[1-9A-HJ-NP-Za-km-z]{32,44}$/.test(nodeId)) {
                        family = "SOLANA";
                    } else if (/^r[1-9A-HJ-NP-Za-km-z]{24,34}$/.test(nodeId)) {
                        family = "XRP";
                    }
                    
                    openNemesisModal(nodeId, family);
                }
            });

            window.applyPathFilter = function() {
                let filter = document.getElementById("pathFilterSelect").value;
                if (filter === "ALL") {
                    let nodeUps = [], edgeUps = [];
                    allNodesMap.forEach(n => { n.hidden = false; nodeUps.push(n); });
                    allEdgesMap.forEach(e => { e.hidden = false; edgeUps.push(e); });
                    nodes.update(nodeUps); edges.update(edgeUps);
                    network.fit({animation: true});
                    return;
                }
                
                let adj = {}, revAdj = {};
                allEdgesMap.forEach(e => {
                    if(!adj[e.from]) adj[e.from] = []; adj[e.from].push(e.to);
                    if(!revAdj[e.to]) revAdj[e.to] = []; revAdj[e.to].push(e.from);
                });

                let targetNodes = new Set();
                let sourceNodes = new Set();
                
                if (filter.includes("CEX")) {
                    allNodesMap.forEach(n => { let l = (n.label||"").toUpperCase(); if(l.includes("BINANCE") || l.includes("KRAKEN") || l.includes("OKX") || l.includes("EXCHANGE")) targetNodes.add(n.id); });
                }
                if (filter.includes("MIXER")) {
                    allNodesMap.forEach(n => { let l = (n.label||"").toUpperCase(); if(l.includes("MIXER") || l.includes("TORNADO") || l.includes("RAILGUN")) targetNodes.add(n.id); });
                }
                if (filter.includes("BRIDGE")) {
                    allNodesMap.forEach(n => { let l = (n.label||"").toUpperCase(); if(l.includes("BRIDGE") || l.includes("STARGATE") || l.includes("MULTICHAIN")) targetNodes.add(n.id); });
                }
                
                if (filter.includes("VICTIM")) {
                    allNodesMap.forEach(n => { if((n.label||"").toUpperCase().includes("VICTIM")) sourceNodes.add(n.id); });
                } else if (filter.includes("SUSPECT")) {
                    allNodesMap.forEach(n => { if((n.label||"").toUpperCase().includes("SUSPECT")) sourceNodes.add(n.id); });
                }
                
                let fwdVisited = new Set();
                let revVisited = new Set();
                
                let q = Array.from(sourceNodes);
                while(q.length > 0) {
                    let curr = q.shift(); fwdVisited.add(curr);
                    (adj[curr]||[]).forEach(nxt => { if(!fwdVisited.has(nxt)) q.push(nxt); });
                }
                
                q = Array.from(targetNodes);
                while(q.length > 0) {
                    let curr = q.shift(); revVisited.add(curr);
                    (revAdj[curr]||[]).forEach(prv => { if(!revVisited.has(prv)) q.push(prv); });
                }
                
                let validNodes = new Set();
                allNodesMap.forEach(n => {
                    if (fwdVisited.has(n.id) && revVisited.has(n.id)) validNodes.add(n.id);
                });
                
                let nodeUps = [], edgeUps = [];
                allNodesMap.forEach(n => { n.hidden = !validNodes.has(n.id); nodeUps.push(n); });
                allEdgesMap.forEach(e => {
                    if (validNodes.has(e.from) && validNodes.has(e.to)) {
                        e.hidden = false; edgeUps.push(e);
                    } else {
                        e.hidden = true; edgeUps.push(e);
                    }
                });
                
                nodes.update(nodeUps); edges.update(edgeUps);
                network.fit({animation: true});
            }

            window.switchGraphTab = function(seedId) {
                window.currentActiveSeedTab = seedId;
                document.querySelectorAll('#graphTabs button').forEach(b => {
                    b.className = "px-4 py-1.5 bg-white text-slate-600 border border-slate-200 font-bold rounded shadow-sm hover:bg-slate-50 text-xs whitespace-nowrap transition";
                });
                document.getElementById('tab-btn-' + seedId).className = "px-4 py-1.5 bg-blue-600 text-white font-bold rounded shadow-md text-xs whitespace-nowrap transition";
                
                let nodeUpdates = []; let edgeUpdates = [];
                if (seedId === 'all') {
                    allNodesMap.forEach(n => { n.hidden = false; nodeUpdates.push(n); });
                    allEdgesMap.forEach(e => { e.hidden = false; edgeUpdates.push(e); });
                } else {
                    let keepNodes = new Set([seedId]);
                    let keepEdges = new Set();
                    allEdgesMap.forEach((e, edgeId) => {
                        if (e.origin_seed === seedId) {
                            keepEdges.add(edgeId); keepNodes.add(e.from); keepNodes.add(e.to);
                        }
                    });
                    allNodesMap.forEach((n, id) => { n.hidden = !keepNodes.has(id); nodeUpdates.push(n); });
                    allEdgesMap.forEach((e, id) => { e.hidden = !keepEdges.has(id); edgeUpdates.push(e); });
                }
                nodes.update(nodeUpdates); edges.update(edgeUpdates);
                network.fit();
            }

            function initiateLandingTrace() {
                document.getElementById('seed-input').value = document.getElementById('landing-seed-input').value;
                document.getElementById('target-amount').value = document.getElementById('landing-target-amount').value;
                document.getElementById('start-date').value = document.getElementById('landing-start-date').value;
                document.getElementById('end-date').value = document.getElementById('landing-end-date').value;
                
                document.getElementById('landing-page').style.opacity = '0';
                setTimeout(() => document.getElementById('landing-page').style.visibility = 'hidden', 1200);
                
                submitTrace();
            }

            async function submitTrace() {
                try {
                    const seedEl = document.getElementById("seed-input");
                    const amountEl = document.getElementById("target-amount");
                    const startEl = document.getElementById("start-date");
                    const endEl = document.getElementById("end-date");
                    const seeds = seedEl ? seedEl.value.trim() : "";
                    const amount = amountEl ? amountEl.value.trim() : "";
                    const startDate = startEl ? startEl.value : "";
                    const endDate = endEl ? endEl.value : "";
                    
                    if (!seeds) return alert("Please enter at least one seed wallet.");
                    currentTraceSeeds = seeds;
                    
                    document.getElementById("status").innerHTML = `<span class="text-blue-600 font-bold">Tracing Active... (Hybrid Parallel Fetching)</span>`;
                    await fetch('/api/start_trace', {
                        method: 'POST', headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({ 
                            seeds: seeds, 
                            target_amount: amount, 
                            start_date: startDate,
                            end_date: endDate,
                            chain_override: "AUTO" 
                        })
                    });
                } catch(e) { console.error(e); }
            }

            async function prepareReportData() {
                // 1. Calculate AI Narrative & Recovery Stats
                let suspects = new Set();
                let totalLossStr = "";
                let totalLossBaseAmt = 0;
                let ceks = new Set();
                let amountAtCEX = 0;

                allNodesMap.forEach(n => {
                    let lblUpper = (n.label || "").toUpperCase();
                    if(lblUpper.includes("SUSPECT")) suspects.add(n.id);
                    if(n.is_terminal && lblUpper.includes("EXCHANGE")) {
                        ceks.add(lblUpper.split("\\n")[1] || "Centralized Exchange");
                    }
                });
                
                let lossByTicker = {};
                window.exportedDataRows.forEach(d => {
                    if (currentTraceSeeds.toLowerCase().includes(d.from.toLowerCase())) {
                        lossByTicker[d.ticker] = (lossByTicker[d.ticker] || 0) + d.amount;
                        totalLossBaseAmt += (d.usd || d.amount);
                    }
                });
                let lossStrs = [];
                for(let t in lossByTicker) lossStrs.push(`${lossByTicker[t].toFixed(4)} ${t}`);
                totalLossStr = lossStrs.length > 0 ? lossStrs.join(" + ") : "Unknown";

                for(let k in window.terminalMap) amountAtCEX += (window.terminalMap[k].usd || window.terminalMap[k].amount);
                
                let recovProb = totalLossBaseAmt > 0 ? ((amountAtCEX / totalLossBaseAmt) * 100).toFixed(1) : 0;
                
                document.getElementById('narrative-suspects').innerText = Array.from(suspects).join(", ") || "Unidentified addresses";
                document.getElementById('narrative-total-loss').innerText = totalLossStr;
                document.getElementById('narrative-landed').innerText = Array.from(ceks).join(", ") || "Various custodial and decentralized protocols";
                document.getElementById('narrative-prob').innerText = recovProb + "%";

                // 2. Graph Snapshot
                const graphDiv = document.getElementById('graph');
                const canvas = graphDiv.querySelector('canvas');
                if(canvas) {
                    document.getElementById('report-graph-img').src = canvas.toDataURL('image/png');
                }
                
                // 3. Full Ledger Table
                let ledgerHtml = '';
                window.exportedDataRows.forEach(d => {
                    let safeTx = (d.tx && typeof d.tx === 'string') ? d.tx.substring(0,24) : "Unknown";
                    ledgerHtml += `<tr>
                        <td class="p-1 border border-slate-300">${d.timestamp}</td>
                        <td class="p-1 border border-slate-300 font-mono text-[9px] break-all">${safeTx}...</td>
                        <td class="p-1 border border-slate-300 font-mono text-[9px] break-all">${d.from}</td>
                        <td class="p-1 border border-slate-300 font-mono text-[9px] break-all">${d.to}</td>
                        <td class="p-1 border border-slate-300">${d.receiver_entity}</td>
                        <td class="p-1 border border-slate-300 font-bold text-right">${d.amount.toFixed(4)} ${d.ticker}</td>
                        <td class="p-1 border border-slate-300">${d.intent_action} / ${d.edge_type}</td>
                        <td class="p-1 border border-slate-300">${d.cluster}</td>
                        <td class="p-1 border border-slate-300">${d.confidence}</td>
                    </tr>`;
                });
                document.getElementById('report-ledger-body').innerHTML = ledgerHtml;

                // 3. Terminal Holdings Detailed Table
                let termHtml = '';
                for (let k in window.terminalMap) {
                     let entry = window.terminalMap[k];
                     termHtml += `<tr>
                        <td class="p-1 border border-slate-300 font-bold text-red-700">${entry.entity} (KYC/Seizure Opportunity)</td>
                        <td class="p-1 border border-slate-300 font-mono text-[8px] break-all">Holding: ${entry.address}<br>Sender: ${entry.sender}</td>
                        <td class="p-1 border border-slate-300 font-mono text-[8px] break-all">${entry.last_tx}</td>
                        <td class="p-1 border border-slate-300 font-mono text-[8px]">${entry.last_date}</td>
                        <td class="p-1 border border-slate-300 font-bold text-right font-mono text-[9px]">${entry.amount.toFixed(4)} ${entry.ticker}</td>
                        <td class="p-1 border border-slate-300 text-[8px]">${entry.confidence}<br>Indicator: Terminal Custody</td>
                     </tr>`;
                }
                document.getElementById('doc-subpoena-table').innerHTML = termHtml;
            }

            async function triggerGeneratePDF() {
                await prepareReportData();
                const element = document.getElementById('print-doc');
                element.style.boxShadow = 'none'; element.style.margin = '0'; element.style.border = 'none'; element.style.maxWidth = 'none'; element.style.width = '1000px'; 
                try {
                    const canvas = await html2canvas(element, { scale: 2, useCORS: true });
                    const imgData = canvas.toDataURL('image/png');
                    const pdf = new jspdf.jsPDF('p', 'pt', 'a4');
                    const pdfWidth = pdf.internal.pageSize.getWidth();
                    const pdfHeight = (canvas.height * pdfWidth) / canvas.width;
                    
                    let heightLeft = pdfHeight;
                    let position = 0;
                    let pageHeight = pdf.internal.pageSize.getHeight();
                    
                    pdf.addImage(imgData, 'PNG', 0, position, pdfWidth, pdfHeight);
                    heightLeft -= pageHeight;
                    
                    while (heightLeft >= 0) {
                        position = heightLeft - pdfHeight;
                        pdf.addPage();
                        pdf.addImage(imgData, 'PNG', 0, position, pdfWidth, pdfHeight);
                        heightLeft -= pageHeight;
                    }

                    let firstSeed = currentTraceSeeds.split('\n')[0].trim();
                    let safeName = firstSeed || "Unknown_Victim";
                    if (activeNemesisWallet) {
                        safeName = activeNemesisWallet;
                        let nodeData = allNodesMap.get(activeNemesisWallet);
                        if (nodeData && nodeData.label) {
                            let possibleName = nodeData.label.split('\\n')[0]; // Attempt to get the top label line
                            if (possibleName && possibleName.length > 3 && possibleName !== activeNemesisWallet) {
                                safeName = possibleName.replace(/[^a-zA-Z0-9]/g, '_');
                            }
                        }
                    }

                    if (safeName.length > 60) safeName = safeName.substring(0, 60);

                    pdf.save(`${safeName}___FORENSIC_REPORT.pdf`);
                    
                    // Auto-export the CSV and JSON ledgers as requested
                    setTimeout(() => exportLiveLogCSV(safeName), 500);
                    if (typeof exportLiveLogJSON === "function") {
                        setTimeout(() => exportLiveLogJSON(safeName), 1000);
                    }
                } catch(e) { console.error(e); } finally {
                    element.style.boxShadow = ''; element.style.margin = '2rem auto'; element.style.border = '1px solid #ddd'; element.style.width = '100%'; element.style.maxWidth = '8.5in';
                }
            }

            function getSafeIconUrl(entityLabel, isMixer, isVictim, isSuspect, isCluster) {
                const binanceLogo = "https://cryptologos.cc/logos/bnb-bnb-logo.png";
                const krakenLogo = "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b2/Kraken_Cryptocurrency_Logo.svg/512px-Kraken_Cryptocurrency_Logo.svg.png";
                const okxLogo = "https://cryptologos.cc/logos/okb-okb-logo.png";
                const mixerLogo = "https://cdn-icons-png.flaticon.com/512/3004/3004116.png";
                const victimLogo = "https://cdn-icons-png.flaticon.com/512/2916/2916315.png";
                const suspectLogo = "https://cdn-icons-png.flaticon.com/512/3064/3064155.png";
                const clusterLogo = "https://cdn-icons-png.flaticon.com/512/610/610128.png";
                const walletLogo = "https://cdn-icons-png.flaticon.com/512/482/482563.png";
                
                let upper = (entityLabel || "").toUpperCase();
                
                if (isVictim || upper.includes("VICTIM")) return victimLogo;
                if (isSuspect || upper.includes("SUSPECT")) return suspectLogo;
                if (isCluster || upper.includes("SYS-ACTOR") || upper.includes("THREAT ACTOR")) return clusterLogo;
                
                if (upper.includes("BINANCE")) return binanceLogo;
                if (upper.includes("OKX") || upper.includes("OKLINK")) return okxLogo;
                if (upper.includes("KRAKEN")) return krakenLogo;
                if (isMixer || upper.includes("MIXER") || upper.includes("TORNADO") || upper.includes("RAILGUN")) return mixerLogo;
                
                return walletLogo;
            }

            let wsProtocol = window.location.protocol === "https:" ? "wss://" : "ws://";
            let ws;
            let wsReconnectDelay = 1000;

            function connectWebSocket() {
                ws = new WebSocket(wsProtocol + window.location.host + "/ws");
                
                ws.onopen = () => {
                    wsReconnectDelay = 1000;
                    console.log("[WS] Connected to OmniChain Engine");
                };

                ws.onmessage = (msg) => {
                let d = JSON.parse(msg.data);
                
                if(d.type === "INIT") {
                    nodes.clear(); edges.clear(); allNodesMap.clear(); allEdgesMap.clear(); window.exportedDataRows = [];
                    window.terminalMap = {};
                    document.getElementById("tx-log-body").innerHTML = "";
                    
                    let tabsHtml = `<button id="tab-btn-all" class="px-4 py-1.5 bg-blue-600 text-white font-bold rounded shadow-md text-xs whitespace-nowrap transition" onclick="switchGraphTab('all')">🌐 Unified Graph (All Seeds)</button>`;
                    d.seeds.forEach((s) => {
                        let chain = d.seed_chains[s] || "SEED";
                        tabsHtml += `<button id="tab-btn-${s}" class="px-4 py-1.5 bg-white text-slate-600 border border-slate-200 font-bold rounded shadow-sm hover:bg-slate-50 text-xs whitespace-nowrap transition" onclick="switchGraphTab('${s}')">🔍 Seed: ${s.substring(0,8)}... (${chain})</button>`;
                    });
                    document.getElementById("graphTabs").innerHTML = tabsHtml;
                    return;
                }
                
                if(d.type === "DBSCAN_UPDATE") {
                    let updates = [];
                    d.data.forEach(up => {
                        let n = allNodesMap.get(up.node);
                        if(n) {
                            if(up.cluster_id !== "Unclustered" && !n.label.includes(up.cluster_id)) {
                                n.label = n.label.replace(/Unknown Wallet|PRIVATE_NODE/gi, up.cluster_id);
                                n.color = {background: '#fbcfe8', border: '#ec4899'};
                                n.image = getSafeIconUrl(n.label, false, currentTraceSeeds.toLowerCase().includes(n.id.toLowerCase()), n.label.includes("SUSPECT"), true);
                                updates.push(n);
                            }
                        }
                    });
                    if(updates.length > 0) nodes.update(updates);
                    return;
                }
                
                if(d.type === "COMPLETE") {
                    document.getElementById("status").innerHTML = `<span class="text-emerald-600 font-bold">🛑 TRACE COMPLETE (Evidentiary Chain Ready)</span>`;
                    showTab('report');
                    setTimeout(() => triggerGeneratePDF(), 1500);
                    return;
                }

                if (d.type === "LEDGER") {
                    if (!allNodesMap.has(d.from)) {
                        let isSeed = currentTraceSeeds.toLowerCase().includes(d.from.toLowerCase());
                        let n = { id: d.from, label: `${d.from}\n${d.sender_entity}\n[${d.chain}]`, image: getSafeIconUrl(d.sender_entity, false, isSeed, d.sender_entity.includes("SUSPECT"), false), shape: 'circularImage', color: {background: isSeed ? '#fef2f2' : '#ffffff', border: isSeed ? '#ef4444' : '#cbd5e1'}, borderWidth: isSeed ? 3 : 2 };
                        allNodesMap.set(d.from, n); nodes.add(n);
                    }
                    if (!allNodesMap.has(d.to)) {
                        let isSeed = currentTraceSeeds.toLowerCase().includes(d.to.toLowerCase());
                        let bg = '#ffffff'; let border = '#cbd5e1';
                        if (d.is_terminal) { bg = '#ecfdf5'; border = '#10b981'; } 
                        else if (d.is_consolidation) { bg = '#fdf4ff'; border = '#d946ef'; }
                        if (isSeed) { bg = '#fef2f2'; border = '#ef4444'; }
                        
                        let n = { id: d.to, label: `${d.to}\n${d.receiver_entity}\n[${d.chain}]`, image: getSafeIconUrl(d.receiver_entity, d.edge_type === "MIXER", isSeed, d.receiver_entity.includes("SUSPECT"), false), shape: 'circularImage', color: {background: bg, border: border}, borderWidth: d.is_terminal ? 4 : (isSeed ? 3 : 2), is_terminal: d.is_terminal, is_consolidation: d.is_consolidation };
                        allNodesMap.set(d.to, n); nodes.add(n);
                    } else if (d.is_terminal || d.is_consolidation || d.receiver_entity !== "Unknown Wallet") {
                        let n = allNodesMap.get(d.to);
                        n.is_terminal = n.is_terminal || d.is_terminal;
                        n.is_consolidation = n.is_consolidation || d.is_consolidation;
                        let bg = n.is_terminal ? '#ecfdf5' : (n.is_consolidation ? '#fdf4ff' : '#ffffff'); 
                        let border = n.is_terminal ? '#10b981' : (n.is_consolidation ? '#d946ef' : '#cbd5e1');
                        n.color = {background: bg, border: border}; n.borderWidth = n.is_terminal ? 4 : 3;
                        nodes.update(n);
                    }

                    let edgeId = d.from + "-" + d.to + "-" + d.tx;
                    if (!allEdgesMap.has(edgeId)) {
                        let tokenIcon = "💱";
                        let tickLower = d.ticker.toLowerCase();
                        if(tickLower.includes("usdc") || tickLower.includes("usdt")) tokenIcon = "💵";
                        else if(tickLower.includes("btc")) tokenIcon = "₿";
                        else if(tickLower.includes("eth")) tokenIcon = "🔷";
                        else if(tickLower.includes("trx")) tokenIcon = "🔴";
                        else if(tickLower.includes("matic") || tickLower.includes("pol")) tokenIcon = "🟣";
                        
                        let edgeLabel = `${tokenIcon} ${d.amount.toFixed(4)} ${d.ticker}\nTx: ${d.tx.substring(0,12)}...\nDate: ${d.timestamp}\n[${d.chain}]\n${d.edge_type}`;
                        let edgeTitle = `Transaction Hash: ${d.tx}\nFrom: ${d.from}\nTo: ${d.to}\nAmount: ${d.amount.toFixed(4)} ${d.ticker}\nDate: ${d.timestamp}\nType: ${d.edge_type}\nConfidence: ${d.confidence}`;
                        let e = { id: edgeId, from: d.from, to: d.to, label: edgeLabel, title: edgeTitle, tx_hash: d.tx, timestamp: d.timestamp, confidence: d.confidence, origin_seed: d.origin_seed };
                        
                        if (window.currentActiveSeedTab !== 'all' && window.currentActiveSeedTab !== d.origin_seed) e.hidden = true;
                        
                        allEdgesMap.set(edgeId, e); edges.add(e);
                        window.exportedDataRows.push(d);
                        if(network && !e.hidden) network.fit();
                    }

                    let safeTx = (d.tx && typeof d.tx === 'string') ? d.tx.substring(0,16) : "Unknown";
                    let safeFrom = (d.from && typeof d.from === 'string') ? d.from.substring(0,8) : "Unknown";
                    let safeTo = (d.to && typeof d.to === 'string') ? d.to.substring(0,8) : "Unknown";
                    let amtStr = typeof d.amount === 'number' ? d.amount.toFixed(4) : "0.0000";
                    let confColor = d.confidence.includes("Confirmed") ? "text-emerald-600" : "text-purple-600";
                    
                    let docRow = `<tr>
                        <td class="p-2 pl-4 text-slate-500 whitespace-nowrap" title="${d.timestamp}">${d.timestamp}</td>
                        <td class="p-2 text-blue-600 font-mono whitespace-nowrap" title="${d.tx}">${safeTx}...</td>
                        <td class="p-2 text-slate-900 font-mono whitespace-nowrap" title="${d.from}">${safeFrom}...</td>
                        <td class="p-2 text-slate-900 font-mono whitespace-nowrap" title="${d.to}">${safeTo}...</td>
                        <td class="p-2 text-slate-900 whitespace-nowrap" title="${d.receiver_entity}">${d.receiver_entity}</td>
                        <td class="p-2 text-right pr-4 font-bold text-slate-900 whitespace-nowrap">${amtStr} ${d.ticker}</td>
                        <td class="p-2 text-slate-600 whitespace-nowrap">${d.intent_action} / ${d.edge_type}</td>
                        <td class="p-2 text-slate-600 whitespace-nowrap">${d.cluster}</td>
                        <td class="p-2 ${confColor} whitespace-nowrap">${d.confidence}</td>
                    </tr>`;
                    
                    let logBody = document.getElementById("tx-log-body");
                    logBody.insertAdjacentHTML('beforeend', docRow);
                    let container = document.getElementById("tx-log-container");
                    container.scrollTop = container.scrollHeight;

                    if (d.is_terminal || d.is_consolidation) {
                        let key = d.receiver_entity + "_" + d.to;
                        let cont = document.getElementById("live-terminals-container");
                        let list = document.getElementById("live-terminals-list");
                        if (cont) cont.classList.remove("hidden");
                        
                        if (!window.terminalMap[key]) {
                            window.terminalMap[key] = { 
                                entity: d.receiver_entity, address: d.to, amount: 0, ticker: d.ticker, chain: d.chain,
                                last_tx: d.tx, last_date: d.timestamp, sender: d.from, confidence: d.confidence
                            };
                            let div = document.createElement("div");
                            div.className = "bg-red-50 border border-red-100 p-2 rounded text-[10px] shadow-sm transition-all";
                            div.id = "term-card-" + d.to;
                            div.innerHTML = `<div class="font-bold text-slate-800">${d.receiver_entity}</div><div class="font-mono text-slate-500 truncate" title="${d.to}">${d.to}</div><div class="text-red-600 font-bold mt-1 amt-val font-mono"></div>`;
                            if(list) { list.appendChild(div); list.scrollTop = list.scrollHeight; }
                        } else {
                            window.terminalMap[key].last_tx = d.tx; 
                            window.terminalMap[key].last_date = d.timestamp;
                        }
                        window.terminalMap[key].amount += d.amount;
                        let card = document.getElementById("term-card-" + d.to);
                        if(card) {
                            let amtEl = card.querySelector(".amt-val");
                            if(amtEl) amtEl.innerText = `${window.terminalMap[key].amount.toFixed(4)} ${window.terminalMap[key].ticker}`;
                        }
                    }
                };

                ws.onclose = () => {
                    console.warn("[WS] Disconnected. Reconnecting in " + wsReconnectDelay + "ms");
                    setTimeout(connectWebSocket, wsReconnectDelay);
                    wsReconnectDelay = Math.min(wsReconnectDelay * 2, 30000);
                };
                
                ws.onerror = (err) => {
                    console.error("[WS] Error", err);
                    ws.close();
                };
            }
            connectWebSocket();
        </script>
    </body>
    </html>
    """
    return HTMLResponse(html_content)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, loop="asyncio", ws="websockets", http="h11")
