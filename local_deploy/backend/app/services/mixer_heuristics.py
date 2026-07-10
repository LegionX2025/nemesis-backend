import logging
from datetime import datetime, timedelta

logger = logging.getLogger("MixerHeuristics")

class MixerCorrelationEngine:
    def __init__(self, db_instance):
        self.db = db_instance
        self.edges_col = self.db.get_mongo_collection("state_edges")
        
        # Common denominations in mixers (e.g., Tornado Cash uses 0.1, 1, 10, 100 ETH)
        self.standard_denominations = [0.1, 1.0, 10.0, 100.0]
        self.fee_tolerance = 0.05 # 5% tolerance for relayer fees

    async def find_mixer_correlations(self, mixer_address: str, deposit_amount: float, deposit_time: datetime, chain: str):
        """
        Heuristic search to find probabilistic withdrawals from a mixer.
        Looks for withdrawals within +24 to +72 hours matching the deposit amount denomination.
        """
        probabilistic_edges = []
        
        # Time window: Look for withdrawals from the mixer up to 72 hours AFTER the deposit
        start_time = deposit_time
        end_time = deposit_time + timedelta(hours=72)
        
        # Match denomination (e.g., if deposit is 10.02, it's likely a 10.0 pool)
        matched_pool = None
        for denom in self.standard_denominations:
            if abs(deposit_amount - denom) / denom <= self.fee_tolerance:
                matched_pool = denom
                break
                
        if not matched_pool:
            logger.info(f"Deposit amount {deposit_amount} does not match standard mixer pools. Skipping heuristic.")
            return probabilistic_edges
            
        logger.info(f"Searching for heuristic mixer outputs for pool {matched_pool} {chain}")
            
        # Find all outgoing transfers from the mixer within the time window
        query = {
            "from": mixer_address,
            "chain": chain,
            "timestamp": {"$gte": start_time, "$lte": end_time}
        }
        
        # In a real production system, this queries the graph database or explorer APIs.
        # Since we're fetching dynamically, if the DB lacks this data, we would invoke api_rotator here
        # to fetch recent withdrawals from the mixer smart contract.
        
        cursor = self.edges_col.find(query)
        for doc in cursor:
            out_amount = float(doc.get("amount", 0))
            # Match withdrawal amount against the pool (accounting for relayer fees)
            if abs(out_amount - matched_pool) / matched_pool <= self.fee_tolerance:
                
                # Calculate confidence score based on time proximity (closer = higher confidence)
                time_diff = (doc["timestamp"] - deposit_time).total_seconds() / 3600 # hours
                confidence = max(0.1, 0.85 - (time_diff * 0.01)) # Decays over time
                
                probabilistic_edges.append({
                    "_id": f"heuristic_{doc['tx_hash']}",
                    "from": mixer_address,
                    "to": doc["to"],
                    "edge_type": "PROBABILISTIC_MIXER_HOP",
                    "tx_hash": doc["tx_hash"],
                    "chain": chain,
                    "asset": doc.get("asset", "ETH"),
                    "amount": str(out_amount),
                    "timestamp": doc["timestamp"],
                    "confidence": round(confidence, 2)
                })
                
        return probabilistic_edges
