# nemesis/intelligence/threat.py

from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from nemesis.observability.telemetry import logger, tracer
from nemesis.intelligence.resolution import entity_resolver

class ThreatIntelligence(BaseModel):
    wallet_address: str
    risk_score: int # 0-100
    category: str # APT, RANSOMWARE, DRAINER, SCAM, SANCTIONED
    campaign: Optional[str] = None
    attribution_confidence: float

class ThreatEngine:
    def __init__(self):
        self.ofac_sanctioned: set = set()
        self.known_drainers: set = set()

    @tracer.start_as_current_span("threat.evaluate")
    async def evaluate_risk(self, address: str) -> ThreatIntelligence:
        addr = address.lower()
        
        # 1. Check strict OFAC sanctions
        if addr in self.ofac_sanctioned:
            return ThreatIntelligence(
                wallet_address=address,
                risk_score=100,
                category="SANCTIONED",
                attribution_confidence=1.0
            )
            
        # 2. Check Drainer lists
        if addr in self.known_drainers:
            return ThreatIntelligence(
                wallet_address=address,
                risk_score=95,
                category="DRAINER",
                attribution_confidence=0.9
            )
            
        # 3. Base risk on Entity Resolution
        resolved = await entity_resolver.resolve_entity(address)
        if resolved and resolved.entity_type == "EXCHANGE":
            return ThreatIntelligence(
                wallet_address=address,
                risk_score=15, # Low risk, CEX
                category="REGULATED_VASP",
                attribution_confidence=1.0
            )

        # Default unknown
        return ThreatIntelligence(
            wallet_address=address,
            risk_score=30,
            category="UNKNOWN",
            attribution_confidence=0.0
        )

threat_engine = ThreatEngine()
