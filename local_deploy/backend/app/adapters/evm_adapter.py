import asyncio
import aiohttp
from typing import Dict, Any, List

class EVMAdapter:
    """
    Production-grade EVM adapter for NEMESIS v32.
    Fetches transactions, receipts, and logs for Ethereum + all EVMs.
    """
    def __init__(self, rpc_urls: Dict[str, str], explorer_keys: Dict[str, str]):
        self.rpc_urls = rpc_urls
        self.explorer_keys = explorer_keys
        self.session = None
        
    async def get_session(self):
        if not self.session:
            self.session = aiohttp.ClientSession()
        return self.session
        
    async def fetch_transaction(self, chain: str, tx_hash: str) -> Dict[str, Any]:
        """Fetches raw transaction data via RPC or Explorer fallback."""
        url = self.rpc_urls.get(chain, self.rpc_urls.get("ETHEREUM"))
        payload = {
            "jsonrpc": "2.0",
            "method": "eth_getTransactionByHash",
            "params": [tx_hash],
            "id": 1
        }
        session = await self.get_session()
        try:
            async with session.post(url, json=payload, timeout=5) as resp:
                data = await resp.json()
                return data.get("result", {})
        except Exception as e:
            return {"error": str(e)}

    async def fetch_receipt(self, chain: str, tx_hash: str) -> Dict[str, Any]:
        """Fetches transaction receipt and event logs."""
        url = self.rpc_urls.get(chain, self.rpc_urls.get("ETHEREUM"))
        payload = {
            "jsonrpc": "2.0",
            "method": "eth_getTransactionReceipt",
            "params": [tx_hash],
            "id": 1
        }
        session = await self.get_session()
        try:
            async with session.post(url, json=payload, timeout=5) as resp:
                data = await resp.json()
                return data.get("result", {})
        except Exception as e:
            return {"error": str(e)}

    async def simulate_trace(self, chain: str, tx_hash: str) -> List[Dict]:
        """Uses debug_traceTransaction if available to reconstruct internal calls."""
        url = self.rpc_urls.get(chain, self.rpc_urls.get("ETHEREUM"))
        payload = {
            "jsonrpc": "2.0",
            "method": "debug_traceTransaction",
            "params": [tx_hash, {"tracer": "callTracer"}],
            "id": 1
        }
        session = await self.get_session()
        try:
            async with session.post(url, json=payload, timeout=10) as resp:
                data = await resp.json()
                return data.get("result", {}).get("calls", [])
        except Exception as e:
            return []
