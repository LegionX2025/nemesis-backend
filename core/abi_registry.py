import os
import json
import logging
import asyncio
from typing import Dict, Any, Optional

logger = logging.getLogger("NEMESIS.GBIO.ABIRegistry")

class ABIRegistry:
    """
    Tier-11 ABI Registry & Caching Engine.
    Manages verified ABIs, transparently fetching from block explorers 
    if not locally cached. Includes support for dynamic proxy resolution.
    """
    def __init__(self, api_indexer):
        self.api_indexer = api_indexer
        self.cache_dir = os.path.join(os.path.dirname(__file__), "..", "data", "abis")
        self.memory_cache: Dict[str, Any] = {}
        
        # Ensure cache directory exists
        os.makedirs(self.cache_dir, exist_ok=True)
        self._preload_common_abis()

    def _preload_common_abis(self):
        """Loads critical standard ABIs (ERC20, ERC721) into memory immediately."""
        self.memory_cache["erc20"] = [
            {"constant": True, "inputs": [], "name": "name", "outputs": [{"name": "", "type": "string"}], "type": "function"},
            {"constant": True, "inputs": [], "name": "totalSupply", "outputs": [{"name": "", "type": "uint256"}], "type": "function"},
            {"constant": True, "inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}], "type": "function"},
            {"constant": True, "inputs": [{"name": "", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "", "type": "uint256"}], "type": "function"},
            {"constant": True, "inputs": [], "name": "symbol", "outputs": [{"name": "", "type": "string"}], "type": "function"}
        ]
        logger.info("[ABIRegistry] Preloaded core standard ABIs into memory.")

    def _get_cache_path(self, chain: str, address: str) -> str:
        return os.path.join(self.cache_dir, f"{chain}_{address.lower()}.json")

    async def get_abi(self, address: str, chain: str = "ethereum") -> Optional[List[Dict[str, Any]]]:
        """
        Retrieves the ABI for a contract address.
        Strategy: Memory Cache -> Disk Cache -> API Fetch (via Indexer)
        """
        cache_key = f"{chain}_{address.lower()}"
        
        # 1. Memory Cache
        if cache_key in self.memory_cache:
            return self.memory_cache[cache_key]

        # 2. Disk Cache
        disk_path = self._get_cache_path(chain, address)
        if os.path.exists(disk_path):
            try:
                with open(disk_path, "r", encoding="utf-8") as f:
                    abi = json.load(f)
                    self.memory_cache[cache_key] = abi
                    return abi
            except Exception as e:
                logger.error(f"[ABIRegistry] Corrupted disk cache for {cache_key}: {e}")

        # 3. Dynamic Fetch (Block Explorers)
        abi = await self._fetch_from_explorer(address, chain)
        if abi:
            self.memory_cache[cache_key] = abi
            try:
                with open(disk_path, "w", encoding="utf-8") as f:
                    json.dump(abi, f)
            except Exception as e:
                logger.error(f"[ABIRegistry] Failed to write cache for {cache_key}: {e}")
            return abi

        return None

    async def _fetch_from_explorer(self, address: str, chain: str) -> Optional[List[Dict[str, Any]]]:
        """
        Dynamically routes the ABI fetch request to the correct block explorer
        using the APIEndpointIndexer.
        """
        provider_name = f"{chain}scan" if chain != "ethereum" else "etherscan"
        provider_cfg = self.api_indexer.get_provider(provider_name)
        
        if not provider_cfg:
            logger.warning(f"[ABIRegistry] No block explorer configured for chain '{chain}'")
            return None

        # Lazy import requests to keep module light
        import requests
        
        url = provider_cfg["base_url"]
        params = {
            "module": "contract",
            "action": "getabi",
            "address": address
        }
        
        # Inject auto-indexed parameters/headers
        if provider_cfg["auth_type"] == "query":
            params.update(provider_cfg["params"])
            
        try:
            logger.info(f"[ABIRegistry] Fetching ABI from {provider_name} for {address}")
            # Run in executor to prevent blocking the async loop
            response = await asyncio.to_thread(
                requests.get, url, params=params, headers=provider_cfg.get("headers", {}), timeout=10
            )
            data = response.json()
            
            if data.get("status") == "1" and data.get("result"):
                return json.loads(data["result"])
            else:
                logger.debug(f"[ABIRegistry] ABI fetch failed or contract unverified: {data.get('message')}")
                return None
        except Exception as e:
            logger.error(f"[ABIRegistry] Network error fetching ABI for {address}: {e}")
            return None
