import logging
import re
import aiohttp
from typing import Dict, Any

logger = logging.getLogger("BytecodeEngine")

class BytecodeAnalysisEngine:
    def __init__(self):
        self.eip_1967_logic_slot = "0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc"
        self.beacon_proxy_slot = "0xa3f0ad74e5423aebfd80d3ef4346578335a9a72aeaee59ff6cb3582b35133d50"
    
    async def analyze_contract(self, rpc_url: str, address: str) -> Dict[str, Any]:
        """
        Fetches contract bytecode, detects proxy patterns, and extracts basic selectors.
        """
        bytecode = await self._fetch_code(rpc_url, address)
        if not bytecode or bytecode == "0x":
            return {"is_contract": False}
            
        is_proxy = False
        impl_address = None
        
        # Heuristic EIP-1967 Proxy Detection
        if "360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc" in bytecode.lower():
            is_proxy = True
            impl_address = await self._fetch_storage_at(rpc_url, address, self.eip_1967_logic_slot)
            if impl_address:
                # Format to 20 byte address
                impl_address = "0x" + impl_address[-40:]
                
        # Extract 4-byte selectors (heuristic PUSH4 opcodes)
        selectors = re.findall(r'63([a-fA-F0-9]{8})', bytecode)
        
        suspicious_patterns = []
        if "ff" in bytecode: # SELFDESTRUCT opcode heuristic
            suspicious_patterns.append("CONTAINS_SELFDESTRUCT")
        if "f4" in bytecode: # DELEGATECALL
            suspicious_patterns.append("USES_DELEGATECALL")
            
        return {
            "is_contract": True,
            "bytecode_hash": hash(bytecode),
            "is_proxy": is_proxy,
            "implementation_address": impl_address,
            "function_selectors": list(set(selectors)),
            "suspicious_patterns": suspicious_patterns
        }
        
    async def _fetch_code(self, rpc_url: str, address: str) -> str:
        try:
            async with aiohttp.ClientSession() as session:
                payload = {"jsonrpc": "2.0", "method": "eth_getCode", "params": [address, "latest"], "id": 1}
                async with session.post(rpc_url, json=payload) as resp:
                    data = await resp.json()
                    return data.get("result", "0x")
        except Exception as e:
            logger.error(f"Failed to fetch bytecode for {address}: {e}")
            return "0x"
            
    async def _fetch_storage_at(self, rpc_url: str, address: str, slot: str) -> str:
        try:
            async with aiohttp.ClientSession() as session:
                payload = {"jsonrpc": "2.0", "method": "eth_getStorageAt", "params": [address, slot, "latest"], "id": 1}
                async with session.post(rpc_url, json=payload) as resp:
                    data = await resp.json()
                    return data.get("result")
        except:
            return None

bytecode_engine = BytecodeAnalysisEngine()
