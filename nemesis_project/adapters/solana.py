import os
import aiohttp
import asyncio
import logging

logger = logging.getLogger("OmniChainEngine.Solana")

class SolanaAdapter:
    def __init__(self):
        self.rpc_url = os.getenv("RPC_SOLANA", "https://api.mainnet-beta.solana.com")

    async def get_transactions(self, address: str):
        logger.info(f"Fetching Solana transactions for {address}")
        # Fetch basic signatures via RPC
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getSignaturesForAddress",
            "params": [
                address,
                {"limit": 200}
            ]
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.rpc_url, json=payload, timeout=10) as r:
                    if r.status == 200:
                        data = await r.json()
                        sigs = [item["signature"] for item in data.get("result", [])]
                        return sigs
        except Exception as e:
            logger.error(f"Solana get_transactions error: {e}")
        return []

    async def get_program_logs(self, signature: str):
        # Fetch the tx data to extract program logs for MINT, TRANSFER, SWAP
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getTransaction",
            "params": [
                signature,
                {"encoding": "json", "maxSupportedTransactionVersion": 0}
            ]
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.rpc_url, json=payload, timeout=10) as r:
                    if r.status == 200:
                        data = await r.json()
                        meta = data.get("result", {}).get("meta", {})
                        logs = meta.get("logMessages", [])
                        return self._parse_solana_logs(logs)
        except Exception as e:
            logger.error(f"Solana get_program_logs error: {e}")
        return []

    def _parse_solana_logs(self, logs):
        events = []
        for log in logs:
            if "Instruction: MintTo" in log:
                events.append({"intent": "MINT", "raw": log})
            elif "Instruction: Transfer" in log:
                events.append({"intent": "TRANSFER", "raw": log})
            elif "Instruction: Swap" in log:
                events.append({"intent": "SWAP", "raw": log})
            elif "Program log: Instruction: Route" in log: # Jupiter Swap
                events.append({"intent": "SWAP", "raw": log})
        return events
