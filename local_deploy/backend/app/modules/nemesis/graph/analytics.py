# nemesis/graph/analytics.py

import networkx as nx
from typing import Dict, Any, List, Set
from nemesis.observability.telemetry import logger, tracer

class GraphAnalytics:
    @tracer.start_as_current_span("graph.pagerank")
    def compute_pagerank(self, graph: nx.DiGraph) -> Dict[str, float]:
        """
        Computes PageRank to identify the most central entities in the trace graph.
        """
        try:
            return nx.pagerank(graph, weight='value')
        except Exception as e:
            logger.error(f"PageRank computation failed: {e}")
            return {}

    @tracer.start_as_current_span("graph.betweenness")
    def compute_betweenness(self, graph: nx.DiGraph) -> Dict[str, float]:
        """
        Identifies critical bottlenecks (e.g., mixers, cross-chain bridges) using Betweenness Centrality.
        """
        try:
            # Betweenness centrality based on the shortest paths
            return nx.betweenness_centrality(graph, weight=None)
        except Exception as e:
            logger.error(f"Betweenness computation failed: {e}")
            return {}

    @tracer.start_as_current_span("graph.communities")
    def detect_communities(self, graph: nx.DiGraph) -> List[Set[str]]:
        """
        Uses greedy modularity maximization (similar to Louvain for directed graphs) 
        to find isolated clusters of activity.
        """
        try:
            # NetworkX requires undirected for standard Louvain, fallback to greedy
            undirected = graph.to_undirected()
            communities = nx.algorithms.community.greedy_modularity_communities(undirected)
            return [set(c) for c in communities]
        except Exception as e:
            logger.error(f"Community detection failed: {e}")
            return []

graph_analytics = GraphAnalytics()
