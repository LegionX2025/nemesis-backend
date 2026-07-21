import logging
from typing import List, Dict, Any
# Note: scikit-learn must be installed manually using `pip install scikit-learn`
try:
    from sklearn.cluster import DBSCAN
    from sklearn.preprocessing import StandardScaler
    import numpy as np
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False

logger = logging.getLogger("NemesisML")

class MLEngine:
    def __init__(self):
        self.scaler = StandardScaler() if ML_AVAILABLE else None
        self.cluster_model = DBSCAN(eps=0.3, min_samples=2) if ML_AVAILABLE else None

    def cluster_wallets(self, wallet_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Groups wallets based on transaction frequency, volume, and interaction overlaps.
        wallet_data expects list of dicts: {"address": str, "tx_count": int, "vol_usd": float, "overlap_score": float}
        """
        if not ML_AVAILABLE:
            logger.warning("scikit-learn is not installed. Returning unclustered wallets.")
            return wallet_data
        
        if not wallet_data:
            return []

        # Extract features for clustering
        features = [[w.get("tx_count", 0), w.get("vol_usd", 0.0), w.get("overlap_score", 0.0)] for w in wallet_data]
        X = np.array(features)
        
        # Standardize features
        X_scaled = self.scaler.fit_transform(X)
        
        # Perform Density-Based Clustering
        labels = self.cluster_model.fit_predict(X_scaled)
        
        # Map labels back to wallets
        for i, wallet in enumerate(wallet_data):
            wallet["ml_cluster_id"] = f"c_{labels[i]}" if labels[i] != -1 else "outlier"
            
        logger.info(f"Successfully clustered {len(wallet_data)} wallets.")
        return wallet_data

    def calculate_osint_correlation_score(self, on_chain_profile: Dict, osint_record: Dict) -> float:
        """
        Heuristic scoring engine to correlate Darknet/OSINT data with on-chain profiles.
        Returns a confidence score between 0.0 and 1.0.
        """
        score = 0.0
        
        # Exact address match is a massive signal
        on_chain_address = on_chain_profile.get("address", "").lower()
        if on_chain_address and on_chain_address in [w.lower() for w in osint_record.get("extracted_wallets", [])]:
            score += 0.8
            
        first_seen = on_chain_profile.get("first_seen")
        scraped_at = osint_record.get("scraped_at")
        if first_seen and scraped_at:
            try:
                import datetime
                if isinstance(first_seen, str) and first_seen.isdigit():
                    first_seen = int(first_seen)
                if isinstance(first_seen, (int, float)):
                    first_dt = datetime.datetime.fromtimestamp(first_seen, datetime.timezone.utc)
                else:
                    first_dt = datetime.datetime.fromisoformat(str(first_seen).replace("Z", "+00:00"))
                    
                if isinstance(scraped_at, (int, float)):
                    scraped_dt = datetime.datetime.fromtimestamp(scraped_at, datetime.timezone.utc)
                else:
                    scraped_dt = datetime.datetime.fromisoformat(str(scraped_at).replace("Z", "+00:00"))
                
                # If within 30 days
                if abs((first_dt - scraped_dt).days) <= 30:
                    score += 0.1
            except Exception:
                pass
            
        return min(score, 1.0)

ml_engine = MLEngine()
