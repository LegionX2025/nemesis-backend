from typing import List, Dict

class GraphCompressionEngine:
    """
    Compresses linear semantic hops into summarized edges to reduce graph noise
    while preserving intent.
    """
    def __init__(self):
        pass

    def compress_graph(self, edges: List[Dict]) -> List[Dict]:
        """
        Merges sequences of A -> B -> C into A -> [B] -> C if B is a pass-through node.
        """
        if not edges:
            return []
            
        compressed = []
        skip_indices = set()
        
        for i in range(len(edges) - 1):
            if i in skip_indices: continue
            
            curr_edge = edges[i]
            next_edge = edges[i+1]
            
            # If curr_edge.target == next_edge.source and amounts are similar
            if curr_edge.get("target") == next_edge.get("source"):
                curr_amt = curr_edge.get("amount", 0)
                next_amt = next_edge.get("amount", 0)
                
                if curr_amt > 0 and 0.95 <= (next_amt / curr_amt) <= 1.05:
                    # It's a pass-through. Merge them.
                    merged_edge = {
                        "source": curr_edge.get("source"),
                        "target": next_edge.get("target"),
                        "amount": next_amt,
                        "chain": curr_edge.get("chain"),
                        "typeStr": "COMPRESSED_HOP",
                        "intermediate_nodes": [curr_edge.get("target")],
                        "tx_hashes": [curr_edge.get("tx_hash"), next_edge.get("tx_hash")]
                    }
                    compressed.append(merged_edge)
                    skip_indices.add(i+1)
                    continue
                    
            compressed.append(curr_edge)
            
        if len(edges) - 1 not in skip_indices and edges:
            compressed.append(edges[-1])
            
        return compressed
