import logging
from datetime import datetime, timezone

logger = logging.getLogger("OmniChainEngine.CEX")

class CEXClusterer:
    def __init__(self, db):
        self.db = db
        # If DB is None, fallback
        self.mock_db = []
        self.cex_keywords = ["MEXC", "BINANCE", "KRAKEN", "OKX", "COINBASE", "KUCOIN", "HOT WALLET", "HUOBI", "EXCHANGE", "CEX"]
        self.mixer_keywords = ["MIXER", "TORNADO CASH", "RAILGUN"]
        self.bridge_keywords = ["BRIDGE", "STARGATE", "MULTICHAIN", "WORMHOLE", "ORBITER"]
        self.dex_keywords = ["ROUTER", "UNISWAP", "PANCAKESWAP", "SUSHISWAP", "1INCH", "CURVE", "DEX", "SWAP", "DEFI"]

    def classify(self, addr, osint_label):
        if not osint_label:
            return "PRIVATE_NODE", 10
        combined_lbl = str(osint_label).upper()
        if any(keyword in combined_lbl for keyword in self.cex_keywords): return "EXCHANGE_CUSTODIAL", 95
        if any(keyword in combined_lbl for keyword in self.bridge_keywords): return "CROSS_CHAIN_BRIDGE", 70
        if any(keyword in combined_lbl for keyword in self.mixer_keywords): return "MIXER_LIKE", 100
        if any(keyword in combined_lbl for keyword in self.dex_keywords): return "DEX_ROUTER", 70
        return "PRIVATE_NODE", 10

    async def detect_internal_ledger_hop(self, edge: dict):
        """
        Takes a deposit edge into a known CEX cluster.
        Returns a list of simulated withdrawal edges (entity_ids) to follow.
        """
        if self.db is None:
            return []
            
        target = edge.get("to")
        # Check if target is a CEX
        entity = await self.db.entities.find_one({"_id": target})
        if not entity or "cex" not in entity.get("labels", []):
            return []
            
        cex_cluster_id = entity.get("cluster_id")
        
        # In a probabilistic CEX model, we find withdrawals from this cluster around the same time and value
        try:
            # We look for outgoing state_edges from ANY entity in this CEX cluster
            # This is a naive implementation; production requires strict heuristic matching (time, entropy, size)
            # Find all entities in this cluster
            cluster_entities = await self.db.entities.find({"cluster_id": cex_cluster_id}).to_list(length=100)
            cluster_ids = [e["_id"] for e in cluster_entities]
            
            # Find recent withdrawals
            withdrawals = await self.db.state_edges.find({
                "from": {"$in": cluster_ids},
                "edge_type": "TRANSFER",
                # Value and time matching would go here
            }).to_list(length=10)
            
            return [w.get("to") for w in withdrawals if w.get("to")]
            
        except Exception as e:
            logger.error(f"CEX Clustering error: {e}")
            return []
