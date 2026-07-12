"""
Risk Engine for Nemesis Intelligence Pipeline
Calculates holistic risk scores for graph nodes and edges.
"""
from typing import Dict, Any, List

class RiskEngine:
    def __init__(self):
        pass

    def calculate_node_risk(self, entity: Dict[str, Any]) -> int:
        """
        Calculates a risk score for a node (0-100).
        """
        score = 0
        tags = entity.get("tags", [])
        
        if "Sanctioned" in tags:
            return 100
        if "Darknet Market" in tags or "Ransomware" in tags or "Scam" in tags:
            return 100
        if "High Risk" in tags or "Mixer" in tags or "Tornado Cash" in tags:
            score += 80
        if "Exchange" in tags:
            score += 10 # Baseline risk for CEX
        if "Bridge" in tags:
            score += 20 # Bridges carry some risk

        return min(score, 100)

    def calculate_edge_risk(self, edge: Dict[str, Any]) -> int:
        """
        Calculates a risk score for an edge (0-100).
        """
        edge_type = edge.get("edge_type", "")
        
        if edge_type in ["TORNADO", "MIXED", "COINJOIN"]:
            return 90
        if edge_type == "SANCTIONED":
            return 100
        if edge_type in ["FLASH_LOAN", "LIQUIDATED"]:
            return 60
        if edge_type in ["BRIDGED_TO", "BRIDGED_FROM"]:
            return 40

        return 10

    def calculate_path_risk(self, path: List[Dict[str, Any]]) -> int:
        """
        Calculates cumulative risk score for a path.
        """
        # Simple implementation: max risk of any node/edge in path
        max_risk = 0
        for element in path:
            if "edge_type" in element:
                max_risk = max(max_risk, self.calculate_edge_risk(element))
            else:
                max_risk = max(max_risk, self.calculate_node_risk(element))
        return max_risk

global_risk_engine = RiskEngine()
