import logging
import traceback
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger("NEMESIS.GBIO.Engine")

class GlobalBlockchainIntelligenceOntologyEngine:
    """
    GBIO Central Orchestrator.
    Maps raw transactions and trace hops through the entire forensic pipeline.
    Implements strict Tier-11 provenance and evidence preservation requirements.
    """
    
    def __init__(self):
        # Dependencies will be injected as they are built (Dependency Injection Ready)
        self.decoder_engine = None
        self.transfer_classifier = None
        self.protocol_fingerprint = None
        self.entity_attribution = None
        self.graph_engine = None
        self.behavior_engine = None
        self.risk_engine = None
        self.evidence_engine = None
        
        self.ontology_version = "v1.1.0-tier-11"
        self._initialize_core_ontology()

    def _initialize_core_ontology(self):
        """Initializes the base GBIO categories in-memory."""
        logger.info("[GBIO Engine] Initializing Global Blockchain Intelligence Ontology...")
        self.categories = [
            "Entity", "Transfer", "Relationship", "Protocol", 
            "Threat", "Risk", "Behavior", "Evidence", "AML", "Investigation"
        ]

    def _generate_unknown_result(self, module: str, reason: str, exception: Optional[Exception] = None) -> Dict[str, Any]:
        """
        Enforces the 'WHEN DATA IS UNAVAILABLE' directive.
        Never invent information. Return structured 'unknown' results with provenance.
        """
        return {
            "status": "UNKNOWN",
            "module": module,
            "provenance": reason,
            "confidence": 0.0,
            "error_trace": traceback.format_exc() if exception else None,
            "timestamp": datetime.utcnow().isoformat()
        }

    async def process_transaction(self, raw_tx: Dict[str, Any], chain: str = "ethereum") -> Dict[str, Any]:
        """
        The central pipeline for transforming a raw transaction into a complete GBIO Evidence Package.
        Executes robust Try/Catch across every module to prevent trace failure.
        """
        tx_hash = raw_tx.get("hash", "UNKNOWN_HASH")
        logger.info(f"[GBIO Engine] Processing transaction {tx_hash} on {chain}")
        
        evidence_package = {
            "transaction_hash": tx_hash,
            "chain": chain,
            "timestamp": raw_tx.get("timestamp", datetime.utcnow().isoformat()),
            "status": "PROCESSING",
            "ontology_version": self.ontology_version,
            "decoded_data": {},
            "transfer_type": {},
            "protocol": {},
            "entity_attribution": {},
            "behavior": {},
            "risk": {},
            "graph_edges": [],
            "provenance_log": []
        }

        # --- PIPELINE STAGE 1: Decoding ---
        if self.decoder_engine:
            try:
                evidence_package["decoded_data"] = await self.decoder_engine.decode(raw_tx, chain)
                evidence_package["provenance_log"].append({"stage": "Decoding", "status": "SUCCESS"})
            except Exception as e:
                logger.error(f"[GBIO Engine] Decoder failure for {tx_hash}: {e}")
                evidence_package["decoded_data"] = self._generate_unknown_result("DecoderEngine", "Failed to resolve ABI or decode payload.", e)
        else:
            evidence_package["decoded_data"] = self._generate_unknown_result("DecoderEngine", "Module not injected.")

        # --- PIPELINE STAGE 2: Transfer Classification ---
        if self.transfer_classifier:
            try:
                evidence_package["transfer_type"] = await self.transfer_classifier.classify(raw_tx, evidence_package["decoded_data"])
                evidence_package["provenance_log"].append({"stage": "Classification", "status": "SUCCESS"})
            except Exception as e:
                evidence_package["transfer_type"] = self._generate_unknown_result("TransferClassifier", "Classification heuristics failed.", e)
        else:
            evidence_package["transfer_type"] = self._generate_unknown_result("TransferClassifier", "Module not injected.")

        # --- PIPELINE STAGE 3: Protocol Fingerprinting ---
        if self.protocol_fingerprint:
            try:
                evidence_package["protocol"] = await self.protocol_fingerprint.identify(raw_tx, evidence_package["decoded_data"])
                evidence_package["provenance_log"].append({"stage": "ProtocolFingerprint", "status": "SUCCESS"})
            except Exception as e:
                evidence_package["protocol"] = self._generate_unknown_result("ProtocolFingerprint", "Failed to fingerprint protocol behavior.", e)
        else:
            evidence_package["protocol"] = self._generate_unknown_result("ProtocolFingerprint", "Module not injected.")

        # --- PIPELINE STAGE 4: Entity Attribution ---
        if self.entity_attribution:
            try:
                evidence_package["entity_attribution"] = await self.entity_attribution.resolve(raw_tx, evidence_package["protocol"])
                evidence_package["provenance_log"].append({"stage": "EntityAttribution", "status": "SUCCESS"})
            except Exception as e:
                evidence_package["entity_attribution"] = self._generate_unknown_result("EntityAttribution", "Entity resolution engine failed.", e)
        else:
            evidence_package["entity_attribution"] = self._generate_unknown_result("EntityAttribution", "Module not injected.")

        # --- PIPELINE STAGE 5: Behavioral Analysis ---
        if self.behavior_engine:
            try:
                evidence_package["behavior"] = await self.behavior_engine.analyze(evidence_package)
                evidence_package["provenance_log"].append({"stage": "BehaviorEngine", "status": "SUCCESS"})
            except Exception as e:
                evidence_package["behavior"] = self._generate_unknown_result("BehaviorEngine", "Behavioral rule evaluation failed.", e)
        else:
            evidence_package["behavior"] = self._generate_unknown_result("BehaviorEngine", "Module not injected.")

        # --- PIPELINE STAGE 6: Graph Generation ---
        if self.graph_engine:
            try:
                evidence_package["graph_edges"] = await self.graph_engine.correlate_edges(evidence_package)
                evidence_package["provenance_log"].append({"stage": "GraphCorrelation", "status": "SUCCESS"})
            except Exception as e:
                evidence_package["provenance_log"].append(self._generate_unknown_result("GraphCorrelationEngine", "Failed to generate recursive edges.", e))
        else:
             evidence_package["provenance_log"].append(self._generate_unknown_result("GraphCorrelationEngine", "Module not injected."))

        # --- PIPELINE STAGE 7: Risk & AML Scoring ---
        if self.risk_engine:
            try:
                evidence_package["risk"] = await self.risk_engine.compute_risk(evidence_package)
                evidence_package["provenance_log"].append({"stage": "RiskEngine", "status": "SUCCESS"})
            except Exception as e:
                evidence_package["risk"] = self._generate_unknown_result("RiskEngine", "AML Scoring failed.", e)
        else:
            evidence_package["risk"] = self._generate_unknown_result("RiskEngine", "Module not injected.")

        evidence_package["status"] = "COMPLETED"
        return evidence_package
