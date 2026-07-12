import logging
from typing import List, Dict, Any

logger = logging.getLogger("UTXOEngine")

class UTXOForensicEngine:
    def __init__(self):
        pass
        
    def analyze_peel_chain(self, tx: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyzes a UTXO transaction to detect peel chain behaviors, change outputs,
        and coinjoin probabilities.
        """
        inputs = tx.get("inputs", [])
        outputs = tx.get("outputs", [])
        
        if not inputs or not outputs:
            return {"pattern": "UNKNOWN"}
            
        total_in = sum(float(i.get("value", 0)) for i in inputs)
        total_out = sum(float(o.get("value", 0)) for o in outputs)
        
        # CoinJoin Detection (Many inputs, many equal outputs)
        if len(inputs) > 3 and len(outputs) > 3:
            out_vals = [o.get("value") for o in outputs]
            if len(set(out_vals)) == 1: # All outputs are identical size
                return {"pattern": "COINJOIN", "anonymity_set": len(outputs)}
                
        # Peel Chain Detection (1 large input -> 1 large change + 1 small target)
        if len(inputs) == 1 and len(outputs) == 2:
            o1, o2 = float(outputs[0].get("value", 0)), float(outputs[1].get("value", 0))
            if max(o1, o2) > (total_in * 0.8): # 80% is change
                change_index = 0 if o1 > o2 else 1
                target_index = 1 if change_index == 0 else 0
                return {
                    "pattern": "PEEL_CHAIN",
                    "change_address": outputs[change_index].get("address"),
                    "target_address": outputs[target_index].get("address")
                }
                
        # Fan-out (1 input -> Many outputs)
        if len(inputs) == 1 and len(outputs) > 5:
            return {"pattern": "FAN_OUT", "target_count": len(outputs)}
            
        return {"pattern": "STANDARD_TRANSFER"}

utxo_engine = UTXOForensicEngine()
