import asyncio
import aiohttp
from typing import Dict, Any, List

class ABIDecoder:
    """
    Decodes transaction calldata and event logs using known signatures
    and 4byte directory fallback.
    """
    def __init__(self):
        self.session = None
        self.known_events = {
            "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef": "Transfer(address,address,uint256)",
            "0x8c5be1e5ebec7d5bd14f71427d1e84f3dd0314c0f7b2291e5b200ac8c7c3b925": "Approval(address,address,uint256)",
            "0x1c411e9a96e071241c2f21f7726b17ae89e3cab4c78be50e062b03a9fffbbad1": "Sync(uint112,uint112)",
            "0xd78ad95fa46c994b6551d0da85fc275fe613ce37657fb8d5e3d130840159d822": "Swap(address,uint256,uint256,uint256,uint256,address)"
        }
        self.known_methods = {
            "0xa9059cbb": "transfer(address,uint256)",
            "0x23b872dd": "transferFrom(address,address,uint256)",
            "0x095ea7b3": "approve(address,uint256)",
            "0x38ed1739": "swapExactTokensForTokens",
            "0x7ff36ab5": "swapExactETHForTokens"
        }

    async def get_session(self):
        if not self.session:
            self.session = aiohttp.ClientSession()
        return self.session

    async def decode_event(self, log: Dict[str, Any]) -> Dict[str, Any]:
        """Decodes log topics into semantic events."""
        topics = log.get("topics", [])
        if not topics:
            return {"event": "Unknown", "confidence": 0}

        signature = topics[0]
        event_name = self.known_events.get(signature)
        
        if not event_name:
            # Fallback to 4byte directory
            event_name = await self._fetch_4byte_directory(signature, type="event")
            
        decoded = {
            "event": event_name or f"UnknownEvent({signature[:10]})",
            "contract": log.get("address"),
            "topics": topics,
            "data": log.get("data"),
            "confidence": 1.0 if event_name else 0.2
        }
        return decoded

    async def decode_method(self, input_data: str) -> Dict[str, Any]:
        """Decodes the 4-byte function selector from calldata."""
        if not input_data or len(input_data) < 10:
            return {"method": "fallback", "confidence": 1.0}
            
        selector = input_data[:10].lower()
        method_name = self.known_methods.get(selector)
        
        if not method_name:
            method_name = await self._fetch_4byte_directory(selector, type="function")
            
        return {
            "method": method_name or f"UnknownMethod({selector})",
            "selector": selector,
            "confidence": 1.0 if method_name else 0.2
        }

    async def _fetch_4byte_directory(self, hex_sig: str, type="function") -> str:
        """Fetches from the 4byte.directory API."""
        url = "https://www.4byte.directory/api/v1/signatures/"
        if type == "event":
            url = "https://www.4byte.directory/api/v1/event-signatures/"
            
        session = await self.get_session()
        try:
            async with session.get(url, params={"hex_signature": hex_sig}, timeout=3) as resp:
                data = await resp.json()
                results = data.get("results", [])
                if results:
                    return results[0].get("text_signature")
        except:
            pass
        return None
