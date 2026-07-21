# nemesis/intelligence/behavior.py

from typing import List, Dict, Any
from pydantic import BaseModel, Field
import numpy as np
from scipy.spatial.distance import cosine
from nemesis.observability.telemetry import logger, tracer

class WalletDNA(BaseModel):
    wallet_address: str
    preferred_chains: List[str] = Field(default_factory=list)
    active_hours_utc: List[int] = Field(default_factory=list)
    mean_gas_price: float = 0.0
    median_priority_fee: float = 0.0
    bridge_preference: Dict[str, float] = Field(default_factory=dict)
    dex_preference: Dict[str, float] = Field(default_factory=dict)
    stablecoin_usage_ratio: float = 0.0
    velocity_tx_per_day: float = 0.0
    typical_amount_usd: float = 0.0

class BehaviorEngine:
    @tracer.start_as_current_span("behavior.extract_dna")
    def extract_dna(self, tx_history: List[Dict[str, Any]], address: str) -> WalletDNA:
        """
        Calculates the behavioral fingerprint of a wallet based on its transaction history.
        """
        dna = WalletDNA(wallet_address=address)
        if not tx_history:
            return dna

        gas_prices = []
        amounts = []
        for tx in tx_history:
            if "gasPrice" in tx:
                try:
                    gas_prices.append(float(tx["gasPrice"]))
                except ValueError:
                    pass
            if "value" in tx:
                try:
                    amounts.append(float(tx["value"]))
                except ValueError:
                    pass

        if gas_prices:
            dna.mean_gas_price = float(np.mean(gas_prices))
        if amounts:
            dna.typical_amount_usd = float(np.median(amounts))

        timestamps = []
        bridge_interactions = 0
        dex_interactions = 0
        for tx in tx_history:
            ts = tx.get("timeStamp") or tx.get("timestamp")
            if ts:
                try:
                    timestamps.append(int(ts))
                except ValueError:
                    pass
            
            # Simple heuristic for DEX / Bridge preference
            input_data = tx.get("input", "").lower()
            if "swap" in input_data or "0x38ed1739" in input_data: # swapExactTokensForTokens
                dex_interactions += 1
            if "bridge" in input_data or tx.get("to", "").lower() in ["0x3ee18b2214aff97000d974cf647e7c347e8fa585"]: # wormhole
                bridge_interactions += 1

        if timestamps:
            from datetime import datetime
            hours = [datetime.utcfromtimestamp(ts).hour for ts in timestamps]
            dna.active_hours_utc = list(set(hours))

        if timestamps and len(timestamps) > 1:
            min_ts = min(timestamps)
            max_ts = max(timestamps)
            days = max(1.0, (max_ts - min_ts) / 86400.0)
            dna.velocity_tx_per_day = len(tx_history) / days
        else:
            dna.velocity_tx_per_day = len(tx_history) / 30.0 # Default if timestamps unavailable
            
        total_txs = len(tx_history) or 1
        dna.dex_preference = {"generic_dex": dex_interactions / total_txs}
        dna.bridge_preference = {"generic_bridge": bridge_interactions / total_txs}
        
        logger.info(f"Extracted DNA for {address}: Velocity={dna.velocity_tx_per_day}, TypicalAmt={dna.typical_amount_usd}")
        return dna

    @tracer.start_as_current_span("behavior.compute_similarity")
    def compute_similarity(self, dna1: WalletDNA, dna2: WalletDNA) -> float:
        """
        Computes Cosine Similarity between two WalletDNAs.
        """
        # Vectorize DNA
        v1 = np.array([dna1.mean_gas_price, dna1.velocity_tx_per_day, dna1.typical_amount_usd, dna1.stablecoin_usage_ratio])
        v2 = np.array([dna2.mean_gas_price, dna2.velocity_tx_per_day, dna2.typical_amount_usd, dna2.stablecoin_usage_ratio])
        
        # Avoid division by zero
        if np.linalg.norm(v1) == 0 or np.linalg.norm(v2) == 0:
            return 0.0
            
        similarity = 1 - cosine(v1, v2)
        return float(similarity)

behavior_engine = BehaviorEngine()
