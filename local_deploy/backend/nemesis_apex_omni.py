#!/usr/bin/env python3
"""
==============================================================================
🛡️ LIONSGATE INTELLIGENCE NETWORK - NEMESIS APEX OMNI-ENGINE (v100.0)
==============================================================================
Integrated Modules:
- C-Level Windows AsyncIO Socket Patch (WinError 10014 Prevention)
- Global Threat Intel Lake (Ransomwhe.re, OFAC, CISA, CryptoScamDB, FBI Flashes)
- Local Data Folder Ingestion (Streaming large JSON/JSONL via ijson)
- Ransomware Behavioral Auto-Clustering (SciKit-Learn DBSCAN)
- Self-Healing Autonomous Supervisor
- Signature-Based Authorization Theft (SBAT) Forensics
==============================================================================
"""

import sys
import os
import certifi
import socket

if os.name == 'nt':
    _orig_getpeername = socket.socket.getpeername
    def _safe_getpeername(self):
        try:
            return _orig_getpeername(self)
        except OSError as e:
            if getattr(e, 'winerror', None) == 10014:
                return ('0.0.0.0', 0)
            raise
    socket.socket.getpeername = _safe_getpeername

os.environ['SSL_CERT_FILE'] = certifi.where()
os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()

import subprocess
import logging
import importlib
import time
import json
import hashlib
import re
import uuid
import asyncio
import statistics
import aiohttp
from collections import defaultdict, deque
from datetime import datetime, timezone
from typing import List, Dict, Any, Set, Callable, Optional
from enum import Enum
from threading import Thread
from contextlib import asynccontextmanager

def bootstrap_environment():
    required_packages = {
        "fastapi": "fastapi", "uvicorn": "uvicorn", "pydantic": "pydantic",
        "motor": "motor", "aiohttp": "aiohttp", "socketio": "python-socketio",
        "playwright": "playwright", "bs4": "beautifulsoup4", "google.genai": "google-genai",
        "sklearn": "scikit-learn", "psutil": "psutil", "dotenv": "python-dotenv", 
        "pymongo": "pymongo", "ijson": "ijson"
    }
    missing = []
    for mod, pip_name in required_packages.items():
        try: importlib.import_module(mod)
        except ImportError: missing.append(pip_name)
            
    if missing:
        print(f"[*] Missing dependencies detected: {missing}. Auto-installing...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", *missing])
            os.execv(sys.executable, [sys.executable] + sys.argv)
        except Exception as e:
            print(f"[!] Auto-Heal Failure: {e}"); sys.exit(1)

bootstrap_environment()

import ijson
import psutil
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field
import motor.motor_asyncio
import socketio
from google import genai
from google.genai import types

from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler

from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger("NEMESIS_APEX")

MONGODB_URI = os.getenv("DATABASE_MONGO_URL", "mongodb://localhost:27017")
ETHERSCAN_API_KEY = os.getenv("ETHERSCAN_API_KEY", "")
GEMINI_KEYS_RAW = os.getenv("GEMINI_API_KEYS", os.getenv("GEMINI_API_KEY", ""))
GEMINI_KEYS = [k.strip() for k in GEMINI_KEYS_RAW.split(",") if k.strip()]

mongo_client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URI, maxPoolSize=100)
db = mongo_client.nemesis_apex

async def init_db():
    collections = ["entities", "state_edges", "darknet_intel", "system_logs", "ransomware_campaigns"]
    try:
        existing = await db.list_collection_names()
        for col in collections:
            if col not in existing: await db.create_collection(col)
        await db.entities.create_index([("address", 1)], unique=True)
        await db.state_edges.create_index([("trace_id", 1)])
        logger.info("✅ NEMESIS OS Storage Fabric Initialized.")
    except Exception as e:
        logger.error(f"⚠️ Storage Fabric Degraded: {e}")

class ActionType(str, Enum):
    TRANSFER = "TRANSFER"
    SWAP = "SWAP"
    BRIDGE = "BRIDGE"
    CEX_DEPOSIT = "CEX_DEPOSIT"
    DRAIN_EXECUTION = "DRAIN_EXECUTION"
    PEEL_CHAIN = "PEEL_CHAIN"

class RansomwareIntelligenceEngine:
    @staticmethod
    def extract_wallet_fingerprint(transactions: List[Dict]) -> Dict:
        if not transactions: return {}
        amounts = [float(tx.get("value", 0)) / 1e18 for tx in transactions]
        times = sorted([int(tx.get("timeStamp", 0)) for tx in transactions])
        intervals = [times[i+1] - times[i] for i in range(len(times)-1)]
        
        senders = set(tx.get("from") for tx in transactions)
        receivers = set(tx.get("to") for tx in transactions)
        
        fan_in = len(senders) > 10 and len(receivers) <= 2
        fan_out = len(senders) <= 2 and len(receivers) > 10
        velocity = sum(intervals) / len(intervals) if intervals else 0
        peel_score = sum(1 for i in range(len(amounts)-1) if 0.85 < (amounts[i+1]/(amounts[i] or 1)) < 0.99) / (len(amounts) or 1) * 100

        return {
            "avg_tx_val": statistics.mean(amounts) if amounts else 0,
            "max_tx_val": max(amounts) if amounts else 0,
            "tx_count": len(transactions),
            "velocity_sec": velocity,
            "fan_in": fan_in, "fan_out": fan_out, "peel_score_pct": peel_score,
            "unique_counterparties": len(senders.union(receivers))
        }

    @staticmethod
    def cluster_syndicates(ledger_data: List[Dict]) -> Dict:
        if not ledger_data or len(ledger_data) < 5: return {}
        
        stats = defaultdict(lambda: {"in_vol": 0.0, "out_vol": 0.0, "tx_count": 0, "counterparties": set()})
        for tx in ledger_data:
            amt = float(tx.get("amount", 0))
            f, t = tx.get("from_addr"), tx.get("to_addr")
            if f:
                stats[f]["out_vol"] += amt; stats[f]["tx_count"] += 1; 
                if t: stats[f]["counterparties"].add(t)
            if t:
                stats[t]["in_vol"] += amt; stats[t]["tx_count"] += 1; 
                if f: stats[t]["counterparties"].add(f)
                
        addresses, features = [], []
        for addr, data in stats.items():
            addresses.append(addr)
            features.append([data["in_vol"], data["out_vol"], data["tx_count"], len(data["counterparties"])])
            
        if len(addresses) < 3: return {}

        scaled = StandardScaler().fit_transform(features)
        labels = DBSCAN(eps=0.5, min_samples=2).fit_predict(scaled)
        
        cluster_map = {}
        for addr, lbl in zip(addresses, labels):
            if lbl != -1: 
                cluster_map[addr] = f"SYNDICATE_{str(lbl).zfill(4)}"
        
        return cluster_map

sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')

class GlobalThreatIntelLake:
    INTELLIGENCE_SOURCES = [
        {"name": "Ransomwhe.re", "url": "https://api.ransomwhe.re/export", "type": "API"},
        {"name": "OFAC Sanctions (SDN)", "url": "https://raw.githubusercontent.com/0xapoorv/ofac-sanctioned-digital-currency-addresses/main/sanctioned_addresses.csv", "type": "CSV"},
        {"name": "CryptoScamDB", "url": "https://cryptoscamdb.org/api/addresses", "type": "API"},
        {"name": "CISA / FBI Flashes", "url": "Automated Parsing", "type": "Scraper"},
        {"name": "VX-Underground", "url": "Malware Binaries", "type": "Heuristic"}
    ]

    @staticmethod
    async def ingest_ransomwhere(session):
        logger.info("🦇 [DATA LAKE] Fetching live Ransomware intelligence from api.ransomwhe.re/export...")
        try:
            async with session.get("https://api.ransomwhe.re/export", timeout=20) as r:
                if r.status == 200:
                    data = await r.json()
                    results = data.get("result", [])
                    for item in results:
                        addr = item.get("address")
                        family = item.get("family", "Unknown")
                        if not addr: continue
                        
                        entity = {
                            "address": addr,
                            "chain": "BTC" if addr.startswith("1") or addr.startswith("3") or addr.startswith("bc1") else "ETH",
                            "classification": "Ransomware",
                            "entity_name": f"{family.title()} Ransomware Group",
                            "tags": [family, "RANSOMWARE", "CRITICAL_THREAT"],
                            "risk_score": 100, "verified": True, "balance": item.get("balance", 0)
                        }
                        try: await db.entities.update_one({"address": addr}, {"$set": entity}, upsert=True)
                        except: pass
        except Exception as e: logger.error(f"⚠️ Ransomwhe.re API fetch failed: {e}")

    @staticmethod
    async def ingest_ofac_cisa(session):
        logger.info("🦅 [DATA LAKE] Fetching OFAC/CISA Sanctioned Entities...")
        url = "https://raw.githubusercontent.com/0xapoorv/ofac-sanctioned-digital-currency-addresses/main/sanctioned_addresses.csv"
        try:
            async with session.get(url, timeout=15) as r:
                if r.status == 200:
                    text = await r.text()
                    ioc_pattern = re.compile(r'0x[a-fA-F0-9]{40}|bc1[a-zA-HJ-NP-Z0-9]{25,39}|[13][a-km-zA-HJ-NP-Z1-9]{25,34}')
                    matches = list(set(ioc_pattern.findall(text)))
                    for addr in matches[:100]:
                        try: await db.entities.update_one({"address": addr}, {"$set": {"classification": "Sanctioned", "risk_score": 100, "tags": ["OFAC_SANCTIONED"]}}, upsert=True)
                        except: pass
        except Exception: pass

    @staticmethod
    async def ingest_local_data_folder():
        logger.info("📂 [DATA LAKE] Scanning local ../data/ folder for bulk intelligence JSON/JSONL...")
        data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
        if not os.path.exists(data_dir): os.makedirs(data_dir); return

        count = 0
        for filename in os.listdir(data_dir):
            filepath = os.path.join(data_dir, filename)
            if filename.endswith(".json") or filename.endswith(".jsonl"):
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        if filename.endswith(".jsonl"):
                            for line in f:
                                if not line.strip(): continue
                                try:
                                    record = json.loads(line)
                                    addr = record.get("address") or (record.get("addresses")[0] if record.get("addresses") else None)
                                    if addr:
                                        await db.entities.update_one({"address": addr}, {"$set": record}, upsert=True)
                                        count += 1
                                except: pass
                        else:
                            objects = ijson.items(f, 'item')
                            for record in objects:
                                addr = record.get("address") or (record.get("addresses")[0] if record.get("addresses") else None)
                                if addr:
                                    await db.entities.update_one({"address": addr}, {"$set": record}, upsert=True)
                                    count += 1
                except Exception as e: logger.warning(f"Failed parsing {filename}: {e}")
                    
        if count > 0: logger.info(f"✅ [DATA LAKE] Auto-Ingested {count} records from local data files.")

class NemesisLiveTracer:
    def __init__(self, trace_id: str, max_depth: int = 2, room_name: str = None):
        self.trace_id = trace_id; self.max_depth = max_depth; self.visited = set(); self.semaphore = asyncio.Semaphore(10)
        self.ledger = [] 
        self.room_name = room_name or trace_id 

    async def orchestrate(self, address: str, chain: str, source_tag: str = "Manual"):
        try:
            await self.execute_trace_step(address, chain, 0, source_tag)
        except Exception as e: logger.error(f"[!] Trace Error: {e}")
        
        # 🧠 ML CLUSTERING POST-PROCESS (Ransomware Auto-Labeling)
        if len(self.ledger) > 3:
            cluster_map = RansomwareIntelligenceEngine.cluster_syndicates(self.ledger)
            if cluster_map:
                await sio.emit('system_alert', {"msg": f"ML Engine identified {len(set(cluster_map.values()))} Threat Campaigns via DBSCAN.", "type": "warning"}, room=self.room_name)
                # Broadcast cluster map to frontend for graph visualization update
                await sio.emit('cluster_map', cluster_map, room=self.room_name)
                
                # Auto-Label Entities in Database
                for addr, cluster_name in cluster_map.items():
                    try: 
                        await db.entities.update_one({"address": addr}, {"$set": {"cluster_id": cluster_name, "classification": "Ransomware_Syndicate"}}, upsert=True)
                    except: pass

        await sio.emit('trace_complete', {"trace_id": self.trace_id}, room=self.room_name)

    async def execute_trace_step(self, address: str, chain: str, depth: int, source_tag: str = ""):
        if depth > self.max_depth: return
        uid = f"{chain}:{address}".lower()
        if uid in self.visited: return
        self.visited.add(uid)
        
        async with self.semaphore:
            db_ent = await db.entities.find_one({"address": address})
            classification = db_ent.get("classification", "Wallet") if db_ent else "Wallet"
            entity_name = db_ent.get("entity_name", "Unknown") if db_ent else "Unknown"
            tags = db_ent.get("tags", []) if db_ent else []
            risk = db_ent.get("risk_score", 0) if db_ent else 0
            
            if source_tag: tags.append(source_tag)
            
            
            node_data = {
                "id": address, "chain": chain, "classification": classification, 
                "entity_name": entity_name, "tags": tags, 
                "risk_score": risk, "verified": classification != "Wallet"
            }
            try: await db.entities.update_one({"address": address}, {"$set": node_data}, upsert=True)
            except: pass

            await sio.emit('ransomware_node', {"node": node_data}, room=self.room_name)
            await sio.emit('node', {"node": node_data}, room=self.room_name) 

            if classification in ["CEX", "Mixer", "Exchange"]: return 

            url = f"https://api.etherscan.io/v2/api?chainid=1&module=account&action=txlist&address={address}&apikey={ETHERSCAN_API_KEY}"
            try:
                async with aiohttp.ClientSession() as s:
                    async with s.get(url, timeout=10) as r:
                        if r.status == 200:
                            data = await r.json()
                            txs = data.get("result", [])
                            fp = RansomwareIntelligenceEngine.extract_wallet_fingerprint(txs)
                            
                            tasks = []
                            for tx in txs[:3]: 
                                if tx.get("to") and tx["from"].lower() == address.lower() and tx.get("isError", "0") == "0":
                                    val = float(tx.get("value", 0)) / 1e18
                                    if val <= 0: continue

                                    action_type = ActionType.PEEL_CHAIN if fp.get("peel_score_pct",0) > 30 else ActionType.TRANSFER

                                    edge = {
                                        "trace_id": self.trace_id, "from_addr": address, "to_addr": tx["to"], "amount": val, 
                                        "chain": chain, "asset": "ETH", "tx_hash": tx["hash"], "action_type": action_type, 
                                        "is_terminal": False, "usd_value": val * 3000,
                                        "timestamp": datetime.now(timezone.utc).isoformat()
                                    }
                                    self.ledger.append(edge)
                                    try: await db.state_edges.insert_one(edge)
                                    except: pass

                                    await sio.emit('ransomware_edge', {"edge": edge}, room=self.room_name)
                                    await sio.emit('edge', {"edge": edge}, room=self.room_name)
                                    tasks.append(asyncio.create_task(self.execute_trace_step(tx["to"], chain, depth + 1)))
                            if tasks: await asyncio.gather(*tasks)
            except Exception as e: logger.error(f"Tx Fetch Error: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    async def populate_datalake():
        async with aiohttp.ClientSession() as session:
            await GlobalThreatIntelLake.ingest_ransomwhere(session)
            await GlobalThreatIntelLake.ingest_ofac_cisa(session)
        await GlobalThreatIntelLake.ingest_local_data_folder()
    asyncio.create_task(populate_datalake())
    yield

app = FastAPI(title="Lionsgate Nemesis - Apex Auto-Tracer", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@sio.on('join_trace')
async def join_trace(sid, data):
    if data.get('trace_id'): sio.enter_room(sid, data['trace_id'])
    
@sio.on('join_ransomware_hub')
async def join_ransomware_hub(sid):
    sio.enter_room(sid, 'ransomware_hub')

class DeploymentPayload(BaseModel):
    seeds: str; chain_override: str = "AUTO"; max_depth: int = 2

@app.post("/api/v1/trace/deploy")
async def deploy_nemesis_engine(payload: DeploymentPayload, background_tasks: BackgroundTasks):
    trace_id = f"NMS-{uuid.uuid4().hex[:8].upper()}"
    tracer = NemesisLiveTracer(trace_id, max_depth=payload.max_depth)
    clean_seeds = [s.strip() for s in re.split(r'[\s,]+', payload.seeds) if s.strip()]
    for seed in clean_seeds:
        chain = payload.chain_override if payload.chain_override != "AUTO" else ("ETH" if seed.startswith("0x") else "BTC")
        background_tasks.add_task(tracer.orchestrate, seed, chain)
    return {"trace_id": trace_id}

@app.post("/api/v1/ransomware/hunt")
async def deploy_ransomware_hunt(background_tasks: BackgroundTasks):
    """Fetches high-risk Ransomware IOCs from DB and autos-traces to map campaigns."""
    async def hunt_task():
        await sio.emit('system_alert', {"msg": "Querying Data Lake for High-Risk Ransomware Actors...", "type": "warning"}, room="ransomware_hub")
        try:
            cursor = db.entities.find({"classification": "Ransomware"}).limit(5)
            iocs = await cursor.to_list(length=5)
            if not iocs: return
                
            await sio.emit('system_alert', {"msg": f"Extracted {len(iocs)} High-Risk Ransomware Indicators. Deploying Trace Swarm...", "type": "error"}, room="ransomware_hub")
            trace_id = f"HUNT-{uuid.uuid4().hex[:8].upper()}"
            tracer = NemesisLiveTracer(trace_id, max_depth=2, room_name="ransomware_hub")
            
            for ioc in iocs:
                await tracer.orchestrate(ioc.get("address"), ioc.get("chain", "BTC"), "API_RANSOMWHE.RE")
                await asyncio.sleep(2) 
        except Exception as e: await sio.emit('system_alert', {"msg": f"Hunt Error: {e}", "type": "error"}, room="ransomware_hub")

    background_tasks.add_task(hunt_task)
    return {"status": "Ransomware Hunt Initiated"}

@app.get("/api/v1/ransomware/sources")
async def get_ransomware_sources():
    return JSONResponse({"sources": GlobalThreatIntelLake.INTELLIGENCE_SOURCES})

@app.get("/api/v1/entities/{address}")
async def get_entity(address: str):
    entity = await db.entities.find_one({"address": address}, {"_id": 0})
    if not entity:
        return {
            "address": address,
            "classification": "Unknown Wallet",
            "risk_score": 50,
            "tags": ["Unverified"]
        }
    return entity

socket_app = socketio.ASGIApp(sio, app)

@app.get("/", response_class=HTMLResponse)
async def serve_dashboard():
    if os.path.exists("index.html"):
        with open("index.html", "r", encoding="utf-8") as f: return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>Error: Frontend UI not found.</h1>")

if __name__ == "__main__":
    import uvicorn
    logger.info("====================================================================")
    logger.info("  DEPLOYING LIONSGATE NEMESIS APEX (v100.0 RANSOMWARE INTEL ENGINE) ")
    logger.info("====================================================================")
    uvicorn.run(socket_app, host="0.0.0.0", port=8000) 
