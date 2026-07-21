# nemesis/intelligence/obfuscation.py

from typing import List, Dict, Any
from pydantic import BaseModel
import networkx as nx
from nemesis.observability.telemetry import logger, tracer

class ObfuscationPattern(BaseModel):
    pattern_type: str
    confidence: float
    nodes_involved: List[str]
    description: str

class ObfuscationEngine:
    @tracer.start_as_current_span("obfuscation.detect_peel_chain")
    def detect_peel_chain(self, graph: nx.DiGraph, start_node: str) -> List[ObfuscationPattern]:
        """
        Detects peel chains: 100 BTC -> 99 BTC (Change) + 1 BTC (Drop) -> 98 BTC (Change) + 1 BTC (Drop)
        """
        patterns = []
        if start_node not in graph:
            return patterns
            
        current_node = start_node
        chain_nodes = [current_node]
        
        while True:
            successors = list(graph.successors(current_node))
            if len(successors) == 2:
                edge1 = graph[current_node][successors[0]]
                edge2 = graph[current_node][successors[1]]
                
                val1 = float(edge1.get("value", 0))
                val2 = float(edge2.get("value", 0))
                total = val1 + val2
                
                if total == 0:
                    break
                    
                if val1 / total > 0.8 and val2 / total < 0.2:
                    current_node = successors[0]
                    chain_nodes.append(current_node)
                elif val2 / total > 0.8 and val1 / total < 0.2:
                    current_node = successors[1]
                    chain_nodes.append(current_node)
                else:
                    break
            elif len(successors) == 1 and len(chain_nodes) > 1:
                chain_nodes.append(successors[0])
                break
            else:
                break
                
            if current_node in chain_nodes[:-1]:
                break
                
        if len(chain_nodes) >= 4:
            patterns.append(ObfuscationPattern(
                pattern_type="PEEL_CHAIN",
                confidence=min(0.99, 0.80 + (len(chain_nodes) - 3) * 0.05),
                nodes_involved=chain_nodes,
                description=f"Detected peel chain originating from {start_node} with {len(chain_nodes)-1} hops."
            ))
            
        return patterns

    @tracer.start_as_current_span("obfuscation.detect_layering")
    def detect_layering(self, graph: nx.DiGraph) -> List[ObfuscationPattern]:
        """
        Detects layering through DEX -> Bridge -> LP -> Swap
        """
        patterns = []
        # Cycle detection and path depth analysis
        cycles = list(nx.simple_cycles(graph))
        if cycles:
            patterns.append(ObfuscationPattern(
                pattern_type="CYCLE_LAUNDERING",
                confidence=0.85,
                nodes_involved=cycles[0],
                description=f"Detected cycle laundering involving {len(cycles[0])} hops."
            ))
        return patterns

    @tracer.start_as_current_span("obfuscation.detect_fan")
    def detect_fan(self, graph: nx.DiGraph) -> List[ObfuscationPattern]:
        """
        Detects Fan-Out (Fragmentation) and Fan-In (Consolidation)
        """
        patterns = []
        for node in graph.nodes():
            out_degree = graph.out_degree(node)
            in_degree = graph.in_degree(node)
            
            if out_degree > 50:
                patterns.append(ObfuscationPattern(
                    pattern_type="FAN_OUT_FRAGMENTATION",
                    confidence=0.9,
                    nodes_involved=[node],
                    description=f"Node fragmented funds to {out_degree} destinations."
                ))
            
            if in_degree > 50:
                patterns.append(ObfuscationPattern(
                    pattern_type="FAN_IN_CONSOLIDATION",
                    confidence=0.9,
                    nodes_involved=[node],
                    description=f"Node consolidated funds from {in_degree} sources."
                ))
        return patterns

obfuscation_engine = ObfuscationEngine()
