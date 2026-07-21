import logging
import aiohttp
from typing import Dict, Any, List

logger = logging.getLogger("ABIDecoder")

class ABIDecodingEngine:
    def __init__(self):
        # Local mapping of known critical signatures
        self.known_signatures = {
            "0xa9059cbb": "Transfer(address,uint256)",
            "0x23b872dd": "TransferFrom(address,address,uint256)",
            "0x095ea7b3": "Approve(address,uint256)",
            "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef": "Transfer(address,address,uint256)",
            "0x8c5be1e5ebec7d5bd14f71427d1e84f3dd0314c0f7b2291e5b200ac8c7c3b925": "Approval(address,address,uint256)"
        }
        
    async def decode_transaction_input(self, input_data: str) -> Dict[str, Any]:
        """
        Decodes the 4-byte selector and parameters.
        """
        if not input_data or input_data == "0x" or len(input_data) < 10:
            return {"method": "NATIVE_TRANSFER", "decoded": False}
            
        selector = input_data[:10].lower()
        signature = self.known_signatures.get(selector, "UNKNOWN_METHOD")
        
        # If unknown, we could try 4byte.directory lookup
        if signature == "UNKNOWN_METHOD":
            signature = await self._lookup_4byte(selector)
            if signature:
                self.known_signatures[selector] = signature
                
        return {
            "method": signature,
            "selector": selector,
            "decoded": signature != "UNKNOWN_METHOD"
        }
        
    async def decode_event_log(self, topics: List[str], data: str) -> Dict[str, Any]:
        """
        Decodes an event log based on topic0 hash.
        """
        if not topics: return {"event": "UNKNOWN_EVENT"}
        topic0 = topics[0].lower()
        signature = self.known_signatures.get(topic0, "UNKNOWN_EVENT")
        
        return {
            "event": signature,
            "topic0": topic0,
            "indexed_params": topics[1:],
            "data": data,
            "decoded": signature != "UNKNOWN_EVENT"
        }
        
    async def _lookup_4byte(self, selector: str) -> str:
        """Heuristic fallback to 4byte.directory"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"https://www.4byte.directory/api/v1/signatures/?hex_signature={selector}"
                async with session.get(url, timeout=5) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if data.get("count", 0) > 0:
                            return data["results"][0]["text_signature"]
        except Exception:
            pass
        return None

abi_decoder = ABIDecodingEngine()
