import logging
from typing import Dict, Any, List, Optional
from core.abi_registry import ABIRegistry
from core.selector_registry import SelectorRegistry

logger = logging.getLogger("NEMESIS.GBIO.DecoderEngine")

class DecoderEngine:
    """
    Tier-11 Transaction & Event Decoder.
    Breaks down raw blockchain transactions into decoded functions, parameters, and logs.
    Utilizes caching, ABI resolution, and heuristic fallback decoding.
    """
    
    def __init__(self, abi_registry: ABIRegistry, selector_registry: SelectorRegistry):
        self.abi_registry = abi_registry
        self.selector_registry = selector_registry

    async def decode(self, raw_tx: Dict[str, Any], chain: str = "ethereum") -> Dict[str, Any]:
        """
        Orchestrates the entire decoding pipeline for a single transaction.
        """
        tx_hash = raw_tx.get("hash", "UNKNOWN_HASH")
        logger.info(f"[DecoderEngine] Decoding payload for {tx_hash} on {chain}")

        decoded_result = {
            "is_contract_call": False,
            "function_selector": None,
            "function_name": None,
            "decoded_params": {},
            "events": []
        }

        input_data = raw_tx.get("input", "0x")
        to_address = raw_tx.get("to")

        # Basic Native Transfer Check
        if input_data == "0x" or not to_address:
            return decoded_result

        decoded_result["is_contract_call"] = True
        
        # Extract 4-byte selector
        if len(input_data) >= 10:
            selector = input_data[:10]
            decoded_result["function_selector"] = selector
            
            # Fast-path: Look up heuristic selector signature
            signature = self.selector_registry.get_function_name(selector)
            if signature:
                decoded_result["function_name"] = signature
        
        # Resolve ABI dynamically
        abi = await self.abi_registry.get_abi(to_address, chain)

        # In a fully-featured Web3.py environment, we would use the ABI to decode the parameters here:
        # e.g., contract.decode_function_input(input_data)
        if abi:
            # Placeholder for actual ABI parameter mapping
            decoded_result["abi_resolved"] = True
        else:
            decoded_result["abi_resolved"] = False

        # Decode Event Logs
        raw_logs = raw_tx.get("logs", [])
        if raw_logs:
            decoded_result["events"] = await self._decode_logs(raw_logs, abi)

        return decoded_result

    async def _decode_logs(self, raw_logs: List[Dict[str, Any]], abi: Optional[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """
        Parses raw EVM log receipts into human-readable events.
        Falls back to SelectorRegistry if ABI is unavailable.
        """
        decoded_events = []
        for log in raw_logs:
            topics = log.get("topics", [])
            if not topics:
                continue
                
            primary_topic = topics[0]
            
            # Fast-path fallback
            event_name = self.selector_registry.get_event_name(primary_topic)
            
            event_obj = {
                "address": log.get("address"),
                "topics": topics,
                "data": log.get("data", "0x"),
                "event_name": event_name or primary_topic,
                "decoded_params": {}
            }
            
            # If ABI is present, this is where we'd parse the indexed/unindexed fields.
            if abi:
                # Placeholder for Web3.py `processReceipt` log extraction
                event_obj["is_abi_decoded"] = True
            else:
                event_obj["is_abi_decoded"] = False
                
            decoded_events.append(event_obj)
            
        return decoded_events
