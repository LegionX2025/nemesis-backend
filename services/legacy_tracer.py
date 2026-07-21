import os
import time
import json
import logging
import requests
from datetime import datetime, timezone
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import networkx as nx
import pandas as pd
import numpy as np
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
from typing import List, Dict, Any, Optional, Tuple

try:
    from godmode_tracer import GodmodeTracer, godmode_db
except ImportError:
    godmode_db = None
    GodmodeTracer = None

try:
    from services.tracing_workflows import build_tracer_workflow, TracerState
except ImportError:
    build_tracer_workflow = None

logger = logging.getLogger(__name__)

# --- CONFIGURATION ---
TOKENVIEW_API_KEY = os.getenv("TOKENVIEW_API_KEY", "Rhl2uJqCsPkNaog2oL4q")
TRONSCAN_API_BASE = "https://apilist.tronscan.org/api"
TOKENVIEW_TRX_BASE = "https://trx.tokenview.io/api"
TOKENVIEW_USDT_BASE = "https://usdt.tokenview.io/api"

MAX_HOPS = 1000 
PAGE_SIZE = 50
DELAY = 0.35 

EXCHANGE_KEYWORDS = ["binance", "huobi", "okx", "okex", "kucoin", "gate", "coinbase", "kraken", "bitfinex", "poloniex", "mxc", "bitstamp", "bingx"]
MIXER_KEYWORDS = ["tornado", "mixer", "railgun", "avalon", "blender", "0xd90e2f925da726b50c4ed8d0fb90ad053324f31b"]

SIGNATURE_REGISTRY = {
    # --- BASIC ERC20 / TRC20 ---
    "a9059cbb": "Transfer (ERC20/TRC20)",
    "23b872dd": "TransferFrom (ERC20/TRC20)",
    "095ea7b3": "Approve Spending Limit",
    "00000000": "Native Transfer / Fallback",
    
    # --- ASSET WRAPPERS (WETH, WBTC, WMATIC) ---
    "d0e30db0": "Deposit (Wrap Native Asset)",
    "2e1a7d4d": "Withdraw (Unwrap to Native)",

    # --- DEX ROUTERS (Uniswap V2, SushiSwap, PancakeSwap) ---
    "38ed1739": "SwapExactTokensForTokens (Uniswap V2/Sushi)",
    "18cbafe5": "SwapExactTokensForETH (Uniswap V2/Sushi)",
    "4a25d94a": "SwapTokensForExactTokens (Uniswap V2/Sushi)",
    "7ff36ab5": "SwapExactETHForTokens (Uniswap V2/Sushi)",
    "fb3bdb41": "SwapETHForExactTokens (Uniswap V2/Sushi)",
    "5c11d795": "SwapExactTokensForTokensSupportingFeeOnTransferTokens",
    "b6f9de95": "SwapExactETHForTokensSupportingFeeOnTransferTokens",
    "791ac947": "SwapExactTokensForETHSupportingFeeOnTransferTokens",
    "e8e33700": "AddLiquidity (DEX Pool Provision)",
    "f305d719": "AddLiquidityETH (DEX Pool Provision)",
    "baa2abde": "RemoveLiquidity (DEX Pool Drain)",
    "02751cec": "RemoveLiquidityETH (DEX Pool Drain)",

    # --- DEX ROUTERS (Uniswap V3) ---
    "414bf389": "ExactInputSingle (Uniswap V3 Swap)",
    "c04b8d59": "ExactInput (Uniswap V3 Swap Route)",
    "db3e2198": "ExactOutputSingle (Uniswap V3 Swap)",
    "f28c0498": "ExactOutput (Uniswap V3 Swap Route)",
    "12210e8a": "Multicall (Uniswap V3 Routing / Batch)",
    "df8de3e7": "Multicall (Generic Contract Batching)",

    # --- DEX ROUTERS (1inch V4 / V5, 0x Protocol) ---
    "12aa3caf": "Swap (1inch V5 Router)",
    "7c025200": "Swap (1inch V4 Router)",
    "e449022e": "Unoswap (1inch V4/V5 Optimized Route)",
    "415565b0": "TransformERC20 (0x Protocol Swap)",
    "8182b61f": "FillQuote (0x Protocol Swap)",

    # --- DEX ROUTERS (Curve Finance) ---
    "3df02124": "Exchange (Curve StableSwap)",
    "5b41b908": "Exchange_Underlying (Curve StableSwap)",
    "0b407b46": "Add_Liquidity (Curve Finance Pool)",

    # --- CROSS-CHAIN BRIDGES ---
    "8b9e4f93": "BridgeOut (Stargate Finance Router)",
    "a3bc6e0e": "BridgeIn (Cross-Chain Settlement)",
    "3d12a85a": "DepositFor (Polygon PoS Bridge Deposit)",
    "e3dec8fb": "DepositERC20 (Arbitrum Nitro Bridge Deposit)",
    "439370b1": "DepositEth (Arbitrum Nitro Native Bridge)",
    "7324dd78": "SendToL2 (Hop Protocol Bridge Out)",
    "0175b1c4": "Deposit (Across Protocol Bridge)",
    "919cefa5": "AnySwapOutUnderlying (Multichain Bridge)",
    "dc53587b": "AnySwapOut (Multichain Bridge)",
    "2cdddfcc": "RelayMessage (General Message Passing Bridge)",

    # --- PRIVACY MIXERS ---
    "b6b55f25": "Deposit (Tornado Cash / Mixer Protocol)",
    "21a0adb6": "Withdraw (Tornado Cash / Mixer Protocol)",
    "e3ceb028": "Transact (Railgun Privacy Protocol)",
    "7fcd881e": "Deposit (Aztec Privacy Protocol)",

    # --- NFT PROTOCOLS & MARKETPLACES ---
    "fb0f3ee1": "FulfillAdvancedOrder (Seaport / OpenSea)",
    "b3a34c4c": "FulfillAvailableOrders (Seaport / OpenSea)",
    "ed98a574": "FulfillBasicOrder (Seaport / OpenSea)",
    "e4dd1e23": "SafeTransferFrom (ERC1155 NFT Transfer)",
    "2eb2c2d6": "SafeBatchTransferFrom (ERC1155 NFT Batch)",
    "42842e0e": "SafeTransferFrom (ERC721 NFT Transfer)",
    "1249c58b": "Mint (NFT / Token Minting)",
    "40c10f19": "Mint (Generic Token Minting)",
    "42966c68": "Burn (Token Burn Execution)",
    "893d20e8": "Burn (Generic Token Burn Execution)",

    # --- CENTRALIZED EXCHANGE (CEX) BEHAVIORS ---
    "e523f4f1": "CEX Hot Wallet Sweep / Forwarder Execution",
    "f242432a": "SafeTransferFrom (CEX/NFT Fallback)"
}

session = requests.Session()
retries = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504], allowed_methods=["GET"])
session.mount('http://', HTTPAdapter(max_retries=retries))
session.mount('https://', HTTPAdapter(max_retries=retries))

def safe_get(url: str, params: Optional[Dict] = None, headers: Optional[Dict] = None, timeout: int = 15) -> Dict[str, Any]:
    try:
        r = session.get(url, params=params, headers=headers, timeout=timeout)
        try: return {"status": r.status_code, "json": r.json()}
        except ValueError: return {"status": r.status_code, "text": r.text[:2000]}
    except requests.exceptions.RequestException as e:
        logger.warning(f"Request failed for {url}: {e}")
        return {"error": str(e), "status": 0}

def detect_chain(address: str) -> str:
    """Omni-chain detection routing."""
    address = address.strip()
    if address.startswith("0x") and len(address) == 42: return "ETHEREUM"
    if address.startswith("T") and len(address) == 34: return "TRON"
    if address.startswith("1") or address.startswith("3") or address.startswith("bc1"): return "BITCOIN"
    return "UNKNOWN"

def resolve_signature(input_data: str) -> str:
    """Decodes advanced smart contract interactions utilizing the comprehensive registry."""
    if not input_data or input_data == "0x" or input_data == "00000000": return "Native Transfer"
    sig = input_data[:8].lower()
    if input_data.startswith("0x"): sig = input_data[2:10].lower()
    return SIGNATURE_REGISTRY.get(sig, f"Unknown Contract Call (Sig: 0x{sig})")

def parse_tronscan_tx_obj(tx: Dict) -> Dict:
    from_addr = tx.get("ownerAddress") or tx.get("fromAddress") or tx.get("from")
    to_addr = tx.get("toAddress") or tx.get("to")
    amt = None
    if "amount" in tx and tx.get("amount") is not None:
        try: amt = float(tx.get("amount")) / 1_000_000
        except ValueError: amt = tx.get("amount")
    txid = tx.get("hash") or tx.get("txID") or tx.get("transactionHash")
    
    ts = tx.get("block_timestamp") or tx.get("timestamp") or tx.get("rawData", {}).get("timestamp")
    ts_iso = str(ts)
    try:
        if isinstance(ts, (int, float)):
            ts_seconds = ts / 1000 if ts > 1e12 else ts
            ts_iso = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(ts_seconds))
    except Exception: pass
    
    raw_data = tx.get("raw_data", {}).get("contract", [{}])[0].get("parameter", {}).get("value", {})
    input_data = raw_data.get("data", "")
    behavior = resolve_signature(input_data)

    return {"from": from_addr, "to": to_addr, "amount": amt, "txid": txid, "timestamp": ts_iso, "behavior": behavior, "raw": tx}

def has_entity_keyword(obj: Any, keywords: List[str]) -> Optional[str]:
    try:
        txt = json.dumps(obj).lower()
        for kw in keywords:
            if kw in txt: return kw
        return None
    except Exception: return None

def analyze_mission_context(text: str) -> dict:
    """Simulates NLP to extract mission directives and objectives from user input."""
    text_lower = text.lower()
    goals = []
    
    if "recover" in text_lower or "trace" in text_lower: goals.append("Trace stolen assets and map recovery endpoints.")
    if "identif" in text_lower or "actor" in text_lower or "suspect" in text_lower: goals.append("Execute threat actor identification & clustering.")
    if "court" in text_lower or "enforcement" in text_lower or "subpoena" in text_lower: goals.append("Generate court-ready evidentiary ledger & CEX targets.")
    if "mixer" in text_lower or "tornado" in text_lower: goals.append("Perform cold-trail signature analysis to demix obfuscated pathways.")
    if "audit" in text_lower or "compliance" in text_lower: goals.append("Conduct deep forensic compliance audit.")

    if not goals:
        goals = ["Omni-Chain Asset Tracing", "CEX Terminal Identification", "Evidentiary Chain Documentation"]

    return {
        "raw_prompt": text,
        "primary_objectives": goals,
        "summary": f"Mission deployment authorized. Tracking {len(goals)} primary directives across the specified omni-chain seed vectors. AI clustering and downstream sweep logic engaged."
    }

class Tracer:
    def __init__(self):
        self.G = nx.DiGraph()
        self.raw: Dict[str, Dict] = {}
        self.evidence_ledger = []

    def add_edge(self, src: str, dst: str, amount: float = 0.0, txid: str = "", timestamp: str = "", token: str = "ASSET", behavior: str = "Transfer") -> None:
        for node in (src, dst):
            if not self.G.has_node(node): self.G.add_node(node)
                
        edge_data = {"txid": txid, "timestamp": timestamp, "amount": amount, "token": token, "behavior": behavior}
        self.evidence_ledger.append({"from": src, "to": dst, **edge_data})

        if self.G.has_edge(src, dst):
            self.G[src][dst]["weight"] += (amount or 0.0)
            self.G[src][dst]["count"] += 1
            if "tx_history" not in self.G[src][dst]: self.G[src][dst]["tx_history"] = []
            self.G[src][dst]["tx_history"].append(edge_data)
        else:
            self.G.add_edge(src, dst, weight=(amount or 0.0), count=1, tx_history=[edge_data], token=token)

    def fetch_and_store_tron(self, address: str) -> None:
        self.raw.setdefault(address, {})
        self.raw[address]["tv_search"] = safe_get(f"{TOKENVIEW_TRX_BASE}/search/{address}")
        time.sleep(DELAY)
        self.raw[address]["tronscan_account"] = safe_get(f"{TRONSCAN_API_BASE}/account", params={"address": address})
        time.sleep(DELAY)
        self.raw[address]["tronscan_txs"] = safe_get(f"{TRONSCAN_API_BASE}/transaction", params={"address": address, "limit": 100, "sort": "-timestamp"})
        time.sleep(DELAY)
        url = f"{TOKENVIEW_USDT_BASE}/usdt/addresstxlist/{address}/1/50"
        if TOKENVIEW_API_KEY: url += f"?apikey={TOKENVIEW_API_KEY}"
        self.raw[address]["tv_usdt_txlist"] = safe_get(url)
        time.sleep(DELAY)

    def trace_from(self, start_addresses: List[str], max_hops: int = 1000) -> None:
        queue: List[Tuple[str, int]] = []
        for addr in start_addresses:
            self.G.add_node(addr)
            queue.append((addr, 0))
            
        visited = set()

        while queue:
            addr, hop = queue.pop(0)
            if hop > max_hops or addr in visited: continue
            visited.add(addr)

            chain = detect_chain(addr)
            if chain == "UNKNOWN":
                logger.warning(f"Unknown chain format for address: {addr}")
                continue

            logger.info(f"Tracing Node [{chain}]: {addr} (Hop {hop})")

            if chain == "TRON":
                tv_search = self.raw.get(addr, {}).get("tv_search")
                tronscan_acct = self.raw.get(addr, {}).get("tronscan_account")
                is_custodial = has_entity_keyword(tv_search, EXCHANGE_KEYWORDS) or has_entity_keyword(tronscan_acct, EXCHANGE_KEYWORDS)
                
                # We DO NOT STOP tracing at exchanges. We continue downstream to trace sweeps and consolidations.
                if is_custodial:
                    logger.info(f"[!] CUSTODIAL NODE ({addr}). Continuing trace to map downstream disbursements and sweeps.")

                try: self.fetch_and_store_tron(addr)
                except Exception as e:
                    logger.error(f"Failed to fetch TRON data for {addr}: {e}")
                    continue

                # TRX Flows
                txs_resp = self.raw[addr].get("tronscan_txs", {})
                txs = []
                if isinstance(txs_resp, dict) and "json" in txs_resp:
                    txs = txs_resp["json"].get("data") or txs_resp["json"].get("transactions") or txs_resp["json"]
                if isinstance(txs, list):
                    for tx in txs:
                        n = parse_tronscan_tx_obj(tx)
                        f, t, amt, txid, ts, behavior = n.get("from"), n.get("to"), n.get("amount"), n.get("txid"), n.get("timestamp"), n.get("behavior")
                        if f and t and amt > 0:
                            self.add_edge(f, t, amount=amt, txid=txid, timestamp=ts, token="TRX", behavior=behavior)
                            queue.append((t, hop + 1))

                # USDT Flows
                usdt_page = self.raw[addr].get("tv_usdt_txlist", {})
                tv_usdt_list = None
                if isinstance(usdt_page, dict) and "json" in usdt_page and isinstance(usdt_page["json"], dict):
                    d = usdt_page["json"].get("data")
                    if isinstance(d, dict) and "data" in d: tv_usdt_list = d["data"]
                    elif isinstance(d, list): tv_usdt_list = d
                if isinstance(tv_usdt_list, list):
                    for tx in tv_usdt_list:
                        f = tx.get("from") or tx.get("sender") or tx.get("owner")
                        t = tx.get("to") or tx.get("receiver")
                        q = tx.get("volume") or tx.get("quantity") or tx.get("value")
                        txid = tx.get("transactionid") or tx.get("txid")
                        ts = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(int(tx.get("time", 0))))
                        try: qf = float(q)
                        except: qf = 0.0
                        if f and t and qf > 0:
                            self.add_edge(f, t, amount=qf, txid=txid, timestamp=ts, token="USDT", behavior="Transfer (ERC20/TRC20)")
                            queue.append((t, hop + 1))

            elif chain == "ETHEREUM":
                # 1. Native ETH Transfers
                url_eth = f"https://api.etherscan.io/api?module=account&action=txlist&address={addr}&startblock=0&endblock=99999999&sort=desc"
                eth_resp = safe_get(url_eth)
                time.sleep(DELAY)
                txs = eth_resp.get("json", {}).get("result", [])
                if isinstance(txs, list):
                    for tx in txs:
                        if isinstance(tx, dict) and tx.get("isError") == "0":
                            f, t, amt_raw, txid, ts_raw = tx.get("from"), tx.get("to"), tx.get("value"), tx.get("hash"), tx.get("timeStamp")
                            try: amt = float(amt_raw) / 1e18
                            except: amt = 0.0
                            behavior = resolve_signature(tx.get("input", "0x"))
                            ts = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(int(ts_raw))) if ts_raw else ""
                            if f and t and amt > 0:
                                self.add_edge(f, t, amount=amt, txid=txid, timestamp=ts, token="ETH", behavior=behavior)
                                queue.append((t, hop + 1))
                                
                # 2. ERC-20 Token Transfers (USDC, USDT, etc.)
                url_erc20 = f"https://api.etherscan.io/api?module=account&action=tokentx&address={addr}&startblock=0&endblock=99999999&sort=desc"
                erc20_resp = safe_get(url_erc20)
                time.sleep(DELAY)
                token_txs = erc20_resp.get("json", {}).get("result", [])
                if isinstance(token_txs, list):
                    for tx in token_txs:
                        if isinstance(tx, dict):
                            f, t, amt_raw, txid, ts_raw = tx.get("from"), tx.get("to"), tx.get("value"), tx.get("hash"), tx.get("timeStamp")
                            token_symbol = tx.get("tokenSymbol", "ERC20")
                            token_decimals = int(tx.get("tokenDecimal", 18))
                            try: amt = float(amt_raw) / (10 ** token_decimals)
                            except: amt = 0.0
                            ts = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(int(ts_raw))) if ts_raw else ""
                            if f and t and amt > 0:
                                self.add_edge(f, t, amount=amt, txid=txid, timestamp=ts, token=token_symbol, behavior=f"Token Transfer ({token_symbol})")
                                queue.append((t, hop + 1))

            elif chain == "BITCOIN":
                url = f"https://mempool.space/api/address/{addr}/txs"
                btc_resp = safe_get(url)
                time.sleep(DELAY)
                txs = btc_resp.get("json", [])
                if isinstance(txs, list):
                    for tx in txs:
                        if not isinstance(tx, dict): continue
                        txid = tx.get("txid")
                        ts_raw = tx.get("status", {}).get("block_time")
                        ts = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(int(ts_raw))) if ts_raw else "Unconfirmed"
                        
                        is_sender = any(vin.get("prevout", {}).get("scriptpubkey_address") == addr for vin in tx.get("vin", []))
                        if is_sender:
                            for vout in tx.get("vout", []):
                                t = vout.get("scriptpubkey_address")
                                if t and t != addr:
                                    amt = float(vout.get("value", 0)) / 1e8
                                    if amt > 0:
                                        self.add_edge(addr, t, amount=amt, txid=txid, timestamp=ts, token="BTC", behavior="UTXO Transfer")
                                        queue.append((t, hop + 1))

    def analyze_nodes(self, start_addresses: List[str]) -> pd.DataFrame:
        rows = []
        features = []
        node_order = []

        for n in self.G.nodes:
            in_edges = list(self.G.in_edges(n, data=True))
            out_edges = list(self.G.out_edges(n, data=True))
            
            inbound_count = sum(d.get("count", 0) for _, _, d in in_edges)
            outbound_count = sum(d.get("count", 0) for _, _, d in out_edges)
            distinct_in = len(set([u for u, _, _ in in_edges]))
            total_in_amt = sum(d.get("weight", 0) for _, _, d in in_edges)
            total_out_amt = sum(d.get("weight", 0) for _, _, d in out_edges)
            
            label = "Unknown Entity"
            group = 0 
            confidence_level = "Analytical Assessment"
            confidence_score = 0.0
            
            tv_search = self.raw.get(n, {}).get("tv_search")
            tronscan_acct = self.raw.get(n, {}).get("tronscan_account")

            kw_cex = has_entity_keyword(tv_search, EXCHANGE_KEYWORDS) or has_entity_keyword(tronscan_acct, EXCHANGE_KEYWORDS)
            kw_mix = has_entity_keyword(tv_search, MIXER_KEYWORDS) or has_entity_keyword(tronscan_acct, MIXER_KEYWORDS)

            if kw_cex:
                if inbound_count > 100 or total_out_amt > 500000:
                    label = f"{kw_cex.upper()} Hot Wallet (Sweep Destination)"
                    group = 7
                else:
                    label = f"{kw_cex.upper()} User Deposit Address"
                    group = 1 
                confidence_level = "Confirmed On-Chain Fact"
                confidence_score = 0.99
            elif kw_mix:
                label = f"Mixer Protocol ({kw_mix.upper()})"
                group = 5 
                confidence_level = "Confirmed On-Chain Fact"
                confidence_score = 0.95
            elif distinct_in >= 2 and total_out_amt > 0: # Adjusted to actively flag Recombination points
                label = "Recombination / Consolidation Point"
                group = 2
                confidence_level = "High-Confidence Analytical Assessment"
                confidence_score = 0.88
            elif outbound_count == 0 and inbound_count > 0:
                label = "Terminal Holding Wallet (Funds Parked)"
                group = 3
                confidence_level = "High-Confidence Analytical Assessment"
                confidence_score = 0.85
            elif inbound_count > 0 and (outbound_count / max(1, inbound_count)) >= 1.0:
                label = "Relay / Layering Mule"
                group = 4
                confidence_level = "High-Confidence Analytical Assessment"
                confidence_score = 0.75

            if n in start_addresses:
                label = "Subject Wallet (Origin Seed)"
                group = 6
                confidence_level = "Confirmed On-Chain Fact"
                confidence_score = 1.0

            node_order.append(n)
            features.append([total_in_amt, total_out_amt, inbound_count, outbound_count])

            inc_txs = []
            for u, v, d in in_edges:
                if 'tx_history' in d:
                    for h in d['tx_history']:
                        inc_txs.append(f"{h['txid']} | {h['timestamp']} | {h['amount']} {h['token']}")
            inc_txs = list(set(inc_txs))[:10] 

            rows.append({
                "id": n,
                "label": label,
                "group": group,
                "confidence_level": confidence_level,
                "confidence_score": confidence_score,
                "inbound_count": inbound_count,
                "outbound_count": outbound_count,
                "total_in": round(total_in_amt, 4),
                "total_out": round(total_out_amt, 4),
                "sample_txs": inc_txs,
                "cluster_id": "Unclustered"
            })
            
        df = pd.DataFrame(rows)

        if len(features) > 2:
            try:
                scaler = StandardScaler()
                scaled_features = scaler.fit_transform(features)
                db = DBSCAN(eps=0.5, min_samples=2).fit(scaled_features)
                for idx, cluster_label in enumerate(db.labels_):
                    if cluster_label != -1:
                        df.at[idx, 'cluster_id'] = f"Threat Actor Syndicate Alpha-{cluster_label}"
            except Exception as e:
                logger.error(f"Clustering failed: {e}")

        for _, row in df.iterrows():
            n = row['id']
            self.G.nodes[n]['label'] = row['label']
            self.G.nodes[n]['group'] = row['group']
            self.G.nodes[n]['cluster_id'] = row['cluster_id']

        return df
