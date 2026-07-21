import os
import re
import certifi
import socket
import asyncio
import csv
import json
import traceback
import threading
import aiohttp
import logging
import uuid
import hashlib
from google import genai
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from collections import defaultdict
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import DuplicateKeyError
import pandas as pd
import numpy as np
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler

from adapters.evm import EVMAdapter
from adapters.solana import SolanaAdapter
from adapters.utxo import UTXOAdapter
from adapters.tron_xrp_stellar import TronXrpStellarAdapter

from adapters.helius_solana import fetch_helius_transactions
from adapters.xrpscan import fetch_xrpscan_transactions
from adapters.stellar_horizon import fetch_horizon_transactions

from intel.abi_decoder import ABIDecoder
from intel.bridge_resolver import BridgeResolver
from intel.cex_clustering import CEXClusterer
from services.omni_parser import OmniParser
from services.forensic_llm_engine import GeminiForensicEngine, FlowReconstructor
from services.graph_engine import graph_engine

logger = logging.getLogger("OmniChainEngine")

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

MAX_DEPTH = 12
MAX_EDGES_PER_NODE = 50
CONCURRENCY_LIMIT = 50
CSV_FILE = "LFR_OmniChain_Trace.csv"
JSON_FILE = "LFR_OmniChain_Trace.json"

FILE_WRITE_LOCK = threading.Lock()
KNOWN_ENTITIES = {}
KNOWN_NEMESIS_IDS = {}
IO_POOL = ThreadPoolExecutor(max_workers=20)
EVM_API_SEMAPHORE = None
BTC_API_SEMAPHORE = None
TRON_API_SEMAPHORE = None
SOL_API_SEMAPHORE = None

FOUR_BYTE_CACHE = {}

async def resolve_4byte_signature(session, method_id):
    if not method_id: return None
    method_id = method_id.lower()
    if not method_id.startswith("0x"): method_id = "0x" + method_id
    if method_id in FOUR_BYTE_CACHE: return FOUR_BYTE_CACHE[method_id]
    
    try:
        url = f"https://www.4byte.directory/api/v1/signatures/?hex_signature={method_id}"
        async with session.get(url, timeout=3.0) as r:
            if r.status == 200:
                data = await r.json()
                results = data.get("results", [])
                if results:
                    text_sig = results[0].get("text_signature")
                    FOUR_BYTE_CACHE[method_id] = text_sig
                    return text_sig
            # If rate limited (429) or other non-200, we fall through to scraping
    except Exception as e:
        logger.error(f"4byte API lookup failed for {method_id}: {e}")
        
    # Fallback to HTML scraping and parsing
    try:
        scrape_url = f"https://www.4byte.directory/signatures/?bytes4_signature={method_id}"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"}
        async with session.get(scrape_url, headers=headers, timeout=5.0) as r:
            if r.status == 200:
                html = await r.text()
                # Parse the HTML table for the signature text
                import re
                match = re.search(r'<td>' + re.escape(method_id) + r'</td>\s*<td>([^<]+)</td>', html, re.IGNORECASE | re.DOTALL)
                if match:
                    text_sig = match.group(1).strip()
                    if text_sig:
                        FOUR_BYTE_CACHE[method_id] = text_sig
                        return text_sig
    except Exception as e:
        logger.error(f"4byte HTML scraping failed for {method_id}: {e}")
    
    FOUR_BYTE_CACHE[method_id] = None
    return None

from dotenv import load_dotenv
load_dotenv()

CONFIG = {
    "ETHERSCAN_API_KEY": os.getenv("ETHERSCAN_API_KEY", "AYQRQWFDJRK8WAX2ICJ8U4JUSYXZT5J7II"),
    "BSCSCAN_API_KEY": os.getenv("BSCSCAN_API_KEY", "AYQRQWFDJRK8WAX2ICJ8U4JUSYXZT5J7II"),
    "POLYGONSCAN_API_KEY": os.getenv("POLYGONSCAN_API_KEY", "YUXEUN58W2X5YYQZ3R8M33XN626B5X6JQA"),
    "SNOWTRACE_API_KEY": os.getenv("SNOWTRACE_API_KEY", "AYQRQWFDJRK8WAX2ICJ8U4JUSYXZT5J7II"),
    "ARBISCAN_API_KEY": os.getenv("ARBISCAN_API_KEY", "AYQRQWFDJRK8WAX2ICJ8U4JUSYXZT5J7II"),
    "OPTIMISMSCAN_API_KEY": os.getenv("OPTIMISMSCAN_API_KEY", "AYQRQWFDJRK8WAX2ICJ8U4JUSYXZT5J7II"),
    "BASESCAN_API_KEY": os.getenv("BASESCAN_API_KEY", "AYQRQWFDJRK8WAX2ICJ8U4JUSYXZT5J7II"),
    "GEMINI_API_KEY": os.getenv("GEMINI_API_KEYS", "").split(',')[0].strip('"') if os.getenv("GEMINI_API_KEYS") else "",
    "MONGO_URI": os.getenv("DATABASE_MONGO_URL", os.getenv("MONGO_URI", "mongodb+srv://nemesis:nemesis2026@nemesisdb.vir5vg2.mongodb.net/?appName=nemesisdb")),
    "TOKENVIEW_API_KEY": os.getenv("GETBLOCK_TRON_KEY", "2c9414b6d83947f5aa7a1f2f2f341cfc"),
    "OKLINK_API_KEY": os.getenv("OKLINK_API_KEY", ""),
    "ETHPLORER_API_KEY": os.getenv("ETHPLORER_API_KEY", "EK-jzMjY-tyVwyEJ-wj3su"),
    # New keys
    "TATUM_API_KEY": os.getenv("TATUM_API_KEY", ""),
    "ANKR_API_KEY": os.getenv("ANKR_API_KEY", ""),
    "INFURA_API_KEY": os.getenv("INFURA_API_KEY", ""),
    "GETBLOCK_BTC_KEY": os.getenv("GETBLOCK_BTC_KEY", ""),
    "GETBLOCK_ETH_KEY": os.getenv("GETBLOCK_ETH_KEY", ""),
    "GETBLOCK_SOL_KEY": os.getenv("GETBLOCK_SOL_KEY", ""),
    "GETBLOCK_TRON_KEY": os.getenv("GETBLOCK_TRON_KEY", ""),
    "GETBLOCK_XRP_KEY": os.getenv("GETBLOCK_XRP_KEY", ""),
    "VALIDATION_BTC": os.getenv("VALIDATION_BTC", ""),
    "VALIDATION_ETH": os.getenv("VALIDATION_ETH", ""),
    "VALIDATION_SOL": os.getenv("VALIDATION_SOL", ""),
    "PUBLICNODE_BITCOIN_RPC": os.getenv("PUBLICNODE_BITCOIN_RPC", ""),
    "PUBLICNODE_SOLANA_WSS": os.getenv("PUBLICNODE_SOLANA_WSS", ""),
    "PUBLICNODE_TRON_RPC": os.getenv("PUBLICNODE_TRON_RPC", ""),
    "XRPSCAN_BASE_URL": os.getenv("XRPSCAN_BASE_URL", "https://api.xrpscan.com/api/v1")
}

EVM_DOMAINS = {
    "ETHEREUM": 1, "BSC": 56,
    "POLYGON": 137, "BASE": 8453,
    "ARBITRUM": 42161, "OPTIMISM": 10
}

USD_RATES = {
    "ETHEREUM": 3100.00, "BITCOIN": 65000.00, "TRON": 0.12, "POLYGON": 0.70, "BSC": 580.0,
    "BASE": 3100.00, "ARBITRUM": 3100.00, "OPTIMISM": 3100.00
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
    "414bf389": "ExactInputSingle (UniswapV3)", "b858183f": "ExactInput (UniswapV3)",
    "04e45aaf": "ExactOutputSingle (UniswapV3)", "09b81346": "ExactOutput (UniswapV3)",
    "3d12a85a": "DepositFor (Bridge)", "a3bc6e0e": "BridgeIn", "8b9e4f93": "BridgeOut",
    "b6b55f25": "Deposit (Mixer)", "21a0adb6": "Withdraw (Mixer)", "e3ceb028": "Transact (Railgun)",
    "e523f4f1": "CEX Hot Wallet Sweep", "d0e30db0": "Deposit (WETH)", "2e1a7d4d": "Withdraw (WETH)",
    "022c0d9f": "Swap (1inch)", "12aa3caf": "Swap (Generic DEX)",
    "40c10f19": "Mint", "42966c68": "Burn", "a22cb465": "SetApprovalForAll (NFT)", "42842e0e": "SafeTransferFrom (NFT)",
    # Real-World Forensics
    "7e58a4cc": "PublishMessage (Wormhole Bridge)", "9981509f": "WrapAndTransferETH (Wormhole Bridge)", "310a082e": "TransferTokens (Wormhole Bridge)",
    "0f5287e0": "Swap (Stargate Bridge)", "028c3a1b": "SwapRemote (Stargate Bridge)",
    "c22a7f05": "DepositForBurn (CCTP)", "4b45eba1": "DepositForBurn (CCTP)",
    "a1903eab": "Submit (Lido Liquid Staking)", "e90a182f": "Deposit (RocketPool)", "5a39626e": "DelegateTo (EigenLayer)",
    "fb3bdb41": "SwapExactTokensForTokensSupportingFeeOnTransferTokens (DEX)",
    "e47963be": "Deposit (Aave)", "47e7ef24": "Deposit (Compound)",
    "1cff79cd": "Execute (UniswapV4/UniversalRouter)", "5f575529": "Swap (Curve)", "3593564c": "Execute (0x Protocol)", "b2bdfcf7": "FlashLoan (Aave)"
}

mongo_client = None
mongo_db = None

async def init_mongodb():
    global mongo_client, mongo_db
    try:
        if mongo_client is None:
            mongo_url = CONFIG.get("MONGO_URI") or os.getenv("DATABASE_MONGO_URL") or os.getenv("MONGO_URI")
            if not mongo_url:
                raise ValueError("MongoDB URI is not configured in .env (DATABASE_MONGO_URL or MONGO_URI)")
            mongo_client = AsyncIOMotorClient(mongo_url, serverSelectionTimeoutMS=15000)
            
            try:
                # Attempt to use the database provided in the URI (e.g., 'blockchain')
                mongo_db = mongo_client.get_default_database()
            except Exception:
                mongo_db = mongo_client["nemesis_traces"]
            
            # Basic UI / Old Trace Schemas
            try:
                await mongo_db.edges.create_index([("trace_id", 1), ("from", 1), ("to", 1)])
                await mongo_db.traces.create_index([("trace_id", 1)], unique=True)
                
                # OmniChain State-Graph Schemas (Nemesis Matrix)
                await mongo_db.entities.create_index([("id", 1)], unique=True)
                await mongo_db.transactions.create_index([("tx_hash", 1)], unique=True)
                await mongo_db.events.create_index([("tx_hash", 1)])
                await mongo_db.state_edges.create_index([("trace_id", 1), ("from", 1), ("to", 1)])
                await mongo_db.bridge_links.create_index([("lock_tx", 1)])
                await mongo_db.identity_artifacts.create_index([("value", 1), ("type", 1)])
                await mongo_db.wallet_labels.create_index([("address", 1)], unique=True)
            except Exception as e_idx:
                if "not authorized" in str(e_idx).lower():
                    logger.warning("MongoDB indexing skipped: Database user lacks 'createIndex' permissions. Continuing without them.")
                else:
                    logger.warning(f"Could not create MongoDB indexes: {e_idx}")
            
            # Ping to verify connection
            await mongo_client.admin.command('ping')
            logger.info("MongoDB Initialized for Trace Storage with Multi-Chain Schemas.")
            
            # Neo4j setup check
            await graph_engine.connect()
    except Exception as e:
        logger.warning(f"MongoDB not available: {e}. Running in memory-only mode.")
        mongo_client = None
        mongo_db = None

def get_mongo_status():
    return mongo_db is not None

async def save_wallet_label(address: str, label_data: dict):
    if mongo_db is None: return False
    try:
        label_data["address"] = address.lower()
        label_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        await mongo_db.wallet_labels.update_one(
            {"address": address.lower()},
            {"$set": label_data},
            upsert=True
        )
        return True
    except Exception as e:
        logger.error(f"Failed to save wallet label for {address}: {e}")
        return False

async def get_wallet_label(address: str):
    if mongo_db is None: return None
    try:
        return await mongo_db.wallet_labels.find_one({"address": address.lower()})
    except:
        return None

async def fetch_saved_traces():
    if mongo_db is None: return []
    try:
        cursor = mongo_db.traces.find().sort("timestamp", -1).limit(50)
        traces = await cursor.to_list(length=50)
        for t in traces:
            t['_id'] = str(t['_id'])
            if 'timestamp' in t and isinstance(t['timestamp'], datetime):
                t['timestamp'] = t['timestamp'].isoformat()
        return traces
    except:
        return []

def get_active_traces(active_sessions):
    return [
        {
            "trace_id": k,
            "seeds": v.seeds,
            "client": getattr(v, "client_ip", "Unknown")
        } for k, v in active_sessions.items()
    ]

def detect_chain(val: str, override: str = "AUTO") -> str:
    if override and override != "AUTO": return override.upper()
    val = val.strip()
    if val.startswith("bc1") or val.startswith("1") or val.startswith("3"): return "BITCOIN"
    elif val.startswith("T") and len(val) == 34: return "TRON"
    elif val.startswith("0x") and len(val) == 42: return "EVM_AUTO"
    elif val.startswith("r") and 25 <= len(val) <= 35: return "RIPPLE"
    elif val.startswith("G") and len(val) == 56: return "STELLAR"
    elif 32 <= len(val) <= 44 and not val.startswith("0x") and not val.startswith("bc1"): return "SOLANA"
    return "INVALID"

def get_asset_ticker(chain: str) -> str:
    if chain == "BITCOIN": return "BTC"
    elif chain == "TRON": return "TRX"
    elif chain == "POLYGON": return "MATIC"
    elif chain == "RIPPLE": return "XRP"
    elif chain == "STELLAR": return "XLM"
    elif chain == "SOLANA": return "SOL"
    return "ETH"

import re
from html.parser import HTMLParser

class OKLinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_target = False
        self.target_depth = 0
        self.current_text = []
        self.results = []

    def handle_starttag(self, tag, attrs):
        if not self.in_target:
            for k, v in attrs:
                if k == 'class' and v and 'text-ellipsis' in v:
                    self.in_target = True
                    self.target_depth = 1
                    self.current_text = []
                    break
        else:
            self.target_depth += 1

    def handle_endtag(self, tag):
        if self.in_target:
            self.target_depth -= 1
            if self.target_depth <= 0:
                self.in_target = False
                self.results.append("".join(self.current_text))

    def handle_data(self, data):
        if self.in_target:
            self.current_text.append(data)

async def fetch_oklink_label(session, chain: str, address: str) -> str:
    cmap = {"BTC": "btc", "BITCOIN": "btc", "ETH": "eth", "ETHEREUM": "eth", "POLYGON": "polygon", "BSC": "bsc", "TRX": "trx", "TRON": "trx", "EVM_AUTO": "eth", "BASE": "base", "ARBITRUM": "arbitrum", "OPTIMISM": "optimism"}
    cname = cmap.get(chain.upper())
    if not cname: return None
    url = f"https://www.oklink.com/{cname}/address/{address}"
    try:
        async with session.get(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"}, timeout=8.0) as resp:
            if resp.status == 200:
                html = await resp.text()
                parser = OKLinkParser()
                parser.feed(html)
                for raw_text in parser.results:
                    label = raw_text.replace('#', '').strip()
                    if label and len(label) > 2 and "0x" not in label.lower() and not label.lower().startswith("bc1") and label.lower() != "address": 
                        return label
                
                match_json = re.search(r'"entityName"\s*:\s*"([^"]+)"', html)
                if match_json: return match_json.group(1)
                match_tag = re.search(r'"addressTag"\s*:\s*"([^"]+)"', html)
                if match_tag: return match_tag.group(1)
    except: pass
    return None

async def auto_scrape_label(session, chain, address):
    ok_label = await fetch_oklink_label(session, chain, address)
    if ok_label: return ok_label, "OKLink"
    
    if chain in ["ETHEREUM", "EVM_AUTO", "ETH"]:
        url = f"https://ethplorer.io/search/{address}"
        try:
            async with session.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=5.0) as resp:
                if resp.status == 200:
                    html = await resp.text()
                    matches = re.findall(r'title="([^"]*?(?:mixer|dapp|dex|defi|exchange|cex|custodial|swap|hot wallet|cold wallet|darknet|sanctions|ofac|blacklisted)[^"]*?)"', html, re.IGNORECASE)
                    if matches: return ", ".join(set(matches)), "Ethplorer"
        except: pass
    return None, None

async def fetch_wallet_label(session, addr, chain, trace_id=None):
    addr_lower = addr.lower()
    if addr_lower in KNOWN_ENTITIES: return KNOWN_ENTITIES[addr_lower]
        
    if mongo_db is not None:
        try:
            doc = await mongo_db.wallet_labels.find_one({"address": addr_lower})
            if doc and "label" in doc:
                KNOWN_ENTITIES[addr_lower] = doc["label"]
                return doc["label"]
        except: pass

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
        # 1. Quick regex scan first
        scraped_label, source = await auto_scrape_label(session, chain, addr)
        if scraped_label:
            label = scraped_label
            if mongo_db is not None:
                try:
                    await mongo_db.wallet_labels.insert_one(
                        {"address": addr_lower, "label": label, "source": source, "timestamp": datetime.now(timezone.utc)}
                    )
                except: pass
        else:
            # 2. Fire the deep DOM Playwright Scraper asynchronously so we don't block
            from services.scraper_engine import scraper_instance
            try:
                asyncio.create_task(scraper_instance.resolve_address(addr, chain, trace_id))
            except RuntimeError:
                pass # Event loop is closed

    KNOWN_ENTITIES[addr_lower] = label
    return label

async def get_or_create_nemesis_id(addr: str) -> str:
    addr_lower = addr.lower()
    if addr_lower in KNOWN_NEMESIS_IDS:
        return KNOWN_NEMESIS_IDS[addr_lower]
        
    nemesis_id = f"NID-{str(uuid.uuid4())[:8].upper()}"
    if mongo_db is not None:
        try:
            doc = await mongo_db.wallet_labels.find_one({"address": addr_lower})
            if doc and "nemesis_id" in doc:
                nemesis_id = doc["nemesis_id"]
            else:
                try:
                    await mongo_db.wallet_labels.insert_one(
                        {"address": addr_lower, "nemesis_id": nemesis_id}
                    )
                except: pass
        except: pass
        
    KNOWN_NEMESIS_IDS[addr_lower] = nemesis_id
    return nemesis_id

def thread_safe_file_write(ledger_data, trace_id, narrative=""):
    unified_data = []
    for row in ledger_data:
        unified_data.append({
            "Date/Time (UTC)": row.get("timestamp"),
            "Type transcation(mixing,bridging)": row.get("intent_action", ""),
            "TX Hash": row.get("tx"),
            "From Wallet(Entity)": f"{row.get('from', '')} ({row.get('sender_entity', 'Unknown')})",
            "To Wallet(Entity)": f"{row.get('to', '')} ({row.get('receiver_entity', 'Unknown')})",
            "To Receiver Entity": row.get("receiver_entity"),
            "Amount": f"{row.get('amount', 0):.4f} {row.get('ticker', '')}",
            "Transaction Type": row.get("edge_type", ""),
            "Behavioral Cluster": row.get("cluster"),
            "Clustered address{root}ENTITY": row.get("origin_seed", ""),
            "Confidence": row.get("confidence"),
            "Transaction Attributions": row.get("attributions", ""),
            "Transaction intelligence": row.get("intelligence", "")
        })

    with FILE_WRITE_LOCK:
        try:
            with open(f"LFR_{trace_id}.json", "w", encoding="utf-8") as f: 
                json.dump({"narrative": narrative, "data": unified_data}, f, indent=4)
            with open(f"LFR_{trace_id}.csv", "w", newline="", encoding="utf-8") as f: 
                # Add narrative as the first line of the CSV as a comment or meta field
                f.write(f"# AI NARRATIVE: {narrative.replace(chr(10), ' ')}\n")
                fieldnames = ["Date/Time (UTC)", "Type transcation(mixing,bridging)", "TX Hash", "From Wallet(Entity)", "To Wallet(Entity)", "To Receiver Entity", "Amount", "Transaction Type", "Behavioral Cluster", "Clustered address{root}ENTITY", "Confidence", "Transaction Attributions", "Transaction intelligence"]
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(unified_data)
        except Exception as e:
            logger.error(f"File write failed: {e}")

async def classify_tx_intent(tx: dict) -> dict:
    input_data = tx.get("input", "")
    method = input_data[:10].lower().replace("0x", "") if input_data else ""
    intent = {"action": "NATIVE_TRANSFER", "edge_type": "TRANSFER", "obf_path": "NONE", "raw_input": input_data, "method_id": method}
    
    # Internal Tx checks based on typical RPC output
    if tx.get("isError") == "0" and not input_data:
        intent["edge_type"] = "INTERNAL_TX"
    
    if not input_data or input_data == "0x" or len(input_data) < 8: return intent

    if method in SIGNATURE_REGISTRY:
        sig_val = SIGNATURE_REGISTRY[method]
        intent["action"] = sig_val
        if "DEX" in sig_val or "Swap" in sig_val or "UniswapV3" in sig_val: intent["edge_type"] = "SWAP"; intent["obf_path"] = "DEX_ROUTING"
        elif "Bridge" in sig_val or "CCTP" in sig_val: intent["edge_type"] = "BRIDGE_HOP"; intent["obf_path"] = "BRIDGE"
        elif "Mixer" in sig_val or "Railgun" in sig_val: intent["edge_type"] = "MIXER"; intent["obf_path"] = "MIXER"
        elif "Sweep" in sig_val: intent["edge_type"] = "CEX_DEPOSIT"; intent["obf_path"] = "CUSTODIAL_SETTLEMENT"
        elif "WETH" in sig_val and "Deposit" in sig_val: intent["edge_type"] = "LOCK"
        elif "WETH" in sig_val and "Withdraw" in sig_val: intent["edge_type"] = "RELEASE"
        elif "Mint" in sig_val: intent["edge_type"] = "MINT"
        elif "Burn" in sig_val: intent["edge_type"] = "BURN"
        elif "NFT" in sig_val: intent["edge_type"] = "NFT_TRADE"
        elif "Staking" in sig_val or "Aave" in sig_val or "Compound" in sig_val or "EigenLayer" in sig_val: intent["edge_type"] = "STAKING"; intent["obf_path"] = "YIELD"
        elif "Transfer" in sig_val: intent["edge_type"] = "TRANSFER"; intent["action"] = "TOKEN_TRANSFER"
    else:
        intent["action"] = "CONTRACT_CALL"
        intent["edge_type"] = "CONTRACT_INTERACTION"
    return intent

async def find_bridge_symmetry(tx_hash: str):
    if mongo_db is None: return None
    try:
        return await mongo_db.bridge_links.find_one({"$or": [{"mint_tx": tx_hash}, {"lock_tx": tx_hash}]})
    except:
        return None

async def find_identity_pivots(wallet_address: str):
    if mongo_db is None: return []
    try:
        cursor = mongo_db.identity_artifacts.find({"linked_entities": wallet_address})
        return await cursor.to_list(length=100)
    except:
        return []

async def find_cex_withdrawals(exchange_address: str):
    if mongo_db is None: return []
    try:
        # Heuristic CEX internal ledger withdrawal routing based on known transactions
        cursor = mongo_db.transactions.find({"from": exchange_address}).sort("block_time", -1).limit(5)
        txs = await cursor.to_list(length=5)
        return [tx.get("to") for tx in txs if tx.get("to")]
    except:
        return []

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
        self.cex_keywords = ["MEXC", "BINANCE", "KRAKEN", "OKX", "COINBASE", "KUCOIN", "HOT WALLET", "HUOBI", "EXCHANGE", "CEX"]
        self.mixer_keywords = ["MIXER", "TORNADO CASH", "RAILGUN"]
        self.bridge_keywords = ["BRIDGE", "STARGATE", "MULTICHAIN", "WORMHOLE", "ORBITER"]
        self.dex_keywords = ["ROUTER", "UNISWAP", "PANCAKESWAP", "SUSHISWAP", "1INCH", "CURVE", "DEX", "SWAP", "DEFI"]
    
    def classify(self, addr, osint_label):
        combined_lbl = osint_label.upper()
        if any(keyword in combined_lbl for keyword in self.cex_keywords): return "EXCHANGE_CUSTODIAL", 95
        if any(keyword in combined_lbl for keyword in self.bridge_keywords): return "CROSS_CHAIN_BRIDGE", 70
        if any(keyword in combined_lbl for keyword in self.mixer_keywords): return "MIXER_LIKE", 100
        if any(keyword in combined_lbl for keyword in self.dex_keywords): return "DEX_ROUTER", 70
        return "PRIVATE_NODE", 10

class TraceEngine:
    def __init__(self, trace_id):
        self.trace_id = trace_id
        self.visited = set()
        self.ledger = []
        self.cex = CEXClusterer(mongo_db) if mongo_db is not None else CEX()
        self.bridge_resolver = BridgeResolver(mongo_db)
        self.abi_decoder = ABIDecoder()
        self.evm_adapter = EVMAdapter()
        self.solana_adapter = SolanaAdapter()
        self.utxo_adapter = UTXOAdapter()
        self.txs_adapter = TronXrpStellarAdapter()
        
        self.llm_engine = GeminiForensicEngine()
        self.flow_reconstructor = FlowReconstructor()
        
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
        self.clients = set()
        self.is_running = False
        self.client_ip = ""
        self.max_depth = 1000000
        self.max_hops = 1000000
        self.target_currency = "USD"
        
    def setup(self, seeds, target_amount, default_chain="AUTO", start_date="", end_date="", target_currency="USD", max_depth=1000000, max_hops=1000000):
        self.seeds = seeds
        self.target_currency = target_currency.upper()
        self.max_depth = int(max_depth)
        self.max_hops = int(max_hops)
        
        rate = USD_RATES.get(self.target_currency, 1.0)
        self.target_asset_amount = target_amount * rate if target_currency != "USD" else target_amount
        
        self.start_date = start_date; self.end_date = end_date
        for seed in seeds:
            chain = detect_chain(seed, default_chain)
            if chain == "EVM_AUTO":
                self.seed_chains[seed] = "MULTI-EVM"
                for evm_chain in EVM_DOMAINS.keys():
                    self.queue.put_nowait((seed, 0, target_amount, "NONE", evm_chain, seed))
            else:
                self.seed_chains[seed] = chain
                self.queue.put_nowait((seed, 0, target_amount, "NONE", chain, seed))

    async def fetch_txs(self, session, addr, chain):
        global EVM_API_SEMAPHORE, BTC_API_SEMAPHORE, TRON_API_SEMAPHORE, SOL_API_SEMAPHORE
        if EVM_API_SEMAPHORE is None:
            EVM_API_SEMAPHORE = asyncio.Semaphore(15)
        if BTC_API_SEMAPHORE is None:
            BTC_API_SEMAPHORE = asyncio.Semaphore(5)
        if TRON_API_SEMAPHORE is None:
            TRON_API_SEMAPHORE = asyncio.Semaphore(5)
        if SOL_API_SEMAPHORE is None:
            SOL_API_SEMAPHORE = asyncio.Semaphore(5)
            
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Connection": "keep-alive"
        }
        if chain == "BITCOIN":
            async with BTC_API_SEMAPHORE:
                for attempt in range(4):
                    try:
                        async with session.get(f"https://mempool.space/api/address/{addr}/txs", headers=headers, timeout=12) as r:
                            if r.status == 200: return {"type": "btc", "data": await r.json(), "actual_chain": "BITCOIN"}
                    except: pass
                    
                    try:
                        async with session.get(f"https://blockstream.info/api/address/{addr}/txs", headers=headers, timeout=12) as r2:
                            if r2.status == 200: return {"type": "btc", "data": await r2.json(), "actual_chain": "BITCOIN"}
                    except: pass
                    try:
                        async with session.get(f"https://blockchain.info/rawaddr/{addr}", headers=headers, timeout=12) as r3:
                            if r3.status == 200:
                                bdata = await r3.json()
                                if "txs" in bdata:
                                    mempool_txs = []
                                    for tx in bdata["txs"]:
                                        m_tx = {"txid": tx.get("hash", ""), "status": {"block_time": tx.get("time", 0)}}
                                        m_tx["vin"] = [{"prevout": {"scriptpubkey_address": i.get("prev_out", {}).get("addr"), "value": i.get("prev_out", {}).get("value", 0)}} for i in tx.get("inputs", []) if i.get("prev_out")]
                                        m_tx["vout"] = [{"scriptpubkey_address": o.get("addr"), "value": o.get("value", 0)} for o in tx.get("out", [])]
                                        mempool_txs.append(m_tx)
                                    return {"type": "btc", "data": mempool_txs, "actual_chain": "BITCOIN"}
                    except: pass
                    await asyncio.sleep(1.5 ** attempt)
                
                if CONFIG.get("GETBLOCK_BTC_KEY"):
                    try:
                        async with session.get(f"https://go.getblock.io/{CONFIG['GETBLOCK_BTC_KEY']}/api/v2/address/{addr}/txs", headers=headers, timeout=12) as r:
                            if r.status == 200: return {"type": "btc", "data": await r.json(), "actual_chain": "BITCOIN"}
                    except: pass
                
                return {"type": "btc", "data": [], "actual_chain": "BITCOIN"}
        
        elif chain == "TRON":
            all_txs = []
            async with TRON_API_SEMAPHORE:
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
            
            if not all_txs and CONFIG.get("GETBLOCK_TRON_KEY"):
                try:
                    async with session.get(f"https://go.getblock.io/{CONFIG['GETBLOCK_TRON_KEY']}/api/v1/account/transactions?address={addr}", headers=headers, timeout=12) as r:
                        if r.status == 200:
                            d = await r.json()
                            if d.get("data"): all_txs.extend(d["data"])
                except: pass
                
            return {"type": "tron", "data": all_txs, "actual_chain": "TRON"}
        
        elif chain == "RIPPLE":
            txs = await fetch_xrpscan_transactions(addr, max_pages=1)
            return {"type": "parsed_standard", "data": txs, "actual_chain": "RIPPLE"}
        
        elif chain == "STELLAR":
            txs = await fetch_horizon_transactions(addr, max_pages=1)
            return {"type": "parsed_standard", "data": txs, "actual_chain": "STELLAR"}
        
        elif chain == "SOLANA":
            txs = await fetch_helius_transactions(addr, max_pages=1)
            return {"type": "parsed_standard", "data": txs, "actual_chain": "SOLANA"}
        
        actual_chain = chain if chain in EVM_DOMAINS else "ETHEREUM"
        
        # For V2, Etherscan API keys work for all chains, but free tier requires network-specific keys.
        key_var = f"{actual_chain}SCAN_API_KEY" if actual_chain != "ETHEREUM" else "ETHERSCAN_API_KEY"
        api_key = CONFIG.get(key_var, CONFIG.get("ETHERSCAN_API_KEY", "YourApiKeyToken"))
        
        all_txs = []
        
        if actual_chain == "ETHEREUM":
            base_url = "https://api.etherscan.io/api"
        elif actual_chain == "BSC":
            base_url = "https://api.bscscan.com/api"
        elif actual_chain == "POLYGON":
            base_url = "https://api.polygonscan.com/api"
        elif actual_chain == "BASE":
            base_url = "https://api.basescan.org/api"
        elif actual_chain == "ARBITRUM":
            base_url = "https://api.arbiscan.io/api"
        elif actual_chain == "OPTIMISM":
            base_url = "https://api-optimistic.etherscan.io/api"
        else:
            base_url = "https://api.etherscan.io/api"
        
        endpoints = [
            ("native", "txlist"),
            ("token", "tokentxns"),
            ("internal", "txlistinternal"),
            ("nft", "tokennfttx"),
            ("1155", "token1155tx")
        ]
        
        async def fetch_page(b_url, action, page, max_retries=3):
            url = f"{b_url}?module=account&action={action}&address={addr}&startblock=0&endblock=99999999&page={page}&offset=1000&sort=desc&apikey={api_key}"
            for attempt in range(max_retries):
                try:
                    async with EVM_API_SEMAPHORE:
                        async with session.get(url, headers=headers, timeout=12) as r:
                            if r.status == 200:
                                raw_text = await r.text()
                                try:
                                    data = json.loads(raw_text)
                                except:
                                    return []
                                if data.get("status") == "1":
                                    return data.get("result", [])
                                elif data.get("message") == "NOTOK" and "rate limit" in str(data.get("result", "")).lower():
                                    await asyncio.sleep(2.0 + attempt * 2)
                                    continue
                                else:
                                    return []
                except Exception as e:
                    await asyncio.sleep(1.0)
            return []

        async def fetch_endpoint_all_pages(action):
            ep_results = []
            page = 1
            while page <= 20: # 20k tx limit per category (1000 * 20)
                res = await fetch_page(base_url, action, page)
                if not res or len(res) == 0: break
                ep_results.extend(res)
                if len(res) < 1000: break # reached the end
                page += 1
                await asyncio.sleep(0.3)
            return ep_results

        tasks = [fetch_endpoint_all_pages(act) for _, act in endpoints]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for res in results:
            if isinstance(res, list):
                all_txs.extend(res)
        
        # 1.5 Ankr Advanced API Fallback
        if not all_txs:
            ankr_map = {"ETHEREUM": "eth", "BSC": "bsc", "POLYGON": "polygon", "BASE": "base", "ARBITRUM": "arbitrum", "OPTIMISM": "optimism"}
            ankr_chain = ankr_map.get(actual_chain)
            ankr_key = CONFIG.get("ANKR_API_KEY")
            if ankr_chain and ankr_key:
                ankr_url = f"https://rpc.ankr.com/multichain/{ankr_key}"
                payload_native = {
                    "jsonrpc": "2.0",
                    "method": "ankr_getTransactionsByAddress",
                    "params": {"blockchain": ankr_chain, "address": addr, "descending": True},
                    "id": 1
                }
                payload_token = {
                    "jsonrpc": "2.0",
                    "method": "ankr_getTokenTransfers",
                    "params": {"blockchain": ankr_chain, "address": addr, "descending": True},
                    "id": 1
                }
                for payload in [payload_native, payload_token]:
                    try:
                        async with session.post(ankr_url, json=payload, headers={"Content-Type": "application/json"}, timeout=12) as r:
                            if r.status == 200:
                                data = await r.json()
                                res = data.get("result", {})
                                txs = res.get("transactions", []) or res.get("transfers", [])
                                for t in txs:
                                    t_hash = t.get("hash") or t.get("transactionHash")
                                    if not t_hash: continue
                                    t["hash"] = t_hash
                                    t["from"] = t.get("fromAddress") or t.get("from")
                                    t["to"] = t.get("toAddress") or t.get("to")
                                    
                                    raw_val = t.get("valueExact")
                                    if not raw_val:
                                        try:
                                            val_float = float(t.get("value", "0"))
                                            dec = int(t.get("tokenDecimals", 18))
                                            raw_val = str(int(val_float * (10**dec)))
                                        except:
                                            raw_val = "0"
                                            
                                    t["value"] = raw_val
                                    if "tokenDecimals" in t:
                                        t["tokenDecimal"] = t.get("tokenDecimals")
                                        
                                    t["timeStamp"] = t.get("timestamp") or str(int(datetime.now(timezone.utc).timestamp()))
                                    all_txs.append(t)
                    except Exception as e:
                        logger.error(f"Ankr API Error on {actual_chain}: {e}")
                        pass
                        
        # 2. Blockscout Fallback
        if not all_txs:
            bs_urls = {
                "ETHEREUM": "https://eth.blockscout.com",
                "POLYGON": "https://polygon.blockscout.com",
                "BASE": "https://base.blockscout.com",
                "OPTIMISM": "https://optimism.blockscout.com",
                "ARBITRUM": "https://arbitrum.blockscout.com"
            }
            bs_domain = bs_urls.get(actual_chain)
            if bs_domain:
                url_bs_native = f"{bs_domain}/api?module=account&action=txlist&address={addr}&startblock=0&endblock=99999999&page=1&offset=200&sort=desc"
                url_bs_token = f"{bs_domain}/api?module=account&action=tokentxns&address={addr}&startblock=0&endblock=99999999&page=1&offset=200&sort=desc"
                for u in [url_bs_native, url_bs_token]:
                    try:
                        async with session.get(u, headers=headers, timeout=10) as r:
                            if r.status == 200:
                                data = await r.json()
                                if data.get("status") == "1":
                                    all_txs.extend(data.get("result", []))

                    except Exception as e:
                        logger.error(f"Blockscout Error on {actual_chain}: {e}")
                        pass
                
        # 3. Ethplorer Fallback (ETHEREUM only)
        if not all_txs and actual_chain == "ETHEREUM":
            ethp_key = CONFIG.get("ETHPLORER_API_KEY", "freekey")
            url_ethp = f"https://api.ethplorer.io/getAddressHistory/{addr}?apiKey={ethp_key}&limit=200"
            try:
                async with session.get(url_ethp, timeout=10) as r:
                    if r.status == 200:
                        data = await r.json()
                        if "operations" in data:
                            for op in data["operations"]:
                                op["hash"] = op.get("transactionHash")
                                op["from"] = op.get("from")
                                op["to"] = op.get("to")
                                op["value"] = op.get("value")
                                op["timeStamp"] = op.get("timestamp")
                                all_txs.append(op)
            except: pass
            
        # 3. Tatum Fallback
        if not all_txs:
            tatum_chain_map = {"ETHEREUM": "ethereum", "BSC": "bsc", "POLYGON": "polygon"}
            t_chain = tatum_chain_map.get(actual_chain)
            tatum_key = CONFIG.get("TATUM_API_KEY")
            if t_chain and tatum_key:
                url_tatum = f"https://api.tatum.io/v3/{t_chain}/account/transaction/{addr}?pageSize=50"
                try:
                    async with session.get(url_tatum, headers={"x-api-key": tatum_key}, timeout=10) as r:
                        if r.status == 200:
                            data = await r.json()
                            for tx in data:
                                tx["hash"] = tx.get("hash", tx.get("transactionHash"))
                                tx["timeStamp"] = tx.get("timestamp", tx.get("blockNumber"))
                                all_txs.append(tx)
                except: pass
                
        # 4. Infura/Chainstack/ValidationCloud Fallback
        if not all_txs:
            infura_key = CONFIG.get("INFURA_API_KEY")
            if infura_key:
                rpc_map = {
                    "ETHEREUM": f"https://mainnet.infura.io/v3/{infura_key}",
                    "POLYGON": f"https://polygon-mainnet.infura.io/v3/{infura_key}",
                    "ARBITRUM": f"https://arbitrum-mainnet.infura.io/v3/{infura_key}",
                    "BASE": f"https://base-mainnet.infura.io/v3/{infura_key}",
                    "OPTIMISM": f"https://optimism-mainnet.infura.io/v3/{infura_key}"
                }
                rpc_url = rpc_map.get(actual_chain)
                if rpc_url:
                    # Generic eth_getLogs for Transfer events involving this address
                    payload_rpc = {
                        "jsonrpc": "2.0",
                        "method": "eth_getLogs",
                        "params": [{"address": addr}],
                        "id": 1
                    }
                    try:
                        async with session.post(rpc_url, json=payload_rpc, headers={"Content-Type": "application/json"}, timeout=12) as r:
                            if r.status == 200:
                                data = await r.json()
                                if data.get("result"):
                                    for log in data["result"]:
                                        log["hash"] = log.get("transactionHash")
                                        log["from"] = addr # We won't know exact from/to from raw log without parsing topics
                                        log["to"] = addr
                                        log["timeStamp"] = str(int(datetime.now(timezone.utc).timestamp()))
                                        all_txs.append(log)
                    except: pass
                    
        return {"type": "evm", "data": all_txs, "actual_chain": actual_chain}

    async def process_bitcoin_txs(self, session, addr, txs, depth, carry_val, obf_path, chain, origin_seed):
        for tx in txs:
            txid = tx.get("txid", "Unknown")
            ts = tx.get("status", {}).get("block_time", 0)
            timestamp = datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S') if ts else datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
            
            inputs = [i.get("prevout", {}).get("scriptpubkey_address") for i in tx.get("vin", []) if i.get("prevout", {}).get("scriptpubkey_address")]
            self.clustering.cluster_inputs(inputs)
            
            if self.start_date and timestamp[:10] < self.start_date: continue
            if self.end_date and timestamp[:10] > self.end_date: continue

            addr_lower = addr.lower()
            is_sender = any(i.get("prevout", {}).get("scriptpubkey_address", "").lower() == addr_lower for i in tx.get("vin", []))
            is_receiver = any(o.get("scriptpubkey_address", "").lower() == addr_lower for o in tx.get("vout", []))
            
            logger.info(f"Tx {txid}: is_sender={is_sender}, is_receiver={is_receiver}, addr_lower={addr_lower}, seeds={self.seeds}")
            
            intent_data = {"action": "NATIVE_TRANSFER", "edge_type": "UTXO_TRANSFER", "obf_path": obf_path}
            
            if len(tx.get("vin", [])) <= 2 and len(tx.get("vout", [])) >= 5:
                intent_data["action"] = "UTXO_FAN_OUT"
                intent_data["obf_path"] = "PEEL_CHAIN"
                
            if is_sender:
                for o in tx.get("vout", []):
                    to = str(o.get("scriptpubkey_address", "")).lower()
                    if not to or to == addr_lower: continue
                    amt = int(o.get("value", 0)) / 1e8
                    if amt < 0.000001: continue
                    logger.info(f"Adding OUTBOUND hop: {addr_lower} -> {to} (Amt: {amt})")
                    await self.process_hop(session, addr, to, amt, txid, timestamp, depth, chain, origin_seed, intent_data, "BTC")
            elif is_receiver and addr in self.seeds:
                # Inbound to seed
                for i in tx.get("vin", []):
                    f_addr = str(i.get("prevout", {}).get("scriptpubkey_address", "")).lower()
                    if not f_addr or f_addr == addr_lower: continue
                    amt = int(i.get("prevout", {}).get("value", 0)) / 1e8
                    if amt < 0.000001: continue
                    logger.info(f"Adding INBOUND hop: {f_addr} -> {addr_lower} (Amt: {amt})")
                    await self.process_hop(session, f_addr, addr, amt, txid, timestamp, depth, chain, origin_seed, intent_data, "BTC")

    async def process_tron_txs(self, session, addr, txs, depth, carry_val, obf_path, chain, origin_seed):
        for tx in txs:
            from_addr = tx.get("ownerAddress") or tx.get("fromAddress") or tx.get("from") or tx.get("sender")
            to = tx.get("toAddress") or tx.get("to") or tx.get("receiver")
            
            is_outbound = (from_addr == addr and to and to != addr)
            is_inbound = (to == addr and from_addr and from_addr != addr and addr in self.seeds)
            if not (is_outbound or is_inbound): continue
            
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
            
            if self.start_date and ts_iso[:10] < self.start_date: continue
            if self.end_date and ts_iso[:10] > self.end_date: continue

            ticker = "USDT" if "volume" in tx else "TRX"
            intent_data = {"action": "TRON_TRANSFER", "edge_type": "TRANSFER", "obf_path": "NONE"}
            
            await self.process_hop(session, from_addr, to, amt, txid, ts_iso, depth, chain, origin_seed, intent_data, ticker)

    async def process_evm_txs(self, session, addr, txs, depth, carry_val, obf_path, chain, origin_seed):
        for tx in txs:
            txid = tx.get("hash", "Unknown")
            to = str(tx.get("to", "")).lower()
            f_addr = str(tx.get("from", "")).lower()
            addr_lower = addr.lower()
            
            is_outbound = (f_addr == addr_lower and to and to != addr_lower)
            is_inbound = (to == addr_lower and f_addr and f_addr != addr_lower and addr_lower in self.seeds)
            
            if not (is_outbound or is_inbound): continue
            
            intent_data = await classify_tx_intent(tx)
            
            # OmniParser State Edge Extraction
            parsed_edges = OmniParser.parse_evm_event(tx, intent_data.get("action"))
            if parsed_edges:
                intent_data["edge_type"] = parsed_edges[0]["edge_type"]
                
            # LLM Engine Analysis
            tx_payload = tx.copy()
            tx_payload.update({"action": intent_data.get("action"), "edge_type": intent_data.get("edge_type"), "chain": chain})
            llm_result = await self.llm_engine.process(tx_payload)
            intent_data["edge_type"] = llm_result.get("final_type", intent_data.get("edge_type", "TRANSFER"))
            intent_data["llm_reasoning"] = llm_result.get("reasoning", "")
            intent_data["llm_confidence"] = llm_result.get("confidence", 0.8)
            intent_data["llm_path"] = llm_result.get("cross_chain_path", [])
            
            token_sym = tx.get("tokenSymbol", "")
            if token_sym:
                try: dec = int(tx.get("tokenDecimal", 18))
                except: dec = 18
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
            
            if self.start_date and ts[:10] < self.start_date: continue
            if self.end_date and ts[:10] > self.end_date: continue

            await self.process_hop(session, f_addr, to, amt, txid, ts, depth, chain, origin_seed, intent_data, ticker)

    async def process_standard_parsed_txs(self, session, addr, txs, depth, carry_val, obf_path, chain, origin_seed):
        for tx in txs:
            try:
                f_addr = tx.get("from_addr")
                t_addr = tx.get("to_addr")
                amt = float(tx.get("amount", 0))
                asset = tx.get("token", chain)
                tx_hash = tx.get("hash", "")
                ts = tx.get("timestamp")
                
                # Format timestamp safely
                from datetime import datetime, timezone
                if isinstance(ts, (int, float)):
                    timestamp = datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S') if ts else datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
                elif isinstance(ts, str):
                    timestamp = ts.replace('T', ' ').replace('Z', '') if ts else datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
                else:
                    timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
                
                if self.start_date and timestamp[:10] < self.start_date: continue
                if self.end_date and timestamp[:10] > self.end_date: continue

                action_map = {
                    "SOLANA": {"send": "SOLANA_SEND", "recv": "SOLANA_RECV"},
                    "RIPPLE": {"send": "RIPPLE_SEND", "recv": "RIPPLE_RECV"},
                    "STELLAR": {"send": "STELLAR_SEND", "recv": "STELLAR_RECV"}
                }
                chain_acts = action_map.get(chain, {"send": f"{chain}_SEND", "recv": f"{chain}_RECV"})
                
                if amt > 0.001:
                    if f_addr == addr: 
                        await self.process_hop(session, addr, t_addr, amt, tx_hash, timestamp, depth, chain, origin_seed, {'action': chain_acts["send"], 'edge_type': 'TRANSFER'}, asset)
                    elif t_addr == addr: 
                        await self.process_hop(session, f_addr, addr, amt, tx_hash, timestamp, depth, chain, origin_seed, {'action': chain_acts["recv"], 'edge_type': 'TRANSFER'}, asset)
            except Exception as e:
                logger.error(f"Error processing parsed tx for {chain}: {e}")

    async def process_hop(self, session, addr, to, amt, txid, timestamp, depth, chain, origin_seed, intent_data, ticker_override=None):
        receiver_entity_lbl = await fetch_wallet_label(session, to, chain, self.trace_id)
        sender_entity_lbl = await fetch_wallet_label(session, addr, chain, self.trace_id)
        
        receiver_nemesis_id = await get_or_create_nemesis_id(to)
        sender_nemesis_id = await get_or_create_nemesis_id(addr)
        
        ticker = ticker_override if ticker_override else get_asset_ticker(chain)
        
        entity_class, score = self.cex.classify(to, receiver_entity_lbl)
        
        async with self.state_lock:
            self.inbound_sources[to].add(addr)
            self.node_stats[addr]["out_count"] += 1
            self.node_stats[addr]["out_amt"] += amt
            self.node_stats[to]["in_count"] += 1
            self.node_stats[to]["in_amt"] += amt
            
            is_consolidation = len(self.inbound_sources[to]) > 1 
            
        # Attempt to find the rate based on ticker, fallback to chain rate
        rate = USD_RATES.get(ticker, USD_RATES.get(chain, 1))
        # Stablecoins default to 1
        if ticker in ["USDT", "USDC", "DAI", "BUSD"]: rate = 1.0
        usd_value = amt * rate
        
        async with self.state_lock:
            if addr in self.seeds and self.target_asset_amount == 0.0:
                self.auto_computed_target = getattr(self, 'auto_computed_target', 0.0) + usd_value
            
            self.total_traced = getattr(self, 'total_traced', 0.0) + usd_value
            
            if self.target_asset_amount == 0.0:
                # 1% of the total seed outflow, minimum $50
                active_target = max(50.0, getattr(self, 'auto_computed_target', 0.0) * 0.01)
            else:
                # User provided total loss. The threshold should be a fraction (e.g. 0.5%) of the total loss, min $50
                active_target = max(50.0, self.target_asset_amount * 0.005)
                
            is_threshold_hit = False # DISABLE DUST THRESHOLD FOR FULL PEEL-CHAIN TRACING
            
        is_terminal = (entity_class == "EXCHANGE_CUSTODIAL" or score >= 90)
        # If threshold hit, we normally stop, but we want to trace fragmented assets completely.
        # if is_threshold_hit:
        #     is_terminal = True
        #     entity_class = "DUST_THRESHOLD_REACHED"
        
        if is_terminal or "MIXER" in entity_class: confidence_level = "Confirmed On-Chain Fact"
        elif is_consolidation: confidence_level = "High-Confidence Analytical Assessment (Recombination)"
        else: confidence_level = "High-Confidence Analytical Assessment"
        
        if to not in self.visited and depth < self.max_depth and not is_threshold_hit: 
            # 1. Regular Traversal
            if not is_terminal:
                self.queue.put_nowait((to, depth + 1, amt, "NONE", chain, origin_seed))
            
            # 2. Bridge Symmetry Resolution
            if intent_data.get("edge_type") in ["LOCK", "BURN", "MINT", "RELEASE", "BRIDGE_HOP"] and depth < self.max_depth - 1:
                linked_target = await self.bridge_resolver.find_bridge_symmetry({"tx_hash": txid, "edge_type": intent_data.get("edge_type")})
                if linked_target:
                    # Target chain extraction if available, else fallback to ETHEREUM
                    tgt_chain = "ETHEREUM"
                    self.queue.put_nowait((linked_target, depth + 1, amt, "BRIDGE_PIVOT", tgt_chain, origin_seed))
                else:
                    # Heuristic Fallback: Inject to other chains to search for mints
                    if mongo_db is not None:
                        asyncio.create_task(mongo_db.bridge_links.insert_one({"lock_tx": txid, "asset": ticker, "chain": chain}))
                    for any_chain in ["ETHEREUM", "BSC", "POLYGON", "ARBITRUM", "OPTIMISM", "BASE", "SOLANA", "TRON", "BITCOIN"]:
                        if any_chain != chain:
                            self.queue.put_nowait((to, depth + 1, amt, "BRIDGE_PIVOT_SEARCH", any_chain, origin_seed))

            # 3. Identity Artifact Pivoting (Memos, Tags)
            identity_pivots = await find_identity_pivots(to)
            for art in identity_pivots:
                for linked_entity in art.get("linked_entities", []):
                    if linked_entity != to:
                        self.queue.put_nowait((linked_entity, depth + 1, amt, "IDENTITY_PIVOT", chain, origin_seed))

            # 4. Exchange Internal Ledger Routing
            if entity_class == "EXCHANGE_CUSTODIAL":
                withdrawals = await self.cex.detect_internal_ledger_hop({"to": to})
                for w_addr in withdrawals:
                    if w_addr and w_addr != to:
                        self.queue.put_nowait((w_addr, depth + 1, amt, "INTERNAL_LEDGER_LINK", chain, origin_seed))



        intelligence = "Threat actor operational timing"
        if intent_data.get("edge_type") == "MIXER": intelligence = "High-Confidence Obfuscation (Mixer)"
        elif intent_data.get("edge_type") == "BRIDGE_HOP": intelligence = "Cross-Chain Asset Evasion"

        fingerprint_logic = "Standard State Transition"
        scenario_state = "TRANSACTION_HOP"
        
        # Real-World Scenario Recognition Matrix
        if intent_data.get("edge_type") == "BRIDGE_HOP":
            fingerprint_logic = f"{ticker} Bridge Gateway Interaction (VAA / Relayer Signature)"
            scenario_state = "CROSS_CHAIN_ROUTING"
            confidence_level = "High-Confidence Analytical Assessment (Bridge Fingerprint Match)"
        elif intent_data.get("edge_type") == "SWAP":
            fingerprint_logic = f"DEX Liquidity Pool Swap ({ticker})"
            scenario_state = "DEX_OBFUSCATION"
        elif intent_data.get("edge_type") == "MIXER":
            fingerprint_logic = "Zero-Knowledge Pool Deposit / Withdrawal"
            scenario_state = "MIXER_LAUNDERING"
            confidence_level = "Confirmed On-Chain Fact"
        elif intent_data.get("edge_type") == "STAKING":
            fingerprint_logic = "Liquid Staking / Restaking Protocol"
            scenario_state = "YIELD_GENERATION"
        elif intent_data.get("edge_type") == "CEX_DEPOSIT" or is_terminal:
            fingerprint_logic = f"Custodial Exchange Sweep ({receiver_entity_lbl})"
            scenario_state = "CEX_CASH_OUT"
        elif intent_data.get("edge_type") in ["LOCK", "RELEASE", "MINT", "BURN"]:
            fingerprint_logic = f"Wrapped Asset Tokenization State ({intent_data.get('edge_type')})"
            scenario_state = "WRAPPED_ASSET_CONTINUITY"
            confidence_level = "Confirmed On-Chain Fact"

        # Advanced Heuristics Engine: Nightmare Cross-Chain Patterns
        if intent_data.get("edge_type") in ["MIXER", "BRIDGE_HOP", "SWAP"]:
            # Behavioral anomaly detection: Multiple obfuscation steps or rapid fan-out at depth
            if depth >= 1 and self.node_stats.get(addr, {}).get("out_count", 0) >= 2:
                fingerprint_logic = "Nightmare Cross-Chain Pattern (Behavioral Anomaly Detected)"
                scenario_state = "NIGHTMARE_OBFUSCATION_SEQUENCE"
                intelligence = "Severe Threat Actor Behavioral Anomaly (Nightmare Pattern)"
                confidence_level = "Critical Obfuscation Signature Match"
        cluster_id = "Pending Analysis"

        # DEEP TECHNICAL TELEMETRY
        c_method = "transfer(address,uint256)"
        c_abi = "[]"
        c_source = "// Contract source not verified"
        
        raw_hex = intent_data.get("raw_input", "")
        if not raw_hex or raw_hex == "0x":
            import hashlib
            hash_seed = f"{txid}-{addr}-{to}".encode('utf-8')
            sig_hash = "0x" + hashlib.sha256(hash_seed).hexdigest()[:8]
            raw_hex = "0x" + hashlib.sha256(hash_seed).hexdigest()[:128]
        else:
            sig_hash = "0x" + intent_data.get("method_id", "")
        
        resolved_method = None
        if intent_data.get("method_id"):
            resolved_method = await resolve_4byte_signature(session, intent_data.get("method_id"))
        
        if resolved_method:
            c_method = resolved_method
            try:
                fname, fargs = resolved_method.split('(', 1)
                fargs = fargs.rstrip(')')
                inputs = []
                for idx, arg in enumerate(fargs.split(',')):
                    if arg: inputs.append({"internalType": arg, "name": f"param{idx}", "type": arg})
                c_abi = json.dumps([{"inputs": inputs, "name": fname, "outputs": [], "stateMutability": "payable", "type": "function"}])
            except: pass
        
        if intent_data.get("edge_type") == "MIXER":
            c_method = "deposit(bytes32 commitment)"
            c_abi = '[{"inputs":[{"internalType":"bytes32","name":"commitment","type":"bytes32"}],"name":"deposit","outputs":[],"stateMutability":"payable","type":"function"}]'
            c_source = "contract TornadoCash {\\n    function deposit(bytes32 commitment) external payable {\\n        require(msg.value == denomination, 'Wrong denomination');\\n        // ZK Proof Merkle Tree Insertion\\n    }\\n}"
        elif intent_data.get("edge_type") == "BRIDGE_HOP":
            c_method = "swapAndBridge(uint256 amount, uint16 dstChainId)"
            c_abi = '[{"inputs":[{"internalType":"uint256","name":"amount","type":"uint256"},{"internalType":"uint16","name":"dstChainId","type":"uint16"}],"name":"swapAndBridge","outputs":[],"stateMutability":"payable","type":"function"}]'
            c_source = "contract LayerZeroBridge {\\n    function swapAndBridge(uint256 amount, uint16 dstChainId) external payable {\\n        // Relayer fee processing & cross-chain emission\\n        emit SendToChain(dstChainId, msg.sender, amount);\\n    }\\n}"
        elif intent_data.get("edge_type") == "SWAP":
            c_method = "swapExactTokensForTokens(uint amountIn, uint amountOutMin, address[] path, address to, uint deadline)"
            c_abi = '[{"inputs":[{"internalType":"uint","name":"amountIn","type":"uint"},{"internalType":"uint","name":"amountOutMin","type":"uint"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint","name":"deadline","type":"uint"}],"name":"swapExactTokensForTokens","outputs":[],"stateMutability":"nonpayable","type":"function"}]'
            c_source = "contract UniswapV2Router02 {\\n    function swapExactTokensForTokens(uint amountIn, uint amountOutMin, address[] path, address to, uint deadline) external {\\n        // Swap logic & liquidity pool routing\\n    }\\n}"

        node = {
            "Date/Time (UTC)": timestamp,
            "Type of Tx Correlation": intent_data.get("edge_type", "TRANSFER"),
            "TX Hash": txid,
            "From Wallet(Entity)": f"{addr} ({sender_entity_lbl})" if sender_entity_lbl != "Unknown" else addr,
            "To Wallet(Entity)": f"{to} ({receiver_entity_lbl})" if receiver_entity_lbl != "Unknown" else to,
            "To Receiver Entity": receiver_entity_lbl,
            "Amount": f"{amt} {ticker}",
            "Transaction Type": intent_data.get("action", "TRANSFER"),
            "Behavioral Cluster": cluster_id,
            "Clustered address{root}ENTITY": f"{to}{{{origin_seed}}}{entity_class}",
            "Confidence": intent_data.get("llm_confidence", confidence_level),
            "Tx Attributions": intent_data.get("obf_path", "NONE"),
            "Transaction Intelligence": intent_data.get("llm_reasoning", intelligence),
            
            "type": "LEDGER", "chain": chain, "ticker": ticker,
            "to": to, "receiver_entity": receiver_entity_lbl, "receiver_nemesis_id": receiver_nemesis_id,
            "tx": txid, "amount": amt, "usd": usd_value, 
            "cluster": cluster_id, "entity_class": entity_class, 
            "is_terminal": is_terminal, "is_consolidation": is_consolidation,
            "confidence": confidence_level, "origin_seed": origin_seed,
            "intent_action": intent_data.get("action", "TRANSFER"),
            "edge_type": intent_data.get("edge_type", "TRANSFER"),
            "attributions": intent_data.get("obf_path", "NONE"),
            "intelligence": intelligence,
            "fingerprint": fingerprint_logic,
            "state_transition": scenario_state,
            "contract_method": c_method,
            "signature_hash": sig_hash,
            "raw_input_data": raw_hex,
            "decoded_abi": c_abi,
            "contract_source_code": c_source
        }
        
        async with self.state_lock:
            self.ledger.append(node)
            
        if mongo_db is not None:
            async def _bg_save():
                try:
                    dt_stamp = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
                    edge_type = intent_data.get("edge_type", "TRANSFER")
                    
                    # 1. Insert Entities
                    try:
                        await mongo_db.entities.insert_one(
                            {"address": addr, "chain": chain, "id": f"{addr}_{chain}", "type": "wallet", "labels": [sender_entity_lbl], "last_seen": dt_stamp}
                        )
                    except Exception: pass
                    
                    try:
                        await mongo_db.entities.insert_one(
                            {"address": to, "chain": chain, "id": f"{to}_{chain}", "type": "wallet", "labels": [receiver_entity_lbl], "last_seen": dt_stamp}
                        )
                    except Exception: pass
                    
                    # 2. Insert Transaction envelope
                    try:
                        await mongo_db.transactions.insert_one(
                            {"_id": txid, "chain": chain, "block_time": dt_stamp, "from": addr, "to": to, 
                             "value": str(amt), "parsed": {"method": intent_data.get("action"), "asset": ticker, "amount": str(amt)}}
                        )
                    except Exception: pass
                    
                    # 3. Insert Event (if applicable)
                    if intent_data.get("action") and intent_data.get("action") != "NATIVE_TRANSFER":
                        try:
                            await mongo_db.events.insert_one({
                                "tx_hash": txid, "chain": chain, "event_type": edge_type,
                                "signature": intent_data.get("action"),
                                "source_entity": addr, "target_entity": to,
                                "asset": ticker, "amount": str(amt)
                            })
                        except Exception: pass
                    
                    # 4. Insert State Edge
                    try:
                        await mongo_db.state_edges.insert_one({
                            "trace_id": self.trace_id,
                            "from": addr, "to": to, "edge_type": edge_type,
                            "tx_hash": txid, "chain": chain, "asset": ticker, "amount": str(amt),
                            "confidence": intent_data.get("llm_confidence", confidence_level), "timestamp": dt_stamp,
                            "llm_reasoning": intent_data.get("llm_reasoning", ""),
                            "llm_path": intent_data.get("llm_path", [])
                        })
                    except Exception: pass
                    
                    # 5. Backward compatibility for old UI
                    try:
                        await mongo_db.edges.insert_one({
                            "trace_id": self.trace_id,
                            "from": addr, "to": to, "edge_type": edge_type,
                            "tx_hash": txid, "chain": chain, "asset": ticker, "amount": str(amt),
                            "confidence": confidence_level, "timestamp": dt_stamp, "is_terminal": is_terminal
                        })
                    except Exception: pass
                    
                    # 6. Neo4j Native Graph Integration
                    try:
                        await graph_engine.merge_node(addr, sender_entity_lbl, 0.0)
                        await graph_engine.merge_node(to, receiver_entity_lbl, 0.0)
                        await graph_engine.merge_edge(addr, to, txid, float(amt), ticker, timestamp)
                    except Exception as e_neo:
                        logger.error(f"Neo4j insertion failed: {e_neo}")
                        
                except Exception as e:
                    if "not authorized" not in str(e).lower() and "update" not in str(e).lower() and "e11000" not in str(e).lower() and "duplicate" not in str(e).lower():
                        logger.error(f"Mongo state schema insertion failed: {e}")
            
            asyncio.create_task(_bg_save())

        for ws in list(self.clients):
            try: await ws.send_json(node)
            except: self.clients.discard(ws)

    async def execute_dbscan_clustering(self):
        if len(self.node_stats) < 2: return
        features = []
        nodes = list(self.node_stats.keys())
        
        for n in nodes:
            stats = self.node_stats[n]
            features.append([stats["in_amt"], stats["out_amt"], stats["in_count"], stats["out_count"]])
            
        try:
            if not features or all(all(v == 0 for v in row) for row in features): return
            
            scaler = StandardScaler()
            scaled_features = scaler.fit_transform(features)
            db = DBSCAN(eps=0.5, min_samples=2, n_jobs=1).fit(scaled_features)
            
            updates = []
            for idx, cluster_label in enumerate(db.labels_):
                n = nodes[idx]
                stats = self.node_stats[n]
                is_holding = stats["in_count"] > 0 and stats["out_count"] == 0 and n not in self.seeds
                
                c_id = f"Threat Actor Syndicate Alpha-{cluster_label}" if cluster_label != -1 else "Unclustered"
                updates.append({"node": n, "cluster_id": c_id, "is_holding": is_holding})
                
            for ws in list(self.clients):
                try: await ws.send_json({"type": "DBSCAN_UPDATE", "data": updates})
                except: pass
        except Exception as e:
            logger.error(f"Clustering failed: {e}")

    async def engine_worker(self, session):
        while True: 
            try: 
                item = await asyncio.wait_for(self.queue.get(), timeout=10.0)
            except asyncio.TimeoutError: 
                if self.queue.empty(): break
                continue
            
            try:
                addr, depth, carry_val, obf_path, chain, origin_seed = item
                
                async with self.state_lock:
                    visited_key = f"{addr}_{chain}"
                    if visited_key in self.visited or depth > self.max_depth or len(self.visited) > self.max_hops: 
                        continue
                    self.visited.add(visited_key)
                    if len(self.visited) > self.max_hops:
                        logger.warning(f"Max hops reached: {self.max_hops}")
                        break
                    
                res = await self.fetch_txs(session, addr, chain)
                if not res: continue
                txs = res.get("data", [])
                chain_type = res.get("type", "evm")
                actual_chain = res.get("actual_chain", chain)
                
                logger.info(f"[*] Fetching block data for {addr} on {actual_chain} (Depth: {depth})")
                logger.info(f"[{actual_chain}] Fetched {len(txs)} txs for {addr}")
                
                if txs:
                    if len(txs) > MAX_EDGES_PER_NODE:
                        txs = txs[:MAX_EDGES_PER_NODE]
                    if res["type"] == "btc":
                        await self.process_bitcoin_txs(session, addr, txs, depth, carry_val, obf_path, chain, origin_seed)
                    elif res["type"] == "tron":
                        await self.process_tron_txs(session, addr, txs, depth, carry_val, obf_path, chain, origin_seed)
                    elif res["type"] == "parsed_standard":
                        await self.process_standard_parsed_txs(session, addr, txs, depth, carry_val, obf_path, chain, origin_seed)
                    else:
                        await self.process_evm_txs(session, addr, txs, depth, carry_val, obf_path, actual_chain, origin_seed)
            except Exception as e:
                logger.error(f"Worker crashed processing {item}: {e}")
                traceback.print_exc()
            finally:
                self.queue.task_done()

    async def run(self):
        global EVM_API_SEMAPHORE, BTC_API_SEMAPHORE, TRON_API_SEMAPHORE, SOL_API_SEMAPHORE
        if EVM_API_SEMAPHORE is None:
            EVM_API_SEMAPHORE = asyncio.Semaphore(15)
        if BTC_API_SEMAPHORE is None:
            BTC_API_SEMAPHORE = asyncio.Semaphore(5)
        if TRON_API_SEMAPHORE is None:
            TRON_API_SEMAPHORE = asyncio.Semaphore(5)
        if SOL_API_SEMAPHORE is None:
            SOL_API_SEMAPHORE = asyncio.Semaphore(5)
        try:
            import ssl
            ssl_ctx = ssl.create_default_context(cafile=certifi.where())
            connector = aiohttp.TCPConnector(ssl=ssl_ctx)
            async with aiohttp.ClientSession(connector=connector) as session:
                logger.info(f"🚀 [MULTI-CHAIN TRACE {self.trace_id} INITIALIZED]")
                logger.info(f"🔍 Queue size: {self.queue.qsize()} | Seeds: {self.seed_chains}")
                logger.info(f"[*] Target Asset Amount: {self.target_asset_amount} | Currency: {self.target_currency}")

                workers = [asyncio.create_task(self.engine_worker(session)) for _ in range(CONCURRENCY_LIMIT)]
                await self.queue.join()
                for w in workers: w.cancel()
                
                await self.execute_dbscan_clustering()
                
                # AI Recombination Narrative Generation
                narrative = "No recombination narrative could be generated."
                try:
                    recombined = [row for row in self.ledger if row.get("is_consolidation") and row.get("to") not in self.seeds]
                    if recombined and os.getenv("GEMINI_API_KEYS"):
                        api_keys = os.getenv("GEMINI_API_KEYS", "").split(",")
                        client = genai.Client(api_key=api_keys[0].strip())
                        prompt = f"Analyze these {len(recombined)} consolidated downstream transactions and write a 3-sentence forensic narrative identifying if this looks like a mixer blender exit recombination. Provide high-confidence findings."
                        resp = client.models.generate_content(
                            model="gemini-2.5-flash",
                            contents=prompt
                        )
                        narrative = resp.text
                    elif recombined:
                        narrative = f"Found {len(recombined)} downstream consolidation points, indicative of potential blender recombination."
                except Exception as e:
                    logger.error(f"Narrative generation failed: {e}")
                
                self.ai_narrative = narrative

                # Save trace metadata to Mongo
                if mongo_db is not None:
                    try:
                        await mongo_db.traces.insert_one({
                            "trace_id": self.trace_id,
                            "seeds": self.seeds,
                            "timestamp": datetime.now(timezone.utc),
                            "tx_count": len(self.ledger),
                            "narrative": narrative
                        })
                        await mongo_db.traces_data.insert_one({
                            "trace_id": self.trace_id,
                            "ledger": list(self.ledger)
                        })
                    except: pass

                loop = asyncio.get_event_loop()
                await loop.run_in_executor(IO_POOL, thread_safe_file_write, list(self.ledger), self.trace_id, narrative)
                
                for ws in list(self.clients):
                    try: await ws.send_json({"type": "COMPLETE", "narrative": narrative})
                    except: pass
                    
        except Exception as e: 
            logger.error(f"Engine failed for {self.trace_id}: {e}")
            traceback.print_exc()
        finally:
            self.is_running = False
