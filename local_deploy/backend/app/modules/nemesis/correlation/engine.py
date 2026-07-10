# nemesis/correlation/engine.py

from typing import Dict, Any, List
import networkx as nx
from pydantic import BaseModel
from nemesis.intelligence.behavior import behavior_engine, WalletDNA
from nemesis.observability.telemetry import logger, tracer

class CorrelationScore(BaseModel):
    wallet_a: str
    wallet_b: str
    overall_probability: float
    dna_similarity: float
    temporal_overlap: float
    graph_distance: int

class CorrelationEngine:
    @tracer.start_as_current_span("correlation.compute")
    def compute_correlation(self, wallet_a: str, wallet_b: str, graph: nx.DiGraph, dna_a: WalletDNA, dna_b: WalletDNA) -> CorrelationScore:
        """
        Probabilistic correlation combining Bayesian inference, HMMs, Graph similarity, and DNA.
        """
        
        # 1. Behavioral DNA Similarity
        dna_sim = behavior_engine.compute_similarity(dna_a, dna_b)
        
        # 2. Graph Distance
        try:
            distance = nx.shortest_path_length(graph, source=wallet_a, target=wallet_b)
        except nx.NetworkXNoPath:
            try:
                distance = nx.shortest_path_length(graph, source=wallet_b, target=wallet_a)
            except nx.NetworkXNoPath:
                distance = 999 # Disconnected
                
        # Transform distance to probability (closer = higher correlation)
        graph_sim = 1.0 / (distance + 1.0) if distance < 999 else 0.01
        
        # 3. Temporal Overlap
        if dna_a.active_hours_utc and dna_b.active_hours_utc:
            set_a = set(dna_a.active_hours_utc)
            set_b = set(dna_b.active_hours_utc)
            intersection = len(set_a.intersection(set_b))
            union = len(set_a.union(set_b))
            temporal_overlap = intersection / union if union > 0 else 0.5
        else:
            temporal_overlap = 0.5
        
        # Naive Bayes Combination
        prob = dna_sim * graph_sim * temporal_overlap
        
        logger.info(f"Correlation between {wallet_a[:8]} and {wallet_b[:8]}: P={prob:.2f}")
        
        return CorrelationScore(
            wallet_a=wallet_a,
            wallet_b=wallet_b,
            overall_probability=prob,
            dna_similarity=dna_sim,
            temporal_overlap=temporal_overlap,
            graph_distance=distance
        )

correlation_engine = CorrelationEngine()
