import logging
from collections import defaultdict
import datetime

logger = logging.getLogger("NemesisOSINT.IdentityEngine")

class IntelligenceConfidenceModel:
    """
    Assigns confidence and attribution scores based on the OSINT Evidence model.
    """
    EVIDENCE_WEIGHTS = {
        "VERIFIED_ENS": 95,
        "SIGNED_MESSAGE": 100,
        "GITHUB_REPO_DOCS": 90,
        "OFFICIAL_WEBSITE": 90,
        "VERIFIED_SOCIAL": 85,
        "GOVERNANCE_VOTE": 85,
        "OFFICIAL_EXPLORER": 80,
        "EXCHANGE_ATTRIBUTION": 80,
        "ARCHIVE_EVIDENCE": 75,
        "COMMUNITY_REFERENCE": 70,
        "WHITEPAPER_MENTION": 65,
        "FORUM_DISCUSSION": 50,
        "BLOG_MENTION": 30,
        "AI_SEMANTIC": 15,
        "OSINT Extracted": 40 # Default fallback for regex extraction
    }

    @staticmethod
    def calculate_score(evidence_list: list) -> int:
        """
        Calculates an aggregate confidence score for an entity based on attached evidence.
        """
        if not evidence_list:
            return 0
            
        score = 0
        for ev in evidence_list:
            weight = IntelligenceConfidenceModel.EVIDENCE_WEIGHTS.get(ev.get("evidence_type", "OSINT Extracted"), 20)
            score = max(score, weight) # Base score on highest single evidence
            
        # Add slight compounding bonus for multiple sources (up to max 100)
        bonus = (len(evidence_list) - 1) * 2
        return min(100, score + bonus)

class IdentityEngine:
    """
    Global Entity Resolution Engine.
    Takes disparate OSINT artifacts and correlates them into a unified Identity Graph node.
    """
    def __init__(self):
        pass

    def resolve_entity(self, address: str, osint_results: dict) -> dict:
        """
        Correlates artifacts into an identity structure.
        """
        identities = {
            "TWITTER": set(),
            "GITHUB": set(),
            "EMAIL": set(),
            "TELEGRAM": set(),
            "ENS": set(),
            "DOMAIN": set(osint_results.get("domains", []))
        }
        
        evidence = osint_results.get("artifacts", [])
        
        for art in evidence:
            t = art.get("type")
            v = art.get("value")
            if t in identities and v:
                identities[t].add(v)
                
        # Calculate Confidence
        confidence_score = IntelligenceConfidenceModel.calculate_score(evidence)
        
        # Build Timeline Event
        timeline_event = {
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "event": "OSINT Correlation Executed",
            "evidence_count": len(evidence)
        }
        
        resolved_node = {
            "wallet_address": address,
            "identities": {k: list(v) for k, v in identities.items()},
            "confidence_score": confidence_score,
            "timeline": [timeline_event],
            "raw_evidence": evidence
        }
        
        logger.info(f"[ENTITY RESOLUTION] Wallet {address} resolved to {len(identities['TWITTER'])} Twitters, {len(identities['GITHUB'])} Githubs with Confidence {confidence_score}%")
        
        return resolved_node

    async def cross_reference_threat_intel(self, address: str) -> dict:
        """
        Cross-references the entity against the Global Threat Intel Engine Database.
        """
        try:
            from services.database_connector import db_connector
            if not db_connector.mongo_db:
                return {"found": False}
                
            intel = await db_connector.mongo_db.threat_intel.find_one({"crypto_address": address.lower()})
            if intel:
                return {
                    "found": True,
                    "source": intel.get("source"),
                    "entity_name": intel.get("entity_name"),
                    "severity": intel.get("severity", "HIGH"),
                    "tags": intel.get("tags", []),
                    "description": intel.get("description", "Sanctioned or flagged entity.")
                }
            return {"found": False}
        except Exception as e:
            logger.error(f"[THREAT INTEL] Cross-reference failed: {e}")
            return {"found": False, "error": str(e)}

identity_engine = IdentityEngine()
