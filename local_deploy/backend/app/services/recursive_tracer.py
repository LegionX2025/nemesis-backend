import logging
import asyncio
from datetime import datetime
from services.database import db_instance
from services.trace_engine import TraceEngine, detect_chain, EVM_DOMAINS
import aiohttp
import pymongo
from services.api_rotator import api_rotator
from services.mixer_heuristics import MixerCorrelationEngine
from services.bridge_resolver import BridgeResolver
from services.swarm_fetcher import swarm_instance

logger = logging.getLogger("RecursiveTracer")

class RecursiveTracer:
    def __init__(self, session=None):
        self.session = session
        self.db = db_instance
        self.entities_col = self.db.get_mongo_collection("entities")
        self.edges_col = self.db.get_mongo_collection("state_edges")
        self.bridge_col = self.db.get_mongo_collection("bridge_links")
        self.identity_col = self.db.get_mongo_collection("identity_artifacts")
        self.transactions_col = self.db.get_mongo_collection("transactions")
        self.events_col = self.db.get_mongo_collection("events")
        
        # Existing trace engine for fetching raw txs
        self.api_engine = TraceEngine("recursive-trace")
        self.mixer_engine = MixerCorrelationEngine(self.db)
        self.bridge_resolver = BridgeResolver(self.db)
    
    async def ingest_wallet_transactions(self, seed: str, chain: str) -> int:
        """Fetches transactions for a wallet from the fallback tier and ingests into Graph DB"""
        if not self.session:
            async with aiohttp.ClientSession() as session:
                return await self._do_ingest(session, seed, chain)
        return await self._do_ingest(self.session, seed, chain)
        
    async def _do_ingest(self, session, seed: str, chain: str) -> int:
        edges_to_insert = []
        
        # If EVM_AUTO, fan out to all supported EVM networks to find cross-chain activity
        chains_to_fetch = list(EVM_DOMAINS.keys()) if chain == "EVM_AUTO" else [chain]
        
        # Swarm Fetch handles the parallel tier-based fallback logic natively per-chain
        swarm_data = await swarm_instance.swarm_fetch(session, seed, chains_to_fetch)
        
        for resolved_chain, tx_list in swarm_data.items():
            if not tx_list:
                continue
                
            for tx in tx_list:
                # Etherscan logic vs others
                tx_type = "evm" if resolved_chain in EVM_DOMAINS else resolved_chain.lower()
                parsed_edges = await self.parse_state_transition(session, tx, tx_type, resolved_chain, seed)
                if parsed_edges:
                    edges_to_insert.extend(parsed_edges)
        
        if edges_to_insert:
            for e in edges_to_insert:
                resolved_chain = e.get("chain", "UNKNOWN")
                self.entities_col.update_one(
                    {"_id": e["from"]}, 
                    {"$set": {"address": e["from"], "chain": resolved_chain, "type": "wallet"}, "$setOnInsert": {"first_seen": datetime.utcnow()}},
                    upsert=True
                )
                self.entities_col.update_one(
                    {"_id": e["to"]}, 
                    {"$set": {"address": e["to"], "chain": resolved_chain, "type": "wallet"}, "$setOnInsert": {"first_seen": datetime.utcnow()}},
                    upsert=True
                )
            if edges_to_insert:
                try:
                    requests = [pymongo.UpdateOne({"_id": edge["_id"]}, {"$set": edge}, upsert=True) for edge in edges_to_insert]
                    self.edges_col.bulk_write(requests, ordered=False)
                except pymongo.errors.BulkWriteError:
                    pass
                except Exception as e:
                    logger.error(f"MongoDB Insert Error: {e}")
        
        return len(edges_to_insert)

    async def parse_state_transition(self, session, tx: dict, tx_type: str, chain: str, seed: str):
        """Transforms raw API txs into Normalized StateEdges (MINT, BURN, SWAP, TRANSFER)"""
        edges = []
        try:
            # 1. Universal Transactions Layer Insertion (All Chains)
            tx_doc = {
                "_id": tx.get("hash", tx.get("txid", tx.get("id", tx.get("transaction_id", "")))),
                "chain": chain.lower(),
                "block_time": datetime.utcnow(),
                "raw": tx
            }
            if tx_doc["_id"]:
                try: self.transactions_col.update_one({"_id": tx_doc["_id"]}, {"$set": tx_doc}, upsert=True)
                except: pass

            if tx_type == "evm":
                method = tx.get("methodId", "")
                val = float(tx.get("value", 0)) / 1e18 if str(tx.get("value", 0)).isdigit() else 0
                
                edge_type = "TRANSFER"
                if method.startswith("0xa9059cbb") or method.startswith("0x23b872dd"): edge_type = "TRANSFER" 
                elif method.startswith("0x38ed1739") or method.startswith("0x5c11d795"): edge_type = "SWAP"
                elif method.startswith("0x3d12a85a") or method.startswith("0xc22a7f05"): edge_type = "BRIDGE_HOP"
                elif method.startswith("0x40c10f19"): edge_type = "MINT"
                elif method.startswith("0x42966c68"): edge_type = "BURN"
                elif method.startswith("0xb6b55f25"): edge_type = "LOCK" 
                elif method.startswith("0x21a0adb6"): edge_type = "RELEASE"
                
                out_asset = "ETH"
                out_amount = val
                
                # Fetch DeFi logs if swap, bridge, or ERC20 Transfer
                is_erc20_transfer = method.startswith("0xa9059cbb") or method.startswith("0x23b872dd")
                if edge_type in ["SWAP", "MINT", "BRIDGE_HOP"] or is_erc20_transfer:
                    logs = await api_rotator.fetch_transaction_receipt(session, tx.get("hash"), chain)
                    if logs:
                        # Extract ERC20 Transfer event: Topic0 = 0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef
                        for log in reversed(logs):  # Read backwards to get final output token
                            topics = log.get("topics", [])
                            if topics and topics[0] == "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef":
                                out_asset = str(log.get("address", "ERC20_TOKEN")).lower() # Token contract address
                                try:
                                    if len(topics) >= 3:
                                        real_to = "0x" + topics[2][-40:]
                                        tx["to"] = real_to.lower()
                                    raw_data = log.get("data", "0x0")
                                    raw_val = int(raw_data, 16)
                                    stablecoins = ["0x8ac76a51cc950d9822d68b83fe1ad97b32cd580d", "0x55d398326f99059ff775485246999027b3197955", "0xdac17f958d2ee523a2206206994597c13d831ec7", "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"]
                                    if out_asset in stablecoins:
                                        out_amount = raw_val / 1e6
                                    else:
                                        out_amount = raw_val / 1e6 if raw_val > 10**12 else raw_val / 1e18
                                except: pass
                                break
                
                timestamp_dt = datetime.fromtimestamp(int(str(tx.get("timeStamp", 0)), 0)) if tx.get("timeStamp") else datetime.utcnow()
                
                # 1. Transactions Layer Insertion
                tx_doc = {
                    "_id": tx.get("hash"),
                    "chain": chain.lower(),
                    "block_time": timestamp_dt,
                    "from": str(tx.get("from", "")).lower(),
                    "to": str(tx.get("to", "")).lower(),
                    "value": str(val),
                    "raw": tx,
                    "parsed": {
                        "method": edge_type,
                        "asset": out_asset,
                        "amount": str(out_amount)
                    }
                }
                try: self.transactions_col.update_one({"_id": tx_doc["_id"]}, {"$set": tx_doc}, upsert=True)
                except: pass
                
                # 2. Events Layer Insertion (EVM Logs)
                if out_asset != "ETH":
                    event_doc = {
                        "_id": f"{tx.get('hash')}_ERC20_{out_asset}",
                        "tx_hash": tx.get("hash"),
                        "chain": chain.lower(),
                        "event_type": "ERC20_Transfer",
                        "signature": "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef",
                        "source_entity": str(tx.get("from", "")).lower(),
                        "target_entity": str(tx.get("to", "")).lower(),
                        "asset": out_asset,
                        "amount": str(out_amount),
                        "metadata": {}
                    }
                    try: self.events_col.update_one({"_id": event_doc["_id"]}, {"$set": event_doc}, upsert=True)
                    except: pass
                
                edges.append({
                    "_id": tx.get("hash") + "_0",
                    "from": str(tx.get("from", "")).lower(),
                    "to": str(tx.get("to", "")).lower(),
                    "edge_type": edge_type,
                    "tx_hash": tx.get("hash"),
                    "chain": chain,
                    "asset": out_asset,
                    "amount": str(out_amount),
                    "timestamp": timestamp_dt,
                    "confidence": 1.0
                })
                
            elif tx_type == "btc" or tx_type == "kaspa":
                addr_lower = seed.lower()
                is_sender = any(i.get("prevout", {}).get("scriptpubkey_address", "").lower() == addr_lower for i in tx.get("vin", []))
                
                if is_sender:
                    vouts = tx.get("vout", [])
                    # Kaspa/Bitcoin Peel Chain / Fan-out Entropy Detection
                    edge_type = "TRANSFER"
                    if len(vouts) > 10: 
                        # High fan-out
                        edge_type = "TRANSFER_FANOUT"
                        try: self.events_col.update_one({"_id": tx.get("txid") + "_PEEL"}, {"$set": {"tx_hash": tx.get("txid"), "event_type": "PEEL_CHAIN", "chain": tx_type}}, upsert=True)
                        except: pass
                        
                    for idx, o in enumerate(vouts):
                        out_addr = o.get("scriptpubkey_address", "")
                        if out_addr.lower() != addr_lower:
                            val = float(o.get("value", 0)) / 1e8
                            edges.append({
                                "_id": f"{tx.get('txid')}_{idx}",
                                "from": addr_lower,
                                "to": out_addr,
                                "edge_type": edge_type,
                                "tx_hash": tx.get("txid"),
                                "chain": tx_type.upper(),
                                "asset": tx_type.upper(),
                                "amount": str(val),
                                "timestamp": datetime.fromtimestamp(tx.get("status", {}).get("block_time", 0)) if tx.get("status", {}).get("block_time") else datetime.utcnow(),
                                "confidence": 1.0
                            })
            elif tx_type == "solana":
                pre_bals = tx.get("meta", {}).get("preBalances", [])
                post_bals = tx.get("meta", {}).get("postBalances", [])
                keys = [k.get("pubkey") if isinstance(k, dict) else k for k in tx.get("transaction", {}).get("message", {}).get("accountKeys", [])]
                
                edge_type = "TRANSFER"
                logs = tx.get("meta", {}).get("logMessages", [])
                for log in logs:
                    if "Instruction: MintTo" in log: 
                        edge_type = "MINT"
                        try: self.events_col.update_one({"_id": tx.get("transaction", {}).get("signatures", [""])[0] + "_MINT"}, {"$set": {"tx_hash": tx.get("transaction", {}).get("signatures", [""])[0], "event_type": "MintTo", "chain": "solana"}}, upsert=True)
                        except: pass
                    elif "Program metaqbxxUerdq28cj1RbAWkYQm3ybzjb6a8bt518x1s" in log:
                        edge_type = "NFT_TRADE"
                        try: self.events_col.update_one({"_id": tx.get("transaction", {}).get("signatures", [""])[0] + "_NFT"}, {"$set": {"tx_hash": tx.get("transaction", {}).get("signatures", [""])[0], "event_type": "Metaplex_NFT", "chain": "solana"}}, upsert=True)
                        except: pass
                
                if seed in keys:
                    idx = keys.index(seed)
                    if idx < len(pre_bals) and idx < len(post_bals):
                        diff = (post_bals[idx] - pre_bals[idx]) / 1e9
                        if diff < 0:
                            val = abs(diff)
                            receiver = keys[1] if len(keys) > 1 else keys[0]
                            edges.append({
                                "_id": tx.get("transaction", {}).get("signatures", [""])[0],
                                "from": seed,
                                "to": receiver,
                                "edge_type": edge_type,
                                "tx_hash": tx.get("transaction", {}).get("signatures", [""])[0],
                                "chain": "SOLANA",
                                "asset": "SOL",
                                "amount": str(val),
                                "timestamp": datetime.fromtimestamp(tx.get("blockTime", 0)) if tx.get("blockTime") else datetime.utcnow(),
                                "confidence": 1.0
                            })

            elif tx_type == "ripple":
                t_tx = tx.get("tx", tx)
                if t_tx.get("TransactionType") == "Payment" and t_tx.get("Account") == seed:
                    amt = t_tx.get("Amount", 0)
                    val = float(amt) / 1e6 if isinstance(amt, str) else float(amt.get("value", 0))
                    
                    edge = {
                        "_id": t_tx.get("hash"),
                        "from": seed,
                        "to": t_tx.get("Destination"),
                        "edge_type": "TRANSFER",
                        "tx_hash": t_tx.get("hash"),
                        "chain": "RIPPLE",
                        "asset": "XRP",
                        "amount": str(val),
                        "timestamp": datetime.utcnow(),
                        "confidence": 1.0
                    }
                    
                    dest_tag = t_tx.get("DestinationTag")
                    if dest_tag:
                        self.identity_col.update_one(
                            {"_id": f"xrp_tag_{dest_tag}"},
                            {"$set": {"type": "tag", "value": str(dest_tag), "chain": "RIPPLE"}, "$addToSet": {"linked_entities": t_tx.get("Destination")}},
                            upsert=True
                        )
                    edges.append(edge)
                    
            elif tx_type == "tron":
                if tx.get("ownerAddress", tx.get("from")) == seed:
                    amt = tx.get("amount")
                    if amt:
                        val = float(amt) / 1e6
                        edges.append({
                            "_id": tx.get("hash"),
                            "from": seed,
                            "to": tx.get("toAddress", tx.get("to")),
                            "edge_type": "TRANSFER",
                            "tx_hash": tx.get("hash"),
                            "chain": "TRON",
                            "asset": "TRX",
                            "amount": str(val),
                            "timestamp": datetime.fromtimestamp(int(str(tx.get("timestamp", 0)), 0)/1000) if tx.get("timestamp") else datetime.utcnow(),
                            "confidence": 1.0
                        })
            
            elif tx_type == "stellar":
                if tx.get("from") == seed:
                    val = float(tx.get("amount", 0))
                    edges.append({
                        "_id": tx.get("id"),
                        "from": seed,
                        "to": tx.get("to"),
                        "edge_type": "TRANSFER",
                        "tx_hash": tx.get("transaction_hash"),
                        "chain": "STELLAR",
                        "asset": "XLM",
                        "amount": str(val),
                        "timestamp": datetime.utcnow(),
                        "confidence": 1.0
                    })
                    
            elif tx_type == "hedera":
                # Hedera HTS and Topic logs
                val = float(tx.get("amount", 0))
                edge_type = "TRANSFER"
                if tx.get("name") == "CRYPTOMINT": 
                    edge_type = "MINT"
                    try: self.events_col.update_one({"_id": tx.get("transaction_id") + "_HTS"}, {"$set": {"tx_hash": tx.get("transaction_id"), "event_type": "HTS_Mint", "chain": "hedera"}}, upsert=True)
                    except: pass
                if tx.get("memo") or tx.get("topic"):
                    topic_id = tx.get("topic") or tx.get("memo")
                    try: self.identity_col.update_one({"_id": f"hedera_topic_{topic_id}"}, {"$set": {"type": "topic", "value": str(topic_id), "chain": "HEDERA"}, "$addToSet": {"linked_entities": tx.get("to")}}, upsert=True)
                    except: pass
                edges.append({
                    "_id": tx.get("transaction_id", ""),
                    "from": seed,
                    "to": tx.get("to", ""),
                    "edge_type": edge_type,
                    "tx_hash": tx.get("transaction_id", ""),
                    "chain": "HEDERA",
                    "asset": "HBAR",
                    "amount": str(val),
                    "timestamp": datetime.utcnow(),
                    "confidence": 1.0
                })
        except Exception as e:
            logger.error(f"Error parsing state transition: {e}")
            
        return edges

    def find_bridge_symmetry(self, edge: dict):
        """Legacy static DB lookup, now combined with dynamic API/Symmetry fallback."""
        return self.bridge_col.find_one({
            "$or": [
                {"mint_tx": edge["tx_hash"]},
                {"lock_tx": edge["tx_hash"]}
            ]
        })

    def find_cex_withdrawals(self, entity_id: str, deposit_amount: float, deposit_time: datetime):
        """FIFO/LIFO internal ledger hop simulation based on volume correlation."""
        # Find withdrawals occurring AFTER the deposit time
        query = {
            "from": entity_id, 
            "edge_type": "TRANSFER",
            "timestamp": {"$gte": deposit_time}
        }
        # Sort by timestamp (FIFO)
        cursor = self.edges_col.find(query).sort("timestamp", 1).limit(20)
        
        correlated_withdrawals = []
        accumulated_volume = 0.0
        
        for doc in cursor:
            out_val = float(doc.get("amount", 0))
            if accumulated_volume < deposit_amount:
                correlated_withdrawals.append(doc["to"])
                accumulated_volume += out_val
            else:
                break
                
        return correlated_withdrawals

    async def start_omni_trace(self, suspect_wallet: str, max_depth: int = 3):
        """Orchestrator to ensure all EVM chains are ingested before tracing starts."""
        suspect_wallet = suspect_wallet.lower()
        chain = detect_chain(suspect_wallet)
        if chain == "EVM_AUTO":
            logger.info(f"Detected EVM wallet. Commencing Omni-Chain Ingestion across {len(EVM_DOMAINS)} networks...")
            # Fan out ingest requests across all EVM networks
            tasks = [self.ingest_wallet_transactions(suspect_wallet, evm_chain) for evm_chain in EVM_DOMAINS.keys()]
            await asyncio.gather(*tasks, return_exceptions=True)
            logger.info("Omni-Chain Ingestion Complete.")
        else:
            if chain != "INVALID":
                logger.info(f"Commencing Single-Chain Ingestion for {chain}...")
                await self.ingest_wallet_transactions(suspect_wallet, chain)

        async for edge in self.trace_from_entity(suspect_wallet, depth=0, max_depth=max_depth):
            yield edge

    async def start_omni_trace_bfs(self, suspect_wallet: str, max_depth: int = 1000000):
        """Breadth-First Search Orchestrator for tracing."""
        suspect_wallet = suspect_wallet.lower()
        chain = detect_chain(suspect_wallet)
        if chain == "EVM_AUTO":
            logger.info(f"[BFS] Detected EVM wallet. Commencing Omni-Chain Ingestion...")
            tasks = [self.ingest_wallet_transactions(suspect_wallet, evm_chain) for evm_chain in EVM_DOMAINS.keys()]
            await asyncio.gather(*tasks, return_exceptions=True)
        elif chain != "INVALID":
            logger.info(f"[BFS] Commencing Single-Chain Ingestion for {chain}...")
            await self.ingest_wallet_transactions(suspect_wallet, chain)

        queue = [(suspect_wallet, 0)]
        visited = {suspect_wallet}
        
        while queue:
            current_entity, depth = queue.pop(0)
            
            if depth >= max_depth:
                continue
                
            logger.info(f"BFS Tracing entity {current_entity} at depth {depth}")
            
            edges = list(self.edges_col.find({"from": current_entity}))
            
            if not edges:
                ent = self.entities_col.find_one({"_id": current_entity})
                c = ent["chain"] if ent else detect_chain(current_entity)
                if c != "INVALID":
                    await self.ingest_wallet_transactions(current_entity, c)
                    edges = list(self.edges_col.find({"from": current_entity}))

            edges.sort(key=lambda x: float(x.get("amount", 0)), reverse=True)
            
            for edge in edges:
                yield edge
                
                next_hops = [edge["to"]]
                
                # 1. Handle Bridges
                if edge["edge_type"] in ["MINT", "RELEASE", "BRIDGE_HOP", "LOCK", "BURN"]:
                    linked = self.find_bridge_symmetry(edge)
                    if not linked:
                        linked = await self.bridge_resolver.resolve_cross_chain_hop(
                            edge["tx_hash"], edge["chain"], float(edge["amount"]), edge["timestamp"]
                        )
                    if linked:
                        next_hops.append(linked["bridge_entity"])
                        
                # 2. Handle Mixers
                ent = self.entities_col.find_one({"_id": edge["to"]})
                labels = ent.get("labels", []) if ent else []
                if "Mixer" in labels or "CoinJoin" in labels or edge["edge_type"] == "MIXER":
                    mixer_edges = await self.mixer_engine.find_mixer_correlations(
                        edge["to"], float(edge["amount"]), edge["timestamp"], edge["chain"]
                    )
                    for medge in mixer_edges:
                        yield medge
                        next_hops.append(medge["to"])
                        
                # 3. Handle Identity Linking
                artifacts = self.identity_col.find({"linked_entities": edge["to"]})
                for art in artifacts:
                    for e in art.get("linked_entities", []):
                        if e != edge["to"]:
                            next_hops.append(e)
                            
                # 4. Handle CEX Internal Ledgers
                if "cex" in labels or "Exchange" in labels:
                    withdrawals = self.find_cex_withdrawals(edge["to"], float(edge["amount"]), edge["timestamp"])
                    for w in withdrawals:
                        next_hops.append(w)
                        
                # Queue next hops for BFS
                for nxt in next_hops:
                    nxt = nxt.lower()
                    if nxt and nxt not in visited:
                        visited.add(nxt)
                        queue.append((nxt, depth + 1))

    async def trace_from_entity(self, entity_id: str, depth=0, max_depth=2, visited=None):
        """Recursive graph traversal for state transitions via async generator."""
        entity_id = entity_id.lower()
        if visited is None: visited = set()
        
        if depth > max_depth or entity_id in visited:
            return
            
        visited.add(entity_id)
        logger.info(f"Tracing entity {entity_id} at depth {depth}")
        
        edges = list(self.edges_col.find({"from": entity_id}))
        
        if not edges and depth < max_depth:
            ent = self.entities_col.find_one({"_id": entity_id})
            chain = ent["chain"] if ent else detect_chain(entity_id)
            if chain != "INVALID":
                await self.ingest_wallet_transactions(entity_id, chain)
                edges = list(self.edges_col.find({"from": entity_id}))

        edges.sort(key=lambda x: float(x.get("amount", 0)), reverse=True)
        
        for edge in edges:
            yield edge
            
            async for sub_edge in self.trace_from_entity(edge["to"], depth+1, max_depth, visited):
                yield sub_edge
            
            # 1. Handle Bridges
            if edge["edge_type"] in ["MINT", "RELEASE", "BRIDGE_HOP", "LOCK", "BURN"]:
                linked = self.find_bridge_symmetry(edge)
                if not linked:
                    # Dynamic Bridge Resolution
                    linked = await self.bridge_resolver.resolve_cross_chain_hop(
                        edge["tx_hash"], edge["chain"], float(edge["amount"]), edge["timestamp"]
                    )
                    
                if linked:
                    async for sub_edge in self.trace_from_entity(linked["bridge_entity"], depth+1, max_depth, visited):
                        yield sub_edge
                    
            # 2. Handle Mixers
            ent = self.entities_col.find_one({"_id": edge["to"]})
            labels = ent.get("labels", []) if ent else []
            if "Mixer" in labels or "CoinJoin" in labels or edge["edge_type"] == "MIXER":
                mixer_edges = await self.mixer_engine.find_mixer_correlations(
                    edge["to"], float(edge["amount"]), edge["timestamp"], edge["chain"]
                )
                for medge in mixer_edges:
                    yield medge
                    async for sub_edge in self.trace_from_entity(medge["to"], depth+1, max_depth, visited):
                        yield sub_edge
                    
            # 3. Handle Identity Linking
            artifacts = self.identity_col.find({"linked_entities": edge["to"]})
            for art in artifacts:
                for e in art.get("linked_entities", []):
                    if e != edge["to"]:
                        async for sub_edge in self.trace_from_entity(e, depth+1, max_depth, visited):
                            yield sub_edge
                        
            # 4. Handle CEX Internal Ledgers
            if "cex" in labels or "Exchange" in labels:
                withdrawals = self.find_cex_withdrawals(edge["to"], float(edge["amount"]), edge["timestamp"])
                for w in withdrawals:
                    async for sub_edge in self.trace_from_entity(w, depth+1, max_depth, visited):
                        yield sub_edge
