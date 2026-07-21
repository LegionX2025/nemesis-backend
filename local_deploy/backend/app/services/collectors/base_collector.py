from abc import ABC, abstractmethod
from typing import List, Dict, Any

class BaseCollector(ABC):
    """
    Base class for all Bitquery collectors.
    Each collector is responsible for a specific domain (e.g., Transfers, DEX Swaps, Bridging).
    """

    def __init__(self, api_key: str):
        self.api_key = api_key
        # Bitquery V2 Streaming endpoint
        self.endpoint = "https://streaming.bitquery.io/graphql"

    @abstractmethod
    async def fetch(self, wallet: str, chain: str, depth: int) -> List[Dict[str, Any]]:
        """
        Fetch data for a given wallet and chain, up to a certain depth.
        Must return a list of standardized edge dictionaries.
        """
        pass

    def _standardize_edge(self, source: str, target: str, edge_type: str, metadata: dict) -> Dict[str, Any]:
        """
        Helper to emit standardized ontology edges.
        """
        return {
            "source": source.lower(),
            "target": target.lower(),
            "edge_type": edge_type,
            "metadata": metadata
        }
