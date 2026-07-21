"""
NEMESIS v3.1 Enterprise
Cloudflare Edge Trace Engine
A horizontally scalable, stateless infinite-hop blockchain tracing module.
"""

import json
import logging
from typing import Dict, Any, List
import urllib.request
import urllib.error

# For Cloudflare Workers JS Fetch API
try:
    from js import fetch, Headers, Request
    import pyodide.ffi
except ImportError:
    pass

logger = logging.getLogger("NEMESIS.Workers.EdgeTraceEngine")

class EdgeTraceEngine:
    def __init__(self, env):
        self.env = env
        
    async def resolve_entity(self, address: str) -> Dict[str, Any]:
        """
        Uses Cloudflare KV Namespace (NEMESIS_KV) for instant entity attribution.
        If not found in cache, falls back to external Threat Intel API (Mocked).
        """
        try:
            cached_entity = await self.env.NEMESIS_KV.get(f"entity:{address}")
            if cached_entity:
                return json.loads(cached_entity)
        except Exception:
            pass
            
        # Hardcoded Enterprise Mock Attributions for demonstration
        address_lower = address.lower()
        entity_name = "Unknown Wallet"
        category = "Private"
        risk_score = 0
        
        if "exchange" in address_lower or "0x28c" in address_lower:
            entity_name = "Binance Hot Wallet"
            category = "Exchange"
            risk_score = 10
        elif "tornado" in address_lower or "0xd90e" in address_lower:
            entity_name = "Tornado Cash Router"
            category = "Mixer"
            risk_score = 100
        elif "lazarus" in address_lower or "suspect" in address_lower:
            entity_name = "Lazarus Group (Sanctioned)"
            category = "Sanctioned Entity"
            risk_score = 100
            
        entity_data = {
            "entity": entity_name,
            "category": category,
            "risk_score": risk_score
        }
        
        # Cache asynchronously in KV
        try:
            await self.env.NEMESIS_KV.put(f"entity:{address}", json.dumps(entity_data))
        except:
            pass
            
        return entity_data

    async def fetch_transactions(self, address: str, chain: str) -> List[Dict[str, Any]]:
        """
        Executes a secure async HTTP fetch to the Bitquery GraphQL API for live on-chain transfers.
        """
        api_key = getattr(self.env, "BITQUERY_APIV2_TOKEN", getattr(self.env, "BITQUERY_API_TOKEN", getattr(self.env, "BITQUERY_API_KEY", "")))
        if not api_key or api_key == "ADD_YOUR_API_KEY_HERE_OR_USE_WRANGLER_SECRET":
            logger.warning("[TRACE ENGINE] BITQUERY API token not configured. Falling back to empty results.")
            return []

        # Map chain string to Bitquery network format
        chain_map = {
            "ethereum": "eth",
            "polygon": "matic",
            "bsc": "bsc",
            "arbitrum": "arbitrum"
        }
        network = chain_map.get(chain.lower(), "eth")

        query = """
        query GetTransfers($address: String!, $network: evm_network) {
          EVM(network: $network) {
            Transfers(
              where: {
                any: [
                  {Transfer: {Receiver: {is: $address}}},
                  {Transfer: {Sender: {is: $address}}}
                ]
              }
              limit: {count: 10}
              orderBy: {descending: Block_Time}
            ) {
              Transfer {
                Amount
                Currency {
                  Symbol
                  SmartContract
                }
                Receiver
                Sender
              }
              Transaction {
                Hash
              }
              Block {
                Time
              }
            }
          }
        }
        """

        variables = {
            "address": address,
            "network": network
        }

        payload = json.dumps({"query": query, "variables": variables})
        url = "https://graphql.bitquery.io/"
        
        try:
            # Check if running in Cloudflare Pyodide context
            if 'fetch' in globals():
                headers = Headers.new({"Content-Type": "application/json", "X-API-KEY": api_key})
                req = Request.new(url, method="POST", headers=headers, body=payload)
                response = await fetch(req)
                json_data = await response.json()
                if hasattr(json_data, "to_py"):
                    data = json_data.to_py()
                else:
                    import js
                    data = json.loads(js.JSON.stringify(json_data))
            else:
                # Local fallback using urllib
                req = urllib.request.Request(url, data=payload.encode('utf-8'), method="POST")
                req.add_header("Content-Type", "application/json")
                req.add_header("X-API-KEY", api_key)
                with urllib.request.urlopen(req, timeout=10) as response:
                    data = json.loads(response.read().decode('utf-8'))
                    
            return self.normalize_bitquery_response(data, address, chain)
        except Exception as e:
            logger.error(f"[TRACE ENGINE] Bitquery API Error: {e}")
            return []

    def normalize_bitquery_response(self, data: Dict[str, Any], address: str, chain: str) -> List[Dict[str, Any]]:
        """
        Standardizes Bitquery V2 JSON structure into internal LEDGER events.
        """
        txs = []
        try:
            transfers = data.get("data", {}).get("EVM", {}).get("Transfers", [])
            for t in transfers:
                transfer_data = t.get("Transfer", {})
                tx_data = t.get("Transaction", {})
                block_data = t.get("Block", {})
                
                amount = float(transfer_data.get("Amount", 0))
                token_symbol = transfer_data.get("Currency", {}).get("Symbol", "Unknown")
                sender = transfer_data.get("Sender", "")
                receiver = transfer_data.get("Receiver", "")
                
                tx = {
                    "tx_hash": tx_data.get("Hash", ""),
                    "timestamp": block_data.get("Time", ""),
                    "amount": amount,
                    "usd": amount, # Need pricing API for accurate USD, assuming 1:1 for now
                    "token": token_symbol,
                    "chain": chain,
                    "state_transition": "TRANSFER",
                    "edge_type": "TRANSFER",
                    "from": sender,
                    "to": receiver
                }
                txs.append(tx)
        except Exception as e:
            logger.error(f"[TRACE ENGINE] Normalization Error: {e}")
            
        return txs

    async def process_hop(self, session_id: str, address: str, chain: str, current_depth: int, max_depth: int):
        """
        The core stateless processing loop executed by the Queue Consumer.
        """
        if current_depth > max_depth:
            return
            
        logger.info(f"[TRACE ENGINE] Processing Hop {current_depth}/{max_depth} for {address}")
        
        # 1. Fetch live transactions
        transactions = await self.fetch_transactions(address, chain)
        
        # 2. Extract unique peers
        peers = set()
        for tx in transactions:
            peers.add(tx["from"])
            peers.add(tx["to"])
            
        # 3. Resolve Entity Attribution via KV
        resolved_entities = {}
        for peer in peers:
            resolved_entities[peer] = await self.resolve_entity(peer)
            
        # 4. Construct Graph LEDGER events and persist to D1 Serverless SQL
        events = []
        next_hops = set()
        
        for tx in transactions:
            sender_info = resolved_entities[tx["from"]]
            receiver_info = resolved_entities[tx["to"]]
            
            # Enrich transaction
            tx["sender_entity"] = sender_info["entity"]
            tx["receiver_entity"] = receiver_info["entity"]
            tx["type"] = "LEDGER"
            tx["trace_id"] = session_id
            
            events.append(tx)
            
            # Determine if we should recursively trace this peer
            target_peer = tx["to"] if tx["from"] == address else tx["from"]
            if current_depth < max_depth:
                next_hops.add(target_peer)
                
            # TODO: Add D1 Persistence logic here
            # await self.env.DB.execute("INSERT INTO state_edges ...")
            
        # 5. Broadcast live events to the Durable Object for the Analyst UI
        if events:
            try:
                do_id = self.env.SESSION_ENGINE.idFromName(session_id)
                stub = self.env.SESSION_ENGINE.get(do_id)
                for ev in events:
                    await stub.fetch("http://internal/push", method="POST", body=json.dumps({
                        "action": "broadcast",
                        "session_id": session_id,
                        "payload": ev
                    }))
            except Exception as e:
                logger.error(f"Failed to push to DO: {e}")
                
        # 6. QUEUE FAN-OUT: Recursively push next hops back into the Cloudflare Queue!
        for hop_address in next_hops:
            try:
                await self.env.JOB_QUEUE.send({
                    "type": "blockchain_trace",
                    "session_id": session_id,
                    "address": hop_address,
                    "chain": chain,
                    "current_depth": current_depth + 1,
                    "max_depth": max_depth
                })
            except Exception as e:
                logger.error(f"Failed to push hop to queue: {e}")
