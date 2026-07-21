# nemesis/tracing/engine.py

import asyncio
import re
from typing import Dict, Any, List, Set, Optional
import networkx as nx
from nemesis.core.config import settings
from nemesis.observability.telemetry import logger, tracer
from nemesis.fetcher.orchestrator import orchestrator

class TracingEngine:
    """
    Recursive Graph Expansion Engine for Asset Tracing.
    Replaces the linear deterministic tracer with a multi-path probabilistic graph builder.
    """
    def __init__(self):
        self.graph = nx.DiGraph()
        self.visited: Set[str] = set()
        
    def _identify_network(self, address: str) -> str:
        regexes = {
            "BITCOIN": r"\b(?:bc1[a-z0-9]{25,39}|[13][a-km-zA-HJ-NP-Z1-9]{25,34})\b",
            "ETHEREUM": r"\b0x[a-fA-F0-9]{40}\b",
            "SOLANA": r"\b[1-9A-HJ-NP-Za-km-z]{32,44}\b",
            "RIPPLE": r"\br[1-9A-HJ-NP-Za-km-z]{24,34}\b",
            "TRON": r"\bT[1-9A-HJ-NP-Za-km-z]{33}\b",
            "LITECOIN": r"\b(?:ltc1[a-z0-9]{25,65}|[LM3][a-km-zA-HJ-NP-Z1-9]{26,33})\b",
            "BITCOIN_CASH": r"\b(?:bitcoincash:)?(?:q|p)[a-z0-9]{41}\b",
            "STELLAR": r"\bG[A-Z2-7]{55}\b",
            "MULTIVERSX": r"\berd1[a-z0-9]{58}\b",
            "ALGORAND": r"\b[A-Z2-7]{58}\b",
            "DASH": r"\b[Xx][a-km-zA-HJ-NP-Z1-9]{25,34}\b",
            "VERGE": r"\b[DdXxYyZz][a-km-zA-HJ-NP-Z1-9]{25,34}\b",
            "DOGECOIN": r"\bD{1}[a-km-zA-HJ-NP-Z1-9]{25,34}\b",
            "CARDANO": r"\b(?:addr1|addr_test1)[0-9a-z]{58,}\b",
            "FILECOIN": r"\b(?:f|t)[0-9][a-z0-9]{20,}\b",
            "HEDERA": r"\b0\.0\.\d+\b",
            "TEZOS": r"\b(?:tz1|tz2|tz3|KT1)[1-9A-HJ-NP-Za-km-z]{33}\b",
            "COTI": r"\b[1-9A-HJ-NP-Za-km-z]{25,45}\b",
            "EVERSCALE": r"\b0:[a-fA-F0-9]{64,}\b",
            "CONFLUX": r"\b(?:cfx:)?0x[a-fA-F0-9]{40}\b"
        }
        for network, pattern in regexes.items():
            if re.match(pattern, address, re.IGNORECASE):
                return network
                
        addr = address.lower()
        if addr.startswith("0x") and len(addr) == 42: return "ETHEREUM"
        if addr.startswith("t") and len(addr) == 34: return "TRON"
        if addr.startswith("1") or addr.startswith("3") or addr.startswith("bc1"): return "BITCOIN"
        return "ETHEREUM"

    @tracer.start_as_current_span("tracing.expand_node")
    async def expand_node(self, node_id: str, network: str, incoming_value: float = 0.0) -> List[Dict[str, Any]]:
        if node_id in self.visited:
            return []
            
        self.visited.add(node_id)
        txs = await orchestrator.fetch_parallel(node_id, network)
        
        # Calculate total inflows to this node for proportional lineage
        total_inflow = sum([float(tx.get("value", 0)) / 1e18 if "0x" in node_id else float(tx.get("value", 0)) for tx in txs if str(tx.get("to", "")).lower() == node_id.lower()])
        # Base case: if it's the target node, incoming_value represents 100% of its value
        total_inflow = max(total_inflow, incoming_value, 1e-9) # prevent div by zero
        
        outflows = []
        for tx in txs:
            try:
                # Default native value
                val = float(tx.get("value", 0)) / 1e18 if "0x" in node_id else float(tx.get("value", 0))
                frm = str(tx.get("from", "")).lower()
                to_addr = str(tx.get("to", "")).lower()
                input_data = tx.get("input", "0x")
                token_address = None
                
                # ERC-20 Token Transfer Decoding
                if input_data and input_data.startswith("0xa9059cbb") and len(input_data) >= 138:
                    # Token contract is the 'to' address of the transaction
                    token_address = to_addr
                    # The actual recipient is encoded in the input data
                    to_addr = "0x" + input_data[34:74]
                    # The value is the last 32 bytes
                    try:
                        raw_token_val = int(input_data[74:138], 16)
                        # Assume 18 decimals for standard ERC20 without contract call
                        val = raw_token_val / 1e18
                    except ValueError:
                        pass
                
                if frm == node_id.lower() and val > 0.001 and to_addr != node_id.lower():
                    tx_type = "TRANSFER"
                    if input_data != "0x" and not input_data.startswith("0xa9059cbb"):
                        if "swap" in input_data.lower(): tx_type = "SWAP"
                        else: tx_type = "CONTRACT_CALL"
                    elif input_data.startswith("0xa9059cbb"):
                        tx_type = "ERC20_TRANSFER"
                        
                    # Value Propagation (Lineage)
                    # How much of the suspect's original value flows into this specific transaction?
                    # Using a simplified proportional model
                    lineage_percentage = (val / total_inflow) if total_inflow > 0 else 0
                    propagated_value = incoming_value * lineage_percentage
                    
                    # Historical Valuation Placeholder (Would use CoinGecko/Binance API based on timestamp)
                    # For now, approximate 1 ETH = $3000 as a static example
                    usd_valuation = val * 3000.0 if network == "ETHEREUM" else val * 100.0

                    outflows.append({
                        "hash": tx.get("hash", ""),
                        "from": node_id,
                        "to": to_addr,
                        "value": val,
                        "token_address": token_address,
                        "tx_type": tx_type,
                        "chain": network,
                        "timestamp": tx.get("timeStamp", "0"),
                        "lineage_percentage": lineage_percentage,
                        "propagated_value": propagated_value,
                        "usd_valuation": usd_valuation
                    })
            except Exception as e:
                logger.error(f"Error parsing transaction: {e}")
                
        return outflows

    @tracer.start_as_current_span("tracing.recursive_trace")
    async def execute_trace(self, target_address: str, max_depth: int = settings.trace_max_depth, stream_callback=None) -> nx.DiGraph:
        """
        Executes a multi-path recursive trace up to max_depth.
        Incorporates Lineage Tracking and Value Propagation.
        """
        logger.info(f"Starting recursive trace for {target_address} up to depth {max_depth}")
        network = self._identify_network(target_address)
        
        self.graph.clear()
        self.visited.clear()
        
        self.graph.add_node(target_address, type="TARGET", network=network, incoming_value=1.0)
        if stream_callback:
            await stream_callback("node", {"address": target_address, "type": "TARGET", "network": network, "depth": 0})
            
        # Current frontier of nodes to explore: dict of {address: incoming_value}
        # Initial target is treated as having 100% (1.0) of the target value.
        frontier = {target_address: 1.0}
        
        for depth in range(max_depth):
            if not frontier:
                break
                
            logger.info(f"Expanding trace frontier at depth {depth}. Nodes: {len(frontier)}")
            
            # Fetch all nodes in frontier concurrently
            tasks = [self.expand_node(node, network, inc_val) for node, inc_val in frontier.items()]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            next_frontier = {}
            
            for (node, incoming_val), outflows in zip(frontier.items(), results):
                if isinstance(outflows, Exception):
                    logger.error(f"Failed to expand {node}: {outflows}")
                    continue
                    
                for outflow in outflows:
                    to_addr = outflow["to"]
                    
                    # Add to graph
                    if to_addr not in self.graph:
                        self.graph.add_node(to_addr, type="INTERMEDIARY", network=network)
                        if stream_callback:
                            await stream_callback("node", {"address": to_addr, "type": "INTERMEDIARY", "network": network, "depth": depth + 1})
                        
                    edge_data = {
                        "hash": outflow["hash"],
                        "value": outflow["value"],
                        "token_address": outflow["token_address"],
                        "tx_type": outflow["tx_type"],
                        "timestamp": outflow["timestamp"],
                        "lineage_percentage": outflow["lineage_percentage"],
                        "propagated_value": outflow["propagated_value"],
                        "usd_valuation": outflow["usd_valuation"]
                    }
                    self.graph.add_edge(
                        outflow["from"], 
                        to_addr, 
                        **edge_data
                    )
                    if stream_callback:
                        await stream_callback("edge", {"from": outflow["from"], "to": to_addr, "data": edge_data})
                    
                    if to_addr not in self.visited:
                        # Accumulate incoming value for the next frontier step
                        next_frontier[to_addr] = next_frontier.get(to_addr, 0) + outflow["propagated_value"]
                        
            frontier = next_frontier
            
        logger.info(f"Trace completed. Graph has {self.graph.number_of_nodes()} nodes and {self.graph.number_of_edges()} edges.")
        return self.graph
