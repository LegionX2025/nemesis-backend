import logging
from typing import Dict, Any, List
import hashlib

logger = logging.getLogger("NEMESIS.GBIO.GraphCorrelation")

class GraphCorrelationEngine:
    """
    Tier-11 Graph Correlation Engine.
    Transforms linear transaction evidence into temporal graph nodes and edges
    compatible with Vis.js rendering in the Nemesis Command Center.
    """
    
    def __init__(self):
        # We assign standard imagery to node categories for the UI
        self.image_map = {
            "CEX": "https://cryptologos.cc/logos/binance-coin-bnb-logo.png",
            "DEX": "https://cryptologos.cc/logos/uniswap-uni-logo.png",
            "MIXER": "https://cryptologos.cc/logos/tornado-cash-torn-logo.png",
            "BRIDGE": "https://cryptologos.cc/logos/stargate-finance-stg-logo.png",
            "THREAT_ACTOR": "https://img.icons8.com/color/48/000000/hacker.png",
            "UNKNOWN_ENTITY": "https://cryptologos.cc/logos/ethereum-eth-logo.png"
        }

    def _generate_node_id(self, address: str) -> str:
        return address.lower() if address else f"unknown_{hashlib.md5(b'unknown').hexdigest()[:8]}"

    async def correlate_edges(self, evidence: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processes an evidence package and constructs standard Graph edges and nodes.
        """
        logger.info("[GraphCorrelation] Generating Temporal Graph structures...")
        
        nodes = []
        edges = []

        tx_hash = evidence.get("transaction_hash", "")
        chain = evidence.get("chain", "ethereum")
        transfer_type = evidence.get("transfer_type", {}).get("primary_type", "UNKNOWN")
        attribution = evidence.get("entity_attribution", {})
        
        src_entity = attribution.get("source_entity", {})
        dst_entity = attribution.get("destination_entity", {})
        
        src_addr = src_entity.get("address", "")
        dst_addr = dst_entity.get("address", "")

        src_id = self._generate_node_id(src_addr)
        dst_id = self._generate_node_id(dst_addr)

        # 1. Construct Source Node
        nodes.append({
            "id": src_id,
            "label": src_entity.get("name", "Unknown Sender")[:20],
            "group": src_entity.get("category", "UNKNOWN").lower(),
            "shape": "circularImage",
            "image": self.image_map.get(src_entity.get("category"), self.image_map["UNKNOWN_ENTITY"]),
            "title": f"Address: {src_addr}\nCategory: {src_entity.get('category')}\nRisk: {src_entity.get('risk_tier')}"
        })

        # 2. Construct Destination Node
        nodes.append({
            "id": dst_id,
            "label": dst_entity.get("name", "Unknown Receiver")[:20],
            "group": dst_entity.get("category", "UNKNOWN").lower(),
            "shape": "circularImage",
            "image": self.image_map.get(dst_entity.get("category"), self.image_map["UNKNOWN_ENTITY"]),
            "title": f"Address: {dst_addr}\nCategory: {dst_entity.get('category')}\nRisk: {dst_entity.get('risk_tier')}"
        })

        # 3. Construct Temporal Edge
        # Edge color reflects the transfer type or risk
        edge_color = "#3b82f6" # default blue
        if "MIXER" in transfer_type or "THREAT" in dst_entity.get("category", ""):
            edge_color = "#ef4444" # red for high risk
        elif transfer_type in ["SWAP", "LIQUIDITY_ADD"]:
            edge_color = "#10b981" # green for DeFi
            
        edge_label = f"{transfer_type}\n{chain.upper()}"
        
        edges.append({
            "from": src_id,
            "to": dst_id,
            "label": edge_label,
            "color": {"color": edge_color},
            "arrows": "to",
            "title": f"Tx: {tx_hash}\nType: {transfer_type}"
        })

        # 4. Handle Bridge Cross-Chain Branches
        bridge_info = evidence.get("bridge_correlation", {})
        if bridge_info and bridge_info.get("is_cross_chain"):
            bridge_dest_chain = bridge_info.get("predicted_destination_chain")
            branch_id = f"{dst_id}_bridge_{bridge_dest_chain}"
            
            nodes.append({
                "id": branch_id,
                "label": f"[{bridge_dest_chain.upper()}]\nDest Network",
                "group": "network",
                "shape": "box",
                "color": "#f59e0b"
            })
            
            edges.append({
                "from": dst_id,
                "to": branch_id,
                "label": "CROSS_CHAIN\nROUTE",
                "dashes": True,
                "color": {"color": "#f59e0b"},
                "arrows": "to"
            })

        # Deduplicate nodes by ID
        unique_nodes = {n["id"]: n for n in nodes}.values()

        return {
            "nodes": list(unique_nodes),
            "edges": edges
        }
