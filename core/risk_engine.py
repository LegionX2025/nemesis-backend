import logging
from typing import Dict, Any, List

logger = logging.getLogger("NEMESIS.GBIO.RiskEngine")

class RiskEngine:
    """
    Tier-11 AML Risk Scoring Engine.
    Calculates deterministic risk scores (0-100) and confidence intervals
    based on entity attribution, behavioral flags, and protocol metadata.
    """
    def __init__(self):
        # Risk Tiers Mapping
        self.risk_weights = {
            "CRITICAL": 95,
            "HIGH": 75,
            "MEDIUM": 50,
            "LOW": 10,
            "UNKNOWN": 25
        }

    async def compute_risk(self, evidence: Dict[str, Any]) -> Dict[str, Any]:
        """
        Computes the final AML Risk Score for a given evidence package.
        """
        logger.info("[RiskEngine] Computing Entity and Transactional Risk Scores...")
        
        attribution = evidence.get("entity_attribution", {})
        protocol = evidence.get("protocol", {})
        behavior_flags = evidence.get("behavior", [])

        src_entity = attribution.get("source_entity", {})
        dst_entity = attribution.get("destination_entity", {})

        # 1. Base Entity Risk
        src_risk_val = self.risk_weights.get(src_entity.get("risk_tier", "UNKNOWN"), 25)
        dst_risk_val = self.risk_weights.get(dst_entity.get("risk_tier", "UNKNOWN"), 25)
        
        base_risk = max(src_risk_val, dst_risk_val)

        # 2. Protocol Risk Modifier
        proto_risk_val = self.risk_weights.get(protocol.get("risk_tier", "UNKNOWN"), 0)
        if proto_risk_val > base_risk:
            base_risk = proto_risk_val

        # 3. Behavioral Modifiers
        modifier = 0
        if "THREAT_VASP_LIQUIDATION" in behavior_flags:
            modifier += 40
        if "MIXER_OBFUSCATION_ATTEMPT" in behavior_flags:
            modifier += 30
        if "VASP_TO_VASP_TRANSFER" in behavior_flags:
            modifier -= 10 # Usually lower risk if traversing KYC'd institutions

        final_score = min(100, max(0, base_risk + modifier))
        
        # 4. Confidence Calculation
        # Confidence increases if entities are known vs unknown
        confidence = 0.0
        if src_entity.get("type") == "KNOWN_ENTITY" and dst_entity.get("type") == "KNOWN_ENTITY":
            confidence = 0.95
        elif src_entity.get("type") == "KNOWN_ENTITY" or dst_entity.get("type") == "KNOWN_ENTITY":
            confidence = 0.70
        else:
            confidence = 0.40

        # Adjust confidence based on protocol fingerprint
        if protocol.get("is_identified"):
            confidence = min(0.99, confidence + 0.15)

        risk_category = "LOW"
        if final_score >= 80:
            risk_category = "CRITICAL"
        elif final_score >= 60:
            risk_category = "HIGH"
        elif final_score >= 40:
            risk_category = "MEDIUM"

        return {
            "score": final_score,
            "category": risk_category,
            "confidence": round(confidence, 2),
            "contributing_factors": {
                "base_entity_risk": base_risk,
                "behavioral_modifier": modifier
            }
        }
