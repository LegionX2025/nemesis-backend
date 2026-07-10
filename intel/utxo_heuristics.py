import logging

logger = logging.getLogger("NEMESIS.v32.UTXOHeuristics")

class UTXOHeuristics:
    def __init__(self):
        self.dust_threshold = 546 # Satoshis

    def detect_peel_chains(self, outputs: list) -> bool:
        """
        Detects if a transaction output splits into a large primary amount
        and a slightly smaller amount sent to a new address (peel pattern).
        """
        if len(outputs) == 2:
            vals = [o["value"] for o in outputs]
            if max(vals) > min(vals) * 10:
                logger.info("Peel chain signature detected: Large value preservation.")
                return True
        return False

    def detect_coinjoin(self, outputs: list) -> bool:
        """
        Detects mixing behaviour where multiple outputs share the exact same denomination.
        """
        if len(outputs) < 3: return False
        
        vals = [o["value"] for o in outputs]
        # If the most common value occurs multiple times, it's a mix
        from collections import Counter
        counts = Counter(vals)
        most_common = counts.most_common(1)[0]
        if most_common[1] >= len(outputs) * 0.8:
            logger.info(f"CoinJoin signature detected: Denomination {most_common[0]}")
            return True
        return False
