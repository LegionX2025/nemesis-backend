"""
Protocol Registry for Nemesis Intelligence Engine
Contains hardcoded/in-memory dictionaries mapping addresses to entities.
In a production system, these can be populated from the D1/Hyperdrive database.
"""
from typing import Optional, Dict, Any

class ProtocolRegistry:
    def __init__(self):
        # Maps address (lowercase) to an entity dictionary
        self.exchanges: Dict[str, Dict[str, Any]] = {}
        self.bridges: Dict[str, Dict[str, Any]] = {}
        self.mixers: Dict[str, Dict[str, Any]] = {}
        self.dexes: Dict[str, Dict[str, Any]] = {}
        
        self._seed_data()

    def _seed_data(self):
        # Example seed data
        
        # Exchanges
        self.exchanges.update({
            "0x28c6c06298d514db089934071355e5743bf21d60": {
                "name": "Binance 14",
                "chain": "ETH",
                "category": "Exchange",
                "tags": ["Hot Wallet", "Binance", "CEX"],
                "confidence": 100,
                "risk_score": 25
            },
            "0x5e032243d507c743b061ef021e2ec7fcc6d3ab89": {
                "name": "KuCoin 6",
                "chain": "ETH",
                "category": "Exchange",
                "tags": ["Hot Wallet", "KuCoin", "CEX"],
                "confidence": 100,
                "risk_score": 30
            }
        })
        
        # Mixers
        self.mixers.update({
            "0x12d66f87a04a9e220743712ce6d9bb1b5616b8fc": {
                "name": "Tornado Cash: 100 ETH",
                "chain": "ETH",
                "category": "Mixer",
                "tags": ["Tornado Cash", "Privacy", "High Risk", "Sanctioned"],
                "confidence": 100,
                "risk_score": 100
            }
        })
        
        # Bridges
        self.bridges.update({
            "0x40ec5b33f54e0e8a33a975908c5ba1c14e5bbbdf": {
                "name": "Polygon ERC20 Bridge",
                "chain": "ETH",
                "category": "Bridge",
                "tags": ["Polygon", "L2 Bridge"],
                "confidence": 100,
                "risk_score": 15
            }
        })

    def lookup_address(self, address: str) -> Optional[Dict[str, Any]]:
        """Look up an address across all registries."""
        address_lower = address.lower()
        if address_lower in self.exchanges:
            return self.exchanges[address_lower]
        if address_lower in self.bridges:
            return self.bridges[address_lower]
        if address_lower in self.mixers:
            return self.mixers[address_lower]
        if address_lower in self.dexes:
            return self.dexes[address_lower]
            
        return None

# Global registry instance
global_registry = ProtocolRegistry()
