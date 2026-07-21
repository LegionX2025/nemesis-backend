# NEMESIS Forensic Signature Engine
# Module: Protocols, Black Holes, Exploits, CEX Deposits, IOCs

ENTITY_TYPES = {
    "wallet",
    "contract",
    "token",
    "bridge",
    "mixer",
    "dex_router",
    "cex",
    "nft"
}

DEX_BLACKHOLES = {
    "uniswap": ["swaprouter", "uniswap"],
    "pancakeswap": ["pancake", "router"],
    "curve": ["curve", "pool"],
    "aave": ["aave", "lendingpool"],
    "1inch": ["1inch", "aggregationrouter"]
}

BLACK_HOLE_TYPES = {
    "dex_router",
    "mixer",
    "bridge",
    "lp_vault"
}

# Add commonly known CEX wallets (this would ideally be populated from DB/OSINT)
KNOWN_CEX_WALLETS = {
    "0x28C6c06298d514Db089934071355E22Af164fC50", # Binance 14
    "0x503828976D22510aad0201ac7EC88293211D23Da", # Coinbase
    "0x28c6c06298d514db089934071355e22af164fc50"  # Lowercase Binance
}

def detect_blackholes(path):
    alerts = []
    for step in path:
        entity_type = step.get("entity_type")
        if entity_type in BLACK_HOLE_TYPES:
            alerts.append({
                "type": "VISIBILITY_DEGRADATION",
                "entity": step.get("to"),
                "event": step.get("event"),
                "confidence": 90
            })
    return alerts

def detect_bridge_exploit(path):
    exploits = []
    for i in range(len(path)-1):
        a = path[i]
        b = path[i+1]
        
        # lock/burn -> mint cross chain logic
        if a.get("event") == "bridge" and b.get("event") == "mint":
            if a.get("token_in") != b.get("token_out"):
                exploits.append({
                    "type": "BRIDGE_EXPLOIT",
                    "confidence": 88
                })
    return exploits

def detect_cex_deposits(txs):
    deposits = []
    for tx in txs:
        if tx.get("to", "").lower() in [addr.lower() for addr in KNOWN_CEX_WALLETS] or tx.get("entity_type") == "cex":
            deposits.append(tx)
    return deposits

def extract_iocs(txs):
    iocs = []
    for tx in txs:
        iocs.append({
            "hash": tx.get("hash", tx.get("tx_hash", "")),
            "from": tx.get("from"),
            "to": tx.get("to"),
            "selector": (tx.get("input") or "")[:10]
        })
    return iocs

def detect_sandwich(flat_txs):
    """
    Heuristic detection of sandwich attacks (Front-run, Victim, Back-run).
    Assumes flat_txs is a list of transactions ordered by time.
    """
    sandwiches = []
    # Sort by time to ensure order
    sorted_txs = sorted(flat_txs, key=lambda x: int(x.get("timeStamp", 0)) if str(x.get("timeStamp", 0)).isdigit() else 0)
    
    for i in range(len(sorted_txs) - 2):
        tx1 = sorted_txs[i]
        tx2 = sorted_txs[i+1]
        tx3 = sorted_txs[i+2]
        
        attacker = tx1.get("from", "").lower()
        victim = tx2.get("from", "").lower()
        attacker2 = tx3.get("from", "").lower()
        
        if attacker and attacker != "unknown" and attacker == attacker2 and attacker != victim:
            time1 = int(tx1.get("timeStamp", 0)) if str(tx1.get("timeStamp", 0)).isdigit() else 0
            time3 = int(tx3.get("timeStamp", 0)) if str(tx3.get("timeStamp", 0)).isdigit() else 0
            
            if abs(time3 - time1) <= 15: # Usually same block = same timestamp or very close
                sandwiches.append({
                    "type": "SANDWICH_ATTACK_PATTERN",
                    "attacker": attacker,
                    "victim": victim,
                    "front_run_hash": tx1.get("hash"),
                    "victim_hash": tx2.get("hash"),
                    "back_run_hash": tx3.get("hash"),
                    "confidence": 75
                })
                
    return sandwiches

def flashbots_decode(flat_txs):
    """
    Identify potential private mempool / Flashbots transactions.
    Checks if gasPrice is 0 which is typical for MEV bots paying miners directly via coinbase transfers.
    """
    private_txs = []
    for tx in flat_txs:
        gas_price = str(tx.get("gasPrice", ""))
        if gas_price == "0":
            private_txs.append({
                "type": "PRIVATE_MEMPOOL_TX",
                "hash": tx.get("hash"),
                "from": tx.get("from"),
                "to": tx.get("to"),
                "confidence": 85,
                "reason": "Zero gas price detected (typical of Flashbots/builder API)"
            })
    return private_txs

def track_campaigns(flat_txs):
    """
    Detect automated attack or mass-distribution campaigns.
    Look for highly repetitive actions from the same address.
    """
    campaigns = []
    sender_activity = {}
    
    for tx in flat_txs:
        sender = tx.get("from", "").lower()
        if not sender or sender == "unknown":
            continue
        if sender not in sender_activity:
            sender_activity[sender] = []
        sender_activity[sender].append(tx)
        
    for sender, txs in sender_activity.items():
        if len(txs) > 10:
            inputs = [t.get("input", "") for t in txs if t.get("input", "")]
            if inputs:
                most_common_input = max(set(inputs), key=inputs.count)
                input_ratio = inputs.count(most_common_input) / len(txs)
                
                if input_ratio > 0.8: # 80% identical transactions
                    campaigns.append({
                        "type": "AUTOMATED_CAMPAIGN",
                        "sender": sender,
                        "tx_count": len(txs),
                        "common_selector": most_common_input[:10],
                        "confidence": 90
                    })
    return campaigns

def cluster_attackers(embeddings=None):
    """
    Cluster attacker addresses based on behavioral embeddings.
    """
    if not embeddings or not isinstance(embeddings, dict):
        return []
        
    try:
        from sklearn.cluster import DBSCAN
        import numpy as np
        
        addresses = list(embeddings.keys())
        vectors = list(embeddings.values())
        
        if len(vectors) < 2:
            return []
            
        max_len = max(len(v) if isinstance(v, (list, tuple)) else 1 for v in vectors)
        padded_vectors = []
        for v in vectors:
            if isinstance(v, (list, tuple)):
                padded_vectors.append(list(v) + [0] * (max_len - len(v)))
            else:
                padded_vectors.append([float(v)] + [0] * (max_len - 1))
                
        X = np.array(padded_vectors)
        clustering = DBSCAN(eps=0.5, min_samples=2).fit(X)
        labels = clustering.labels_
        
        clusters = {}
        for addr, label in zip(addresses, labels):
            if label != -1: # -1 is noise
                if label not in clusters:
                    clusters[label] = []
                clusters[label].append(addr)
                
        result = []
        for label, addrs in clusters.items():
            result.append({
                "cluster_id": f"Syndicate-{label}",
                "members": addrs,
                "size": len(addrs)
            })
            
        return result
    except ImportError:
        return [{"error": "sklearn not available for clustering"}]
    except Exception as e:
        return [{"error": str(e)}]
