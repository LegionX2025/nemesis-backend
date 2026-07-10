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

def generate_deep_dom_label(chain: str, dom_data: dict) -> str:
    """
    Generates a highly specific intelligence label based on deep DOM 
    scraping features (ENS, Contracts, Assets, ERC-20s, EIP-7702).
    """
    if not dom_data or "error" in dom_data:
        return ""
        
    labels = []
    
    # 1. ENS / Name tags are top priority
    if "ens" in dom_data and dom_data["ens"]:
        labels.append(f"ENS: {dom_data['ens']}")
        
    # 2. Check for EIP-7702 Authorizations (indicates smart account / delegator)
    if dom_data.get("eip7702_authorizations") and len(dom_data["eip7702_authorizations"]) > 0:
        labels.append("EIP-7702 Delegator")
        
    # 3. Contract / Creator logic
    if dom_data.get("is_contract"):
        labels.append("Smart Contract")
        
    # 4. Heavy ERC-20 Activity might indicate a DEX router or MEV Bot
    erc20s = dom_data.get("erc20_transfers", [])
    if len(erc20s) > 50:
        labels.append("High-Frequency ERC-20 Trader / Bot")
        
    # 5. Fallback to Asset heavy
    assets = dom_data.get("assets", [])
    if len(assets) > 10:
        labels.append("Multi-Asset Portfolio")
        
    if not labels:
        return ""
        
    # Combine the strongest signals
    base_chain = chain.title() if chain else "Cross-Chain"
    return f"{base_chain} " + " | ".join(labels)
