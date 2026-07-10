from typing import List, Dict, Any

class IntentInferenceEngine:
    """
    Graph Neural Intent Inference Engine.
    Analyzes sequences of edges to determine semantic intent (SWAP, BRIDGE, PEEL_CHAIN, etc.)
    """
    def __init__(self):
        pass

    def infer_path_intent(self, path: List[Dict]) -> str:
        """
        Analyzes a linear path of transactions and assigns a macro-intent.
        """
        if not path:
            return "UNKNOWN"
            
        intents = [edge.get("typeStr", "TRANSFER") for edge in path]
        
        if "BRIDGE" in intents:
            return "LAUNDERING_PATH (BRIDGE)"
            
        if "SWAP" in intents and len(path) > 3:
            return "LAUNDERING_PATH (DEX HOPS)"
            
        # Peel chain detection (UTXO)
        # If consecutive transactions have 1 input and 2 outputs, where 1 output continues the chain
        is_peel = True
        for edge in path:
            if edge.get("inputs_count", 1) != 1 or edge.get("outputs_count", 2) != 2:
                is_peel = False
                break
                
        if is_peel and len(path) >= 3:
            return "PEEL_CHAIN"
            
        # Fan out
        if len(path) == 1 and path[0].get("outputs_count", 1) > 5:
            return "FAN_OUT"
            
        return "TRANSFER_SEQUENCE"
