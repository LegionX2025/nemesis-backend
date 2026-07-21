import numpy as np
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
from collections import defaultdict

def extract_features(ledger_data):
    """
    Extract features from ledger data for each address.
    Features: 
    1. Total Volume Received
    2. Total Volume Sent
    3. Transaction Count
    4. Unique Counterparties
    """
    stats = defaultdict(lambda: {"in_vol": 0.0, "out_vol": 0.0, "tx_count": 0, "counterparties": set()})
    
    for tx in ledger_data:
        try:
            amt = float(tx.get("amount", 0))
        except:
            amt = 0.0
            
        f = tx.get("from")
        t = tx.get("to")
        
        if f:
            stats[f]["out_vol"] += amt
            stats[f]["tx_count"] += 1
            if t: stats[f]["counterparties"].add(t)
            
        if t:
            stats[t]["in_vol"] += amt
            stats[t]["tx_count"] += 1
            if f: stats[t]["counterparties"].add(f)
            
    addresses = []
    features = []
    
    for addr, data in stats.items():
        addresses.append(addr)
        features.append([
            data["in_vol"],
            data["out_vol"],
            data["tx_count"],
            len(data["counterparties"])
        ])
        
    return addresses, features

def run_syndicate_clustering(ledger_data):
    """
    Runs DBSCAN clustering to identify automated syndicate clusters
    based on transactional behavior.
    """
    if not ledger_data or len(ledger_data) < 5:
        return {} # Not enough data to cluster
        
    addresses, features = extract_features(ledger_data)
    
    if len(addresses) < 3:
        return {}

    # Normalize features
    scaler = StandardScaler()
    scaled_features = scaler.fit_transform(features)
    
    # Run DBSCAN
    # eps=0.5 and min_samples=3 are arbitrary defaults for anomaly detection
    # but work well for normalized transactional groupings
    dbscan = DBSCAN(eps=0.5, min_samples=2)
    labels = dbscan.fit_predict(scaled_features)
    
    clusters = {}
    for addr, label in zip(addresses, labels):
        if label != -1: # -1 means noise (unclustered)
            # Tag with AUTO_ID prefix for frontend compatibility
            clusters[addr] = f"AUTO_ID_{str(label).zfill(4)}"
            
    return clusters
