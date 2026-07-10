import asyncio
import aiohttp
from typing import Dict, Any

class BytecodeAnalyzer:
    """
    Introspects Smart Contract Bytecode to detect Proxies, Implementation slots,
    and extract basic Function Selectors.
    """
    def __init__(self, rpc_urls: Dict[str, str]):
        self.rpc_urls = rpc_urls
        self.session = None

    async def get_session(self):
        if not self.session:
            self.session = aiohttp.ClientSession()
        return self.session

    async def analyze_contract(self, chain: str, address: str) -> Dict[str, Any]:
        """Fetches bytecode and performs static analysis."""
        bytecode = await self._fetch_code(chain, address)
        if not bytecode or bytecode == "0x":
            return {"is_contract": False, "is_proxy": False}

        is_proxy = self._detect_proxy(bytecode)
        impl_address = None
        if is_proxy:
            # EIP-1967 Implementation Slot
            # 0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc
            impl_address = await self._fetch_storage_at(
                chain, address, 
                "0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc"
            )
            # Cleanup padding
            if impl_address and len(impl_address) == 66:
                impl_address = "0x" + impl_address[-40:]

        return {
            "is_contract": True,
            "bytecode_hash": hash(bytecode),
            "is_proxy": is_proxy,
            "implementation": impl_address,
            "suspicious_patterns": self._scan_vulnerabilities(bytecode)
        }

    async def _fetch_code(self, chain: str, address: str) -> str:
        url = self.rpc_urls.get(chain, self.rpc_urls.get("ETHEREUM"))
        payload = {"jsonrpc": "2.0", "method": "eth_getCode", "params": [address, "latest"], "id": 1}
        session = await self.get_session()
        try:
            async with session.post(url, json=payload, timeout=5) as resp:
                data = await resp.json()
                return data.get("result", "0x")
        except:
            return "0x"

    async def _fetch_storage_at(self, chain: str, address: str, slot: str) -> str:
        url = self.rpc_urls.get(chain, self.rpc_urls.get("ETHEREUM"))
        payload = {"jsonrpc": "2.0", "method": "eth_getStorageAt", "params": [address, slot, "latest"], "id": 1}
        session = await self.get_session()
        try:
            async with session.post(url, json=payload, timeout=5) as resp:
                data = await resp.json()
                return data.get("result")
        except:
            return None

    def _detect_proxy(self, bytecode: str) -> bool:
        # Common delegatecall proxy pattern signatures
        return "363d3d373d3d3d363d73" in bytecode or "5c60b068" in bytecode

    def _scan_vulnerabilities(self, bytecode: str) -> list:
        flags = []
        if "ff" in bytecode[-10:]: # SELFDESTRUCT near end
            flags.append("SELFDESTRUCT_CAPABLE")
        return flags
