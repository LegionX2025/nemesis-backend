import urllib.parse
import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("GBEO_ENGINE")

class GBEO_Ontology:
    """
    Global Blockchain Explorer Ontology (GBEO) v4
    Maps chains to canonical explorer URL structures for forensic tracing.
    """
    EXPLORERS = {
        "ETHEREUM": {"base": "https://etherscan.io", "type": "EVM"},
        "BASE": {"base": "https://basescan.org", "type": "EVM"},
        "ARBITRUM": {"base": "https://arbiscan.io", "type": "EVM"},
        "OPTIMISM": {"base": "https://optimistic.etherscan.io", "type": "EVM"},
        "POLYGON": {"base": "https://polygonscan.com", "type": "EVM"},
        "BSC": {"base": "https://bscscan.com", "type": "EVM"},
        "AVALANCHE": {"base": "https://snowtrace.io", "type": "EVM"},
        "FANTOM": {"base": "https://ftmscan.com", "type": "EVM"},
        "SONIC": {"base": "https://sonicscan.org", "type": "EVM"},
        "SCROLL": {"base": "https://scrollscan.com", "type": "EVM"},
        "LINEA": {"base": "https://lineascan.build", "type": "EVM"},
        "BLAST": {"base": "https://blastscan.io", "type": "EVM"},
        "MANTLE": {"base": "https://mantlescan.xyz", "type": "EVM"},
        "CRONOS": {"base": "https://cronoscan.com", "type": "EVM"},
        "GNOSIS": {"base": "https://gnosisscan.io", "type": "EVM"},
        "HARMONY": {"base": "https://explorer.harmony.one", "type": "EVM"}
    }

    @staticmethod
    def get_wallet_url(chain: str, address: str) -> str:
        chain = chain.upper()
        if chain in GBEO_Ontology.EXPLORERS:
            base = GBEO_Ontology.EXPLORERS[chain]["base"]
            return f"{base}/address/{address}"
        return f"https://{chain.lower()}.blockscout.com/address/{address}"

    @staticmethod
    def get_transaction_url(chain: str, txhash: str) -> str:
        chain = chain.upper()
        if chain in GBEO_Ontology.EXPLORERS:
            base = GBEO_Ontology.EXPLORERS[chain]["base"]
            return f"{base}/tx/{txhash}"
        return f"https://{chain.lower()}.blockscout.com/tx/{txhash}"

    @staticmethod
    def get_token_url(chain: str, token: str) -> str:
        chain = chain.upper()
        if chain in GBEO_Ontology.EXPLORERS:
            base = GBEO_Ontology.EXPLORERS[chain]["base"]
            return f"{base}/token/{token}"
        return f"https://{chain.lower()}.blockscout.com/token/{token}"

    @staticmethod
    def get_contract_source_url(chain: str, address: str) -> str:
        chain = chain.upper()
        if chain in GBEO_Ontology.EXPLORERS:
            base = GBEO_Ontology.EXPLORERS[chain]["base"]
            return f"{base}/address/{address}#code"
        return f"https://{chain.lower()}.blockscout.com/address/{address}?tab=contract"


class NEMESISExplorerAdapter:
    """
    Implements the Universal Detection Matrix and State Transition logic.
    """
    def __init__(self, chain: str):
        self.chain = chain.upper()

    def fingerprint_entity(self, address: str, metadata: dict) -> dict:
        """
        Extract tags, AML risk, and entity cluster from raw DOM/API metadata.
        """
        fingerprint = {
            "entity": "Unknown",
            "tags": [],
            "risk_score": 0,
            "type": "EOA"
        }
        
        raw_text = str(metadata).upper()
        
        # Heuristic tagging
        if "CONTRACT" in raw_text or "ABI" in raw_text:
            fingerprint["type"] = "CONTRACT"
        
        if any(exch in raw_text for exch in ["BINANCE", "KRAKEN", "COINBASE", "OKX", "MEXC", "BYBIT"]):
            fingerprint["entity"] = "EXCHANGE"
            fingerprint["tags"].append("CEX")
            fingerprint["risk_score"] = max(fingerprint["risk_score"], 20)
            
        if "TORNADO" in raw_text or "MIXER" in raw_text:
            fingerprint["entity"] = "MIXER"
            fingerprint["tags"].append("HIGH_RISK")
            fingerprint["tags"].append("OFAC_SANCTIONED")
            fingerprint["risk_score"] = 100
            
        if "BRIDGE" in raw_text or "ROUTER" in raw_text or "GATEWAY" in raw_text:
            fingerprint["entity"] = "BRIDGE"
            fingerprint["tags"].append("CROSS_CHAIN")
            fingerprint["risk_score"] = 40
            
        return fingerprint

    def model_state_transition(self, tx_data: dict) -> str:
        """
        Maps raw transaction data to the Category A-U State Transition Ontology.
        """
        method = str(tx_data.get("method", "")).upper()
        logs = str(tx_data.get("logs", [])).upper()
        
        if "SWAP" in method:
            return "Swap"
        elif "DEPOSIT" in method and "LIDO" in logs:
            return "Stake"
        elif "LOCK" in method or "BRIDGE" in logs:
            return "Bridge Lock"
        elif "MINT" in method:
            return "Mint"
        elif "BURN" in method:
            return "Burn"
        else:
            return "Transfer"
