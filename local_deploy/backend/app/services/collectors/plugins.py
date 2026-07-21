import asyncio
from typing import List, Dict, Any
from app.services.collectors.base_collector import BaseCollector

class TransferCollector(BaseCollector):
    async def fetch(self, wallet: str, chain: str, depth: int) -> List[Dict[str, Any]]:
        # In production, this runs a GraphQL query against self.endpoint
        edges = []
        return edges

class DexCollector(BaseCollector):
    async def fetch(self, wallet: str, chain: str, depth: int) -> List[Dict[str, Any]]:
        edges = []
        return edges

class BridgeCollector(BaseCollector):
    async def fetch(self, wallet: str, chain: str, depth: int) -> List[Dict[str, Any]]:
        edges = []
        return edges
