"""
NEMESIS V3.1 - Global Identity Resolution Layer (GIRL)
Standardizes entities, wallets, and tokens into a global canonical schema.
Uses cryptologos.cc as primary fallback.
"""

import os
import json
import logging
import re
from typing import Dict, Any

logger = logging.getLogger("NEMESIS.IdentityResolver")

# Known entity and classification mappings
KNOWN_ENTITIES = {
    "binance": {"logo": "/assets/entities/binance.svg", "classification": "Exchange", "risk": 15},
    "coinbase": {"logo": "/assets/entities/coinbase.svg", "classification": "Exchange", "risk": 10},
    "kraken": {"logo": "/assets/entities/kraken.svg", "classification": "Exchange", "risk": 10},
    "okx": {"logo": "/assets/entities/okx.svg", "classification": "Exchange", "risk": 20},
    "bybit": {"logo": "/assets/entities/bybit.svg", "classification": "Exchange", "risk": 25},
    "tornado cash": {"logo": "/assets/entities/tornado-cash.svg", "classification": "Mixer", "risk": 100},
    "lazarus": {"logo": "/assets/classifications/sanction.svg", "classification": "Sanctioned Entity", "risk": 100}
}

CHAIN_MAP = {
    "ethereum": {"logo": "https://cryptologos.cc/logos/ethereum-eth-logo.png", "native": "ETH", "color": "#627EEA"},
    "bitcoin": {"logo": "https://cryptologos.cc/logos/bitcoin-btc-logo.png", "native": "BTC", "color": "#F7931A"},
    "solana": {"logo": "https://cryptologos.cc/logos/solana-sol-logo.png", "native": "SOL", "color": "#00FFA3"},
    "polygon": {"logo": "https://cryptologos.cc/logos/polygon-matic-logo.png", "native": "POL", "color": "#8247E5"},
    "bsc": {"logo": "https://cryptologos.cc/logos/bnb-bnb-logo.png", "native": "BNB", "color": "#F3BA2F"},
    "arbitrum": {"logo": "https://cryptologos.cc/logos/arbitrum-arb-logo.png", "native": "ARB", "color": "#28A0F0"},
    "optimism": {"logo": "https://cryptologos.cc/logos/optimism-ethereum-op-logo.png", "native": "OP", "color": "#FF0420"},
    "base": {"logo": "https://cryptologos.cc/logos/base-logo.png", "native": "ETH", "color": "#0052FF"},
    "tron": {"logo": "https://cryptologos.cc/logos/tron-trx-logo.png", "native": "TRX", "color": "#FF0013"},
}

TOKEN_MAP = {
    "usdt": "https://cryptologos.cc/logos/tether-usdt-logo.png",
    "usdc": "https://cryptologos.cc/logos/usd-coin-usdc-logo.png",
    "dai": "https://cryptologos.cc/logos/multi-collateral-dai-dai-logo.png",
    "link": "https://cryptologos.cc/logos/chainlink-link-logo.png",
    "uni": "https://cryptologos.cc/logos/uniswap-uni-logo.png",
}

class IdentityResolver:
    def __init__(self):
        pass
        
    def _resolve_entity_logo(self, entity_name: str) -> str:
        if not entity_name: return "/assets/classifications/wallet.svg"
        name_lower = entity_name.lower()
        for key, data in KNOWN_ENTITIES.items():
            if key in name_lower:
                return data["logo"]
        return "/assets/classifications/wallet.svg"

    def _resolve_classification(self, entity_name: str) -> str:
        if not entity_name: return "Unknown EOA"
        name_lower = entity_name.lower()
        for key, data in KNOWN_ENTITIES.items():
            if key in name_lower:
                return data["classification"]
        if "hot wallet" in name_lower: return "Hot Wallet"
        if "router" in name_lower or "bridge" in name_lower: return "Bridge"
        if "exploit" in name_lower or "hack" in name_lower: return "Exploiter"
        return "Smart Contract"

    def _calculate_risk(self, entity_name: str, chain: str) -> int:
        if not entity_name: return 0
        name_lower = entity_name.lower()
        for key, data in KNOWN_ENTITIES.items():
            if key in name_lower:
                return data["risk"]
        if "exploit" in name_lower or "hack" in name_lower or "scam" in name_lower: return 100
        return 0

    def get_token_logo(self, symbol: str) -> str:
        """Returns standard logo URL for a token."""
        if not symbol: return ""
        symbol_lower = symbol.lower()
        if symbol_lower in TOKEN_MAP:
            return TOKEN_MAP[symbol_lower]
        # Auto-fallback mapping for cryptologos generic tokens (best effort)
        # E.g. AAVE -> https://cryptologos.cc/logos/aave-aave-logo.png
        return f"https://cryptologos.cc/logos/{symbol_lower}-{symbol_lower}-logo.png"

    def resolve_wallet(self, address: str, chain: str, raw_entity_name: str = None) -> Dict[str, Any]:
        """
        Takes raw blockchain metadata and standardizes it into the NEMESIS canonical schema.
        """
        chain_info = CHAIN_MAP.get(chain.lower(), CHAIN_MAP["ethereum"])
        
        entity_name = raw_entity_name if raw_entity_name else "Unknown Address"
        entity_logo = self._resolve_entity_logo(entity_name)
        classification = self._resolve_classification(entity_name)
        risk = self._calculate_risk(entity_name, chain)
        
        # Calculate confidence randomly for UI simulation if unknown, 
        # or 99% if it's a strongly labeled entity
        confidence = 99.8 if raw_entity_name and raw_entity_name != "Unknown Address" else 45.0

        return {
            "id": f"{chain.lower()}:{address}",
            "address": address,
            "entity_name": entity_name,
            "entity_logo": entity_logo,
            "classification": classification,
            "wallet_type": "Hot Wallet" if "hot wallet" in entity_name.lower() else "EOA",
            "chain": chain.title(),
            "chain_logo": chain_info["logo"],
            "native_asset": chain_info["native"],
            "risk_score": risk,
            "confidence": confidence,
            "verified": bool(raw_entity_name and raw_entity_name != "Unknown Address"),
            "tags": [classification, chain.title()]
        }

# Global singleton
girl = IdentityResolver()
