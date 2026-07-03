import logging

logger = logging.getLogger("OmniChainEngine.Inference")

class IntentInferenceEngine:
    def __init__(self):
        self.rules = {
            "mixer_deposit": ["tornado", "mixer", "blender", "coinjoin"],
            "cex_deposit": ["exchange", "binance", "kraken", "coinbase", "huobi", "okx", "bybit", "hot wallet"],
            "bridge": ["bridge", "multichain", "across", "stargate", "wormhole"],
            "swap": ["router", "swap", "dex", "uniswap", "sushiswap", "pancakeswap", "1inch"]
        }

    def infer_intent(self, from_entity: str, to_entity: str, function_signature: str, value: float):
        to_lower = to_entity.lower()
        
        # 1. Check entity tags based on keywords
        for intent, keywords in self.rules.items():
            if any(k in to_lower for k in keywords):
                if intent == "mixer_deposit":
                    return "LAUNDERING_PATH", "High risk obfuscation detected."
                if intent == "cex_deposit":
                    return "CEX_DEPOSIT", "Funds consolidated at Centralized Exchange."
                if intent == "bridge":
                    return "CROSS_CHAIN_BRIDGE", "Funds bridged to another network."
                if intent == "swap":
                    return "DEX_SWAP", "Funds swapped for another asset."

        # 2. Check function signature heuristics
        if function_signature:
            if "swap" in function_signature.lower():
                return "DEX_SWAP", "Contract execution indicates token swap."
            if "transfer" in function_signature.lower():
                return "TRANSFER", "Standard token transfer."
        
        # 3. Value-based heuristics
        if value > 100000: # large arbitrary threshold for demonstration
            return "WHALE_MOVEMENT", "Large value transfer detected."

        return "PEEL_CHAIN", "Standard transaction, possible peel chain hop."
