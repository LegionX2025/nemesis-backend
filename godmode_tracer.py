import os
import json
import time
import logging
import requests
from typing import List, Dict, Any, Optional
from pymongo import MongoClient
import networkx as nx

try:
    from rpc_adapters import OmniChainSync
except ImportError:
    OmniChainSync = None

logger = logging.getLogger(__name__)

MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://MKpBkrUw:Z63zGHQaiYG6rhrb@us-east-1.ufsuw.mongodb.net/blockchain")

class GodmodeDB:
    def __init__(self):
        self.client = None
        self.db = None
        try:
            self.client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=2000)
            self.db = self.client["nemesis"]
            # Collections
            self.entities = self.db["entities"]
            self.transactions = self.db["transactions"]
            self.events = self.db["events"]
            self.state_edges = self.db["state_edges"]
            self.bridge_links = self.db["bridge_links"]
            self.identity_artifacts = self.db["identity_artifacts"]
            logger.info("GodmodeDB: Connected to MongoDB cluster.")
        except Exception as e:
            logger.error(f"GodmodeDB Connection failed: {e}")

    def is_connected(self):
        return self.client is not None

godmode_db = GodmodeDB()

class GodmodeTracer:
    def __init__(self, max_depth: int = 10):
        self.max_depth = max_depth
        self.G = nx.DiGraph()
        self.evidence_ledger = []
        self.total_volume_usd = 0.0

    def trace_from_entity(self, entity_id: str, depth: int = 0, current_path: List[str] = None):
        """
        Recursive Cross-Chain Tracer Logic consuming state_edges.
        """
        if current_path is None:
            current_path = []
            
        if depth > self.max_depth or entity_id in current_path:
            return

        current_path.append(entity_id)

        if not godmode_db.is_connected():
            return
            
        # Optional: Sync live public API data into MongoDB for the current entity before tracing
        if OmniChainSync and depth == 0:
            OmniChainSync.sync_all(entity_id)

        # Fetch edges from MongoDB
        edges = list(godmode_db.state_edges.find({"from": entity_id}))

        for edge in edges:
            to_entity = edge.get("to")
            edge_type = edge.get("edge_type", "TRANSFER")
            tx_hash = edge.get("tx_hash", "Unknown")
            chain = edge.get("chain", "Unknown")
            asset = edge.get("asset", "Unknown")
            amount = edge.get("amount", 0.0)
            timestamp = edge.get("timestamp", "")
            
            try: amt_float = float(amount)
            except: amt_float = 0.0

            # Update Graph and Evidence Ledger
            self._add_to_graph(entity_id, to_entity, amt_float, tx_hash, timestamp, asset, edge_type, chain)

            # 1. Standard Traversal
            self.trace_from_entity(to_entity, depth + 1, current_path.copy())

            # 2. Bridge Symmetry Resolution (Mint -> Find corresponding Lock/Burn)
            if edge_type in ["MINT", "RELEASE", "BRIDGE_HOP"]:
                linked = self._find_bridge_symmetry(tx_hash)
                if linked and linked.get("from"):
                    self.trace_from_entity(linked["from"], depth + 1, current_path.copy())

            # 3. Pivot Identity based on Memos/Tags
            artifacts = list(godmode_db.identity_artifacts.find({"linked_entities": to_entity}))
            for art in artifacts:
                linked_entities = art.get("linked_entities", [])
                for e in linked_entities:
                    if e != to_entity:
                        self.trace_from_entity(e, depth + 1, current_path.copy())

            # 4. Exchange Entity Internal Hop Simulation
            entity_record = godmode_db.entities.find_one({"_id": to_entity})
            if entity_record and "cex" in entity_record.get("labels", []):
                withdrawals = self._find_cex_withdrawals(to_entity)
                for w in withdrawals:
                    self.trace_from_entity(w, depth + 1, current_path.copy())

    def _find_bridge_symmetry(self, tx_hash: str) -> Optional[Dict]:
        """Resolves cross-chain bridge hops by searching lock/mint pairs."""
        if not godmode_db.is_connected(): return None
        return godmode_db.bridge_links.find_one({
            "$or": [{"mint_tx": tx_hash}, {"lock_tx": tx_hash}]
        })

    def _find_cex_withdrawals(self, cex_entity_id: str) -> List[str]:
        """Simulates internal ledger routing to find matching withdrawals."""
        return []

    def _add_to_graph(self, src: str, dst: str, amount: float, txid: str, ts: str, token: str, behavior: str, chain: str):
        for node in (src, dst):
            if not self.G.has_node(node):
                self.G.add_node(node, label=node, group=0, cluster_id="Unclustered")
        
        edge_data = {"txid": txid, "timestamp": ts, "amount": amount, "token": token, "behavior": behavior, "chain": chain}
        self.evidence_ledger.append({"from": src, "to": dst, **edge_data})
        self.total_volume_usd += amount

        if self.G.has_edge(src, dst):
            self.G[src][dst]["weight"] += amount
            self.G[src][dst]["count"] += 1
        else:
            self.G.add_edge(src, dst, weight=amount, count=1, token=token)
            
    def export_frontend_data(self, target_address: str, loss_amount: str = "0", mission_brief: dict = None) -> Dict:
        """Converts internal graph to frontend JSON format required by NEMESIS Tracer/ID."""
        nodes = []
        for n in self.G.nodes:
            inbound_count = sum(1 for _, _, _ in self.G.in_edges(n, data=True))
            total_in = sum(d.get("weight", 0) for _, _, d in self.G.in_edges(n, data=True))
            total_out = sum(d.get("weight", 0) for _, _, d in self.G.out_edges(n, data=True))
            
            group = 0
            if total_in > 0 and total_out == 0: group = 3 # Terminal
            if n == target_address: group = 6 # Seed
            
            nodes.append({
                "id": n,
                "label": "Entity Node",
                "group": group,
                "confidence_level": "Confirmed" if group == 6 else "Analytical Assessment",
                "total_in": total_in,
                "cluster_id": self.G.nodes[n].get("cluster_id", "Unclustered")
            })

        edges = []
        for u, v, d in self.G.edges(data=True):
            edges.append({
                "from_address": u,
                "to_address": v,
                "value": d.get("weight", 0),
                "amount_usd": d.get("weight", 0),
                "token_symbol": d.get("token", "ASSET"),
                "tx_hash": ""
            })

        return {
            "target_address": target_address,
            "loss_amount": loss_amount,
            "mission_brief": mission_brief or {"summary": "Trace", "primary_objectives": []},
            "nodes": nodes,
            "edges": edges,
            "total_volume_usd": self.total_volume_usd,
            "evidence_ledger": self.evidence_ledger,
            "ai_insights": f"Godmode MongoDB trace completed for {target_address}. Depth traversed: {self.max_depth}."
        }
