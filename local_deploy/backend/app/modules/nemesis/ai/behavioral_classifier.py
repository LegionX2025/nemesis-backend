import numpy as np
from typing import Dict, Any, List
import networkx as nx
from sklearn.cluster import DBSCAN
from nemesis.observability.telemetry import logger, tracer
from nemesis.core.config import settings

class BehavioralClassifier:
    """
    Scikit-Learn based behavioral classifier for Wallet Scoring and Laundering Pattern Detection.
    Implements DBSCAN Outlier Detection on transaction velocity and subgraph density calculation.
    """
    def __init__(self):
        # We configure DBSCAN for anomaly detection
        # eps: max distance between two samples for one to be considered as in the neighborhood
        # min_samples: The number of samples in a neighborhood for a point to be considered a core point
        self.dbscan = DBSCAN(eps=0.5, min_samples=3)

    @tracer.start_as_current_span("ai.vectorize_timestamps")
    def _vectorize_timestamps(self, graph: nx.DiGraph, node_id: str) -> np.ndarray:
        """
        Extracts and vectorizes timestamps of edges involving the node to analyze velocity.
        """
        timestamps = []
        for u, v, data in graph.edges(data=True):
            if u == node_id or v == node_id:
                ts = data.get("timestamp", 0)
                try:
                    timestamps.append(float(ts))
                except ValueError:
                    continue
        
        if len(timestamps) < 2:
            return np.array([])
            
        # Calculate time deltas (velocity) between consecutive transactions
        timestamps.sort()
        deltas = np.diff(timestamps)
        return deltas.reshape(-1, 1)

    @tracer.start_as_current_span("ai.calculate_density")
    def _calculate_subgraph_density(self, graph: nx.DiGraph, node_id: str) -> float:
        """
        Calculates the density of the peer-to-peer subgraph around a specific node.
        High density often indicates peeling chains or sybil-like laundering rings.
        """
        # Get ego graph (node and its immediate neighbors)
        ego = nx.ego_graph(graph, node_id, radius=1)
        if len(ego) <= 1:
            return 0.0
            
        return nx.density(ego)

    @tracer.start_as_current_span("ai.analyze_node")
    def analyze_node_behavior(self, graph: nx.DiGraph, node_id: str) -> Dict[str, Any]:
        """
        Runs the full behavioral scoring pipeline on a single node.
        """
        logger.info(f"Analyzing behavior for {node_id}")
        
        # 1. Vectorize Wallet Timestamps & Calculate Velocity
        velocity_vector = self._vectorize_timestamps(graph, node_id)
        
        # 2. Calculate Peer-to-Peer Subgraph Density
        density = self._calculate_subgraph_density(graph, node_id)
        
        # 3. DBSCAN Outlier Detection on Velocity
        is_anomalous_velocity = False
        anomaly_score = 0.0
        
        if len(velocity_vector) >= 3:
            labels = self.dbscan.fit_predict(velocity_vector)
            # -1 indicates noise/outliers in DBSCAN
            outlier_ratio = np.sum(labels == -1) / len(labels)
            if outlier_ratio > 0.3:  # If more than 30% of tx velocities are anomalous
                is_anomalous_velocity = True
            anomaly_score = outlier_ratio
            
        # Classify the pattern
        typology = "UNKNOWN"
        risk_level = "LOW"
        
        # Basic heuristic mapping combining ML features
        if density > 0.8 and anomaly_score > 0.5:
            typology = "MIXER_OR_SYBIL_RING"
            risk_level = "CRITICAL"
        elif anomaly_score > 0.5:
            typology = "HIGH_FREQUENCY_PROGRAMMATIC"
            risk_level = "HIGH"
        elif density > 0.8:
            typology = "CONSOLIDATION_NODE"
            risk_level = "MEDIUM"
            
        return {
            "node_id": node_id,
            "density": float(density),
            "anomaly_score": float(anomaly_score),
            "is_anomalous_velocity": bool(is_anomalous_velocity),
            "predicted_typology": typology,
            "risk_level": risk_level
        }

    @tracer.start_as_current_span("ai.batch_analyze")
    def analyze_graph(self, graph: nx.DiGraph) -> Dict[str, Dict[str, Any]]:
        """
        Analyzes all nodes in the graph to classify laundering patterns.
        """
        results = {}
        for node in graph.nodes():
            results[node] = self.analyze_node_behavior(graph, node)
        return results

behavioral_classifier = BehavioralClassifier()
