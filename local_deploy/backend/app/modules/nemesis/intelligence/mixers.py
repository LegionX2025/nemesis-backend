# nemesis/intelligence/mixers.py

from typing import Dict, Any, List
import math
from pydantic import BaseModel
from nemesis.observability.telemetry import logger, tracer

class DemixingScore(BaseModel):
    probability: float
    amount_similarity: float
    timing_similarity: float
    gas_similarity: float
    destination_similarity: float
    bridge_similarity: float

class MixerEngine:
    def __init__(self):
        self.known_mixers = {
            "0xd90e2f925da726b50c4ed8d0fb90ad053324f31b": "Tornado Cash Router",
            "0x12d66f87A04A9E220743712cE6d9bB1B5616B8Fc": "Tornado Cash 0.1 ETH",
            "0x47CE0C6eD5B0Ce3d3A51fcf1C52DC66F7D5357A1": "Tornado Cash 1 ETH",
            "0x910Cbd523D972eb0a6f4cAe44A881DDfcA933f98": "Tornado Cash 10 ETH",
            "0xA160cdAB225685dA1d56aa342d88849c719875a5": "Tornado Cash 100 ETH",
            "0xfaE155700b02131F3b1Bc3Ffb9c4a4fB52bb53C4": "Railgun Proxy",
            "0x42f74136611f7c5f8dfab7e4edfa15e98f06dd1a": "Whirlpool Proxy",
        }

    @tracer.start_as_current_span("mixers.bayesian_demix")
    async def bayesian_demix(self, deposit_tx: Dict[str, Any], candidate_withdrawals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Calculates P(withdraw | deposit) using Bayesian inference across multiple heuristics.
        """
        results = []
        dep_val = float(deposit_tx.get("value", 0))
        dep_time = int(deposit_tx.get("timestamp", 0))

        for w_tx in candidate_withdrawals:
            w_val = float(w_tx.get("value", 0))
            w_time = int(w_tx.get("timestamp", 0))

            # 1. Amount Similarity (Pool denomination matching)
            # Typically 0.1, 1, 10, 100 ETH minus relayer fee
            val_diff = abs(dep_val - w_val)
            amount_sim = max(0, 1.0 - (val_diff / (dep_val + 0.0001)))

            # 2. Timing Similarity (Withdrawal windows)
            # Longer time in mixer = lower confidence, but harder to trace
            time_diff_hours = (w_time - dep_time) / 3600
            if time_diff_hours < 0:
                continue # Withdrawal before deposit is impossible
            timing_sim = math.exp(-0.01 * time_diff_hours)

            # 3. Gas Fingerprinting (Relayer analysis)
            # If the withdrawal uses exactly the same gas price or a strongly correlated relayer priority fee
            dep_gas = float(deposit_tx.get("gasPrice", 0))
            w_gas = float(w_tx.get("gasPrice", 0))
            if dep_gas > 0 and w_gas > 0:
                gas_diff_ratio = abs(dep_gas - w_gas) / max(dep_gas, w_gas)
                gas_sim = max(0.1, 1.0 - (gas_diff_ratio * 5)) # high similarity if gas price is identical
            else:
                gas_sim = 0.5 # Unknown gas correlation

            # Combine probabilities (Naive Bayes assumption)
            prob = amount_sim * timing_sim * gas_sim

            if prob > 0.1:
                results.append({
                    "withdrawal_tx": w_tx,
                    "score": DemixingScore(
                        probability=prob,
                        amount_similarity=amount_sim,
                        timing_similarity=timing_sim,
                        gas_similarity=gas_sim,
                        destination_similarity=0.5,
                        bridge_similarity=0.5
                    ).dict()
                })

        # Sort by highest probability
        results.sort(key=lambda x: x["score"]["probability"], reverse=True)
        return results

mixer_engine = MixerEngine()
