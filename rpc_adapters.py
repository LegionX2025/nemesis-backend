import os
import time
import logging
import requests
from pymongo import MongoClient
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

# Import the shared Godmode DB
from godmode_tracer import godmode_db

# Constants
ETHERSCAN_API_KEY = "YourApiKeyToken"
TRONSCAN_API_BASE = "https://apilist.tronscan.org/api"

def safe_get(url: str, params: Dict = None) -> Dict:
    try:
        r = requests.get(url, params=params, timeout=15)
        return r.json()
    except Exception as e:
        logger.error(f"RPC Adapter request failed: {e}")
        return {}

class EVMAdapter:
    def sync_address(self, address: str):
        if not godmode_db.is_connected(): return
        
        url = f"https://api.etherscan.io/api?module=account&action=txlist&address={address}&startblock=0&endblock=99999999&sort=desc"
        data = safe_get(url)
        txs = data.get("result", [])
        
        if not isinstance(txs, list): return
        
        for tx in txs:
            if tx.get("isError") != "0": continue
            f, t, amt_raw, txid, ts_raw = tx.get("from"), tx.get("to"), tx.get("value"), tx.get("hash"), tx.get("timeStamp")
            
            try: amt = float(amt_raw) / 1e18
            except: amt = 0.0
            
            ts = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(int(ts_raw))) if ts_raw else ""
            
            if f and t and amt > 0:
                godmode_db.state_edges.update_one(
                    {"tx_hash": txid, "from": f, "to": t},
                    {"$set": {
                        "from": f,
                        "to": t,
                        "amount": amt,
                        "asset": "ETH",
                        "chain": "ETHEREUM",
                        "timestamp": ts,
                        "edge_type": "TRANSFER",
                        "tx_hash": txid
                    }},
                    upsert=True
                )

class SolanaAdapter:
    def sync_address(self, address: str):
        if not godmode_db.is_connected(): return
        
        # Using public Solana RPC (Rate limited heavily)
        url = "https://api.mainnet-beta.solana.com"
        headers = {"Content-Type": "application/json"}
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getSignaturesForAddress",
            "params": [address, {"limit": 50}]
        }
        
        try:
            r = requests.post(url, json=payload, headers=headers, timeout=15)
            sigs = r.json().get("result", [])
            for sig_info in sigs:
                # We would need to fetch the parsed transaction to get from/to/amount
                # This is highly rate limited so we'll mock the insertion for the sake of the engine schema
                pass
        except Exception as e:
            logger.error(f"Solana RPC failed: {e}")

class TronAdapter:
    def sync_address(self, address: str):
        if not godmode_db.is_connected(): return
        
        data = safe_get(f"{TRONSCAN_API_BASE}/transaction", params={"address": address, "limit": 50})
        txs = data.get("data", [])
        
        if not isinstance(txs, list): return
        
        for tx in txs:
            f = tx.get("ownerAddress")
            t = tx.get("toAddress")
            txid = tx.get("hash")
            ts_raw = tx.get("timestamp")
            amt = tx.get("amount", 0)
            
            try: amt_float = float(amt) / 1e6
            except: amt_float = 0.0
            
            ts = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(int(ts_raw)/1000)) if ts_raw else ""
            
            if f and t and amt_float > 0:
                 godmode_db.state_edges.update_one(
                    {"tx_hash": txid, "from": f, "to": t},
                    {"$set": {
                        "from": f,
                        "to": t,
                        "amount": amt_float,
                        "asset": "TRX",
                        "chain": "TRON",
                        "timestamp": ts,
                        "edge_type": "TRANSFER",
                        "tx_hash": txid
                    }},
                    upsert=True
                )

class OmniChainSync:
    @staticmethod
    def sync_all(address: str):
        """Dispatches to the correct chain adapter based on address format."""
        logger.info(f"Syncing state transitions into MongoDB for {address}")
        
        if address.startswith("0x"):
            EVMAdapter().sync_address(address)
        elif address.startswith("T") and len(address) == 34:
            TronAdapter().sync_address(address)
        elif len(address) >= 32 and not address.startswith("0x"):
            # Very basic assumption for Solana/BTC for now
            SolanaAdapter().sync_address(address)
