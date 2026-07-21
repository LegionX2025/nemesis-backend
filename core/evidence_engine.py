import logging
from typing import Dict, Any, List
from datetime import datetime

logger = logging.getLogger("NEMESIS.GBIO.EvidenceEngine")

class EvidenceEngine:
    """
    Tier-11 Evidence Generation Engine.
    Stitches the fully analyzed GBIO pipeline state into the finalized 
    `Nemesis ID` structured format for immediate ingestion by the UI and Downstream APIs.
    """
    def __init__(self):
        pass

    def generate_nemesis_id_profile(self, target_address: str, evidence_packages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Aggregates multiple transaction evidence packages into a single Entity Profile.
        Replaces the old mock generator.
        """
        logger.info(f"[EvidenceEngine] Generating Nemesis ID for {target_address}")
        
        total_tx = len(evidence_packages)
        if total_tx == 0:
            return self._empty_profile(target_address)

        # Aggregate metrics
        cex_interactions = {}
        osint_findings = []
        max_risk = 0
        
        for pkg in evidence_packages:
            # Risk Aggregation
            risk = pkg.get("risk", {}).get("score", 0)
            if risk > max_risk:
                max_risk = risk
                
            # CEX Tracking
            attr = pkg.get("entity_attribution", {})
            for entity_key in ["source_entity", "destination_entity"]:
                ent = attr.get(entity_key, {})
                if ent.get("is_vasp"):
                    name = ent.get("name")
                    cex_interactions[name] = cex_interactions.get(name, 0) + 1 # count interactions

            # OSINT Aggregation
            for entity_key in ["source_entity", "destination_entity"]:
                ent = attr.get(entity_key, {})
                if ent.get("osint_data"):
                    for osint in ent.get("osint_data"):
                         # Avoid duplicates
                         if osint not in osint_findings:
                             osint_findings.append(osint)

        cex_list = [{"exchange": name, "interactions": count} for name, count in cex_interactions.items()]

        return {
            "address": target_address,
            "network": evidence_packages[0].get("chain", "ethereum").upper(),
            "first_activity": evidence_packages[0].get("timestamp"),
            "last_activity": evidence_packages[-1].get("timestamp"),
            "tx_count": total_tx,
            "max_risk_score": max_risk,
            "cex_interactions": cex_list,
            "osint": [{"source": "GBIO OSINT Engine", "info": finding.get("label")} for finding in osint_findings] if osint_findings else [],
            "analytics": {
                "profile_generated_at": datetime.utcnow().isoformat(),
                "ontology_version": evidence_packages[0].get("ontology_version")
            }
        }

    def _empty_profile(self, address: str) -> Dict[str, Any]:
        return {
            "address": address,
            "network": "UNKNOWN",
            "tx_count": 0,
            "max_risk_score": 0,
            "cex_interactions": [],
            "osint": [{"source": "System", "info": "No on-chain activity found for this address within scope."}],
            "analytics": {
                "profile_generated_at": datetime.utcnow().isoformat()
            }
        }
