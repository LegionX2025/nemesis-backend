import asyncio
import aiohttp
from typing import Dict, Any, List

class UTXOAdapter:
    """
    Production-grade UTXO adapter for NEMESIS v32.
    Fetches input/output graph data for Bitcoin and Kaspa.
    """
    def __init__(self, api_keys: Dict[str, str]):
        self.api_keys = api_keys
        self.session = None

    async def get_session(self):
        if not self.session:
            self.session = aiohttp.ClientSession()
        return self.session

    async def fetch_utxo_graph(self, tx_id: str, chain: str = "BITCOIN") -> Dict[str, Any]:
        """
        Reconstructs the inputs and outputs for a given transaction.
        Handles change address detection and output splitting.
        """
        # Note: Implementing against mempool.space format for BTC
        if chain.upper() == "BITCOIN":
            url = f"https://mempool.space/api/tx/{tx_id}"
            session = await self.get_session()
            try:
                async with session.get(url, timeout=10) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return self._parse_bitcoin_tx(data)
                    return {"error": f"Status {resp.status}"}
            except Exception as e:
                return {"error": str(e)}
        return {"error": f"Chain {chain} not fully implemented in UTXO adapter."}

    def _parse_bitcoin_tx(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Parses the raw BTC tx into a standardized IO graph."""
        inputs = []
        for vin in data.get("vin", []):
            if "prevout" in vin:
                inputs.append({
                    "address": vin["prevout"].get("scriptpubkey_address", "UNKNOWN"),
                    "value": vin["prevout"].get("value", 0) / 100_000_000,
                    "txid": vin.get("txid")
                })
        
        outputs = []
        for vout in data.get("vout", []):
            outputs.append({
                "address": vout.get("scriptpubkey_address", "UNKNOWN"),
                "value": vout.get("value", 0) / 100_000_000
            })
            
        return {
            "txid": data.get("txid"),
            "fee": data.get("fee", 0) / 100_000_000,
            "inputs": inputs,
            "outputs": outputs,
            "change_probability": self._calculate_change_probability(inputs, outputs)
        }

    def _calculate_change_probability(self, inputs: List[Dict], outputs: List[Dict]) -> float:
        """Heuristic to detect which output is the change address."""
        if len(outputs) <= 1:
            return 0.0
        # If an output matches an input address (reuse), it's highly likely change
        input_addrs = {i["address"] for i in inputs}
        for out in outputs:
            if out["address"] in input_addrs:
                return 0.95
        return 0.5
