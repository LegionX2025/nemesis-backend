import logging
from typing import Dict, Any, Optional
from services.gbeo_parser import GBEOParser
from services.ontology import WALLET_CLASSIFICATION_ONTOLOGY

logger = logging.getLogger("OmniChainEngine.Resolver")

class EntityResolver:
    def __init__(self):
        self.gbeo = GBEOParser()
        self.scraper = None

    def _get_scraper(self):
        if self.scraper is None:
            from services.playwright_scraper import HeadlessExplorerScraper
            self.scraper = HeadlessExplorerScraper()
        return self.scraper

    def resolve_entity(self, address: str, network: str = "ETHEREUM") -> Dict[str, Any]:
        """
        Executes the Auto-Resolver Intelligence Pipeline.
        1. Gets Canonical URL.
        2. Tries to scrape labels from DOM/Title.
        3. Classifies using Ontology.
        """
        logger.info(f"Resolving entity for {address} on {network}")
        
        canonical_url = self.gbeo.get_wallet_url(network, address)
        
        # Base Intelligence Profile
        intelligence_profile = {
            "address": address,
            "network": network.upper(),
            "explorer_url": canonical_url or f"https://etherscan.io/address/{address}",
            "attribution_source": "GBEO v3",
            "entity_type": "Unknown",
            "labels": [],
            "risk_score": 0,
            "resolved": False
        }

        # Fallback heuristic for entity classification if no scrape data is available yet
        classification = self.classify_wallet(address, labels=intelligence_profile["labels"])
        intelligence_profile["entity_type"] = classification
        
        if classification != "Unknown":
            intelligence_profile["resolved"] = True
            
        # Example risk scoring based on classification
        if classification in ["Mixer", "Darknet Market", "Ransomware", "Scam", "Wallet Drainer", "Sanctioned"]:
            intelligence_profile["risk_score"] = 99
        elif classification in ["Exchange Hot Wallet", "Custodial Wallet", "OTC Broker", "Mixer"]:
            intelligence_profile["risk_score"] = 50

        return intelligence_profile

    def classify_wallet(self, address: str, labels: list = None) -> str:
        """
        Normalizes discovered labels into the standardized GBEO v3 taxonomy.
        """
        if not labels:
            return "Unknown"
            
        combined_text = " ".join(labels).lower()
        
        # Heuristic mapping to the ontology
        if "exchange" in combined_text and "hot" in combined_text:
            return "Exchange Hot Wallet"
        elif "exchange" in combined_text and "cold" in combined_text:
            return "Exchange Cold Wallet"
        elif "exchange" in combined_text or "binance" in combined_text or "kraken" in combined_text:
            return "Exchange"
        elif "bridge" in combined_text:
            return "Bridge"
        elif "mev" in combined_text or "bot" in combined_text:
            return "MEV Bot"
        elif "mixer" in combined_text or "tornado" in combined_text:
            return "Mixer"
        elif "scam" in combined_text or "phish" in combined_text:
            return "Scam"
            
        for category in WALLET_CLASSIFICATION_ONTOLOGY:
            if category.lower() in combined_text:
                return category
                
        return "Private Wallet"
