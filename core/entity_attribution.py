import logging
from typing import Dict, Any, List

logger = logging.getLogger("NEMESIS.GBIO.EntityAttribution")

class EntityAttributionEngine:
    """
    Tier-11 Entity Attribution & Labeling Engine.
    Resolves blockchain addresses to real-world entities, organizations, 
    exchanges, threat actors, and DAOs. Uses local deterministic maps
    and calls out to the Scraper/OSINT engine when unknown.
    """
    
    def __init__(self, scraper=None):
        self.scraper = scraper # PlaywrightWalletScraper dependency injection
        self._initialize_deterministic_labels()

    def _initialize_deterministic_labels(self):
        """
        Loads the core Tier-11 entity map. 
        In production, this is loaded from a massive distributed database.
        """
        self.known_entities = {
            "0xbinance_hot": {"name": "Binance Hot Wallet 1", "category": "CEX", "risk_tier": "LOW", "is_vasp": True},
            "0xkraken_deposit": {"name": "Kraken Exchange", "category": "CEX", "risk_tier": "LOW", "is_vasp": True},
            "0xlazarus_group": {"name": "Lazarus Group (DPRK)", "category": "THREAT_ACTOR", "risk_tier": "CRITICAL", "is_vasp": False},
            "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D": {"name": "Uniswap V2: Router", "category": "DEX", "risk_tier": "LOW", "is_vasp": False},
            "0x47ce0c6ed5b0ce3d3a51fdb1c52dc66a7c3c2936": {"name": "Tornado Cash: Router", "category": "MIXER", "risk_tier": "CRITICAL", "is_vasp": False}
        }

    async def resolve(self, raw_tx: Dict[str, Any], protocol_info: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Resolves the target and source addresses to entities.
        """
        to_address = raw_tx.get("to", "").lower()
        from_address = raw_tx.get("from", "").lower()
        
        logger.info(f"[EntityAttribution] Resolving entities for TX: {raw_tx.get('hash', 'UNKNOWN')}")

        result = {
            "source_entity": await self._resolve_address(from_address),
            "destination_entity": await self._resolve_address(to_address),
            "is_vasp_involved": False,
            "threat_actor_involved": False
        }

        # Contextual Overrides based on Protocol Fingerprint
        if protocol_info and protocol_info.get("is_identified"):
            # If the destination is a known protocol but missing from our static map, use the fingerprint.
            if result["destination_entity"]["type"] == "UNKNOWN_ENTITY":
                result["destination_entity"] = {
                    "address": to_address,
                    "name": protocol_info["primary_protocol"],
                    "category": protocol_info["category"],
                    "risk_tier": protocol_info["risk_tier"],
                    "type": "PROTOCOL_CONTRACT",
                    "is_vasp": False
                }

        # Flag Threat & VASP involvement for AML Engine
        for entity_key in ["source_entity", "destination_entity"]:
            entity = result[entity_key]
            if entity.get("is_vasp"):
                result["is_vasp_involved"] = True
            if entity.get("category") == "THREAT_ACTOR":
                result["threat_actor_involved"] = True

        return result

    async def _resolve_address(self, address: str) -> Dict[str, Any]:
        """
        Internal resolver. Checks deterministic map, then attempts OSINT scrape.
        """
        if not address:
             return {"address": address, "name": "Contract Creation", "type": "SYSTEM", "category": "NETWORK"}

        # 1. Deterministic Map Check
        # Fast lookup against lowercase address
        for known_addr, profile in self.known_entities.items():
            if address == known_addr.lower():
                return {
                    "address": address,
                    "name": profile["name"],
                    "category": profile["category"],
                    "risk_tier": profile["risk_tier"],
                    "type": "KNOWN_ENTITY",
                    "is_vasp": profile["is_vasp"]
                }

        # 2. OSINT Fallback
        osint_labels = []
        if self.scraper:
            try:
                # E.g., scraping Etherscan labels dynamically
                target_url = f"https://etherscan.io/address/{address}"
                osint_labels = await self.scraper.scrape_entity_labels(target_url)
            except Exception as e:
                logger.debug(f"[EntityAttribution] OSINT scrape failed for {address}: {e}")

        if osint_labels:
            return {
                "address": address,
                "name": osint_labels[0].get("label", "Unknown Label"),
                "category": "OSINT_DISCOVERED",
                "risk_tier": "UNKNOWN",
                "type": "OSINT_ENTITY",
                "is_vasp": False, # Assume False unless confirmed
                "osint_data": osint_labels
            }

        # 3. Completely Unknown
        return {
            "address": address,
            "name": "Unknown Entity",
            "category": "UNKNOWN",
            "risk_tier": "UNKNOWN",
            "type": "UNKNOWN_ENTITY",
            "is_vasp": False
        }
