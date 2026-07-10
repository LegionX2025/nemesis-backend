from typing import List, Dict, Any

class CrossChainEngine:
    """
    Connects Lock/Burn events on Chain A to Mint/Release events on Chain B
    using time + amount heuristics for bridges like Stargate, LayerZero.
    """
    def __init__(self):
        self.known_bridges = {
            "0x12312312": "Stargate Router",
            "0x32132132": "LayerZero Endpoint"
        }

    def correlate_cross_chain(self, locks: List[Dict], mints: List[Dict], max_time_delta_sec: int = 1800) -> List[Dict]:
        """
        Attempts to match a lock/burn on chain A with a mint/release on chain B.
        """
        correlated_edges = []
        for lock in locks:
            lock_amt = lock.get("amount", 0)
            lock_time = lock.get("timestamp", 0)
            
            best_match = None
            smallest_delta = float('inf')
            
            for mint in mints:
                mint_amt = mint.get("amount", 0)
                mint_time = mint.get("timestamp", 0)
                
                # Check time (mint must happen AFTER lock, but within delta)
                time_diff = mint_time - lock_time
                if 0 < time_diff <= max_time_delta_sec:
                    # Check amount (allowing for 1% slippage/bridge fee)
                    if 0.99 <= (mint_amt / lock_amt) <= 1.01:
                        if time_diff < smallest_delta:
                            smallest_delta = time_diff
                            best_match = mint
                            
            if best_match:
                correlated_edges.append({
                    "source_chain": lock.get("chain"),
                    "target_chain": best_match.get("chain"),
                    "source_tx": lock.get("tx_hash"),
                    "target_tx": best_match.get("tx_hash"),
                    "confidence": 0.95 - (smallest_delta / max_time_delta_sec) * 0.2
                })
                
        return correlated_edges
