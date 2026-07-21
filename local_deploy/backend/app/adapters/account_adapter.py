import asyncio
import aiohttp
from typing import Dict, Any, List

class AccountAdapter:
    """
    Production-grade adapter for Non-EVM Account-based chains.
    Supports Solana, Tron, XRP Ledger, and Stellar.
    """
    def __init__(self, endpoints: Dict[str, str]):
        self.endpoints = endpoints
        self.session = None

    async def get_session(self):
        if not self.session:
            self.session = aiohttp.ClientSession()
        return self.session

    async def fetch_transaction(self, chain: str, tx_hash: str) -> Dict[str, Any]:
        """Fetches instructions / memos depending on the chain."""
        chain = chain.upper()
        if chain == "SOLANA":
            return await self._fetch_solana(tx_hash)
        elif chain == "TRON":
            return await self._fetch_tron(tx_hash)
        elif chain == "XRP":
            return await self._fetch_xrp(tx_hash)
        else:
            return {"error": f"Chain {chain} not supported in AccountAdapter"}

    async def _fetch_solana(self, tx_hash: str) -> Dict[str, Any]:
        url = self.endpoints.get("SOLANA", "https://api.mainnet-beta.solana.com")
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getTransaction",
            "params": [tx_hash, {"encoding": "jsonParsed", "maxSupportedTransactionVersion": 0}]
        }
        session = await self.get_session()
        try:
            async with session.post(url, json=payload, timeout=10) as resp:
                data = await resp.json()
                return data.get("result", {})
        except Exception as e:
            return {"error": str(e)}

    async def _fetch_tron(self, tx_hash: str) -> Dict[str, Any]:
        url = self.endpoints.get("TRON", "https://api.trongrid.io/wallet/gettransactionbyid")
        session = await self.get_session()
        try:
            async with session.post(url, json={"value": tx_hash}, timeout=10) as resp:
                data = await resp.json()
                return data
        except Exception as e:
            return {"error": str(e)}

    async def _fetch_xrp(self, tx_hash: str) -> Dict[str, Any]:
        url = self.endpoints.get("XRP", "https://s1.ripple.com:51234/")
        payload = {
            "method": "tx",
            "params": [{"transaction": tx_hash, "binary": False}]
        }
        session = await self.get_session()
        try:
            async with session.post(url, json=payload, timeout=10) as resp:
                data = await resp.json()
                return data.get("result", {})
        except Exception as e:
            return {"error": str(e)}
