import logging
from app.services.gbeo_ontology import EXPLORER_FAMILIES, get_canonical_endpoints, WALLET_CLASSIFICATION_ONTOLOGY

logger = logging.getLogger(__name__)

class ExplorerAdapter:
    def __init__(self):
        self.families = EXPLORER_FAMILIES
        
    def _find_chain_config(self, chain: str) -> dict:
        chain_upper = str(chain).upper()
        for family, chains in self.families.items():
            if chain_upper in chains:
                return chains[chain_upper], family
        
        # Fallback for intelligence mapping (e.g., OKLink fallback)
        if chain_upper in ["ETH", "ETHEREUM"]:
            return self.families["EVM"]["ETH"], "EVM"
        if chain_upper in ["BSC", "BNB"]:
            return self.families["EVM"]["BSC"], "EVM"
            
        return None, None

    def get_wallet_url(self, chain: str, address: str, use_intelligence_explorer=False) -> str:
        if use_intelligence_explorer:
            base = self.families["INTELLIGENCE"]["OKLINK"]["base"]
            endpoints = get_canonical_endpoints("oklink", base)
            chain_lower = str(chain).lower()
            if chain_lower == "eth": chain_lower = "ethereum"
            return endpoints["wallet"].format(chain_lower=chain_lower, address=address)
            
        config, _ = self._find_chain_config(chain)
        if not config:
            return f"https://etherscan.io/address/{address}" # default fallback
            
        endpoints = get_canonical_endpoints(config["type"], config["base"])
        return endpoints["wallet"].format(address=address)

    def get_transaction_url(self, chain: str, txhash: str) -> str:
        config, _ = self._find_chain_config(chain)
        if not config:
            return f"https://etherscan.io/tx/{txhash}"
        endpoints = get_canonical_endpoints(config["type"], config["base"])
        return endpoints["tx"].format(txhash=txhash)

    def classify_wallet(self, chain: str, address: str, metadata: dict) -> str:
        """
        Classifies a wallet against the WALLET_CLASSIFICATION_ONTOLOGY 
        using combined signals from the Auto-Resolver Intelligence Pipeline.
        """
        combined_text = " ".join([str(v).lower() for v in metadata.values() if v])
        
        if "binance" in combined_text and "hot" in combined_text: return "Exchange Hot Wallet"
        if "binance" in combined_text or "coinbase" in combined_text or "kraken" in combined_text: return "Exchange"
        if "mixer" in combined_text or "tornado" in combined_text: return "Mixer"
        if "hack" in combined_text or "exploit" in combined_text or "stolen" in combined_text: return "Exploiter"
        if "scam" in combined_text or "phish" in combined_text: return "Scam"
        if "dex" in combined_text or "swap" in combined_text or "router" in combined_text: return "Router"
        if "bridge" in combined_text: return "Bridge"
        if "mev" in combined_text or "bot" in combined_text: return "MEV Bot"
        
        # Default mapping
        if metadata.get("is_contract"): return "Smart Contract"
        
        return "Unknown"
