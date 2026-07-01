import os
import aiohttp
import asyncio
import logging

logger = logging.getLogger("OmniChainEngine.UTXO")

class UTXOAdapter:
    def __init__(self):
        self.btc_url = os.getenv("RPC_BTC", "https://mempool.space/api")
        self.kaspa_url = os.getenv("RPC_KASPA", "https://api.kaspa.org")

    async def get_btc_utxos(self, address: str):
        url = f"{self.btc_url}/address/{address}/txs"
        events = []
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as r:
                    if r.status == 200:
                        data = await r.json()
                        for tx in data:
                            # Analyze entropy/fan-out
                            in_count = len(tx.get("vin", []))
                            out_count = len(tx.get("vout", []))
                            
                            intent = "TRANSFER"
                            if in_count == 1 and out_count > 10:
                                intent = "FAN_OUT"
                            elif in_count > 5 and out_count == 1:
                                intent = "CONSOLIDATION"
                                
                            events.append({
                                "intent": intent,
                                "tx_hash": tx.get("txid"),
                                "inputs": in_count,
                                "outputs": out_count
                            })
        except Exception as e:
            logger.error(f"BTC get_utxos error: {e}")
        return events

    async def get_kaspa_utxos(self, address: str):
        # Kaspa transaction history
        url = f"{self.kaspa_url}/addresses/{address}/transactions?limit=100"
        events = []
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as r:
                    if r.status == 200:
                        data = await r.json()
                        for tx in data:
                            in_count = len(tx.get("inputs", []))
                            out_count = len(tx.get("outputs", []))
                            
                            intent = "TRANSFER"
                            if in_count == 1 and out_count > 10:
                                intent = "FAN_OUT"
                                
                            events.append({
                                "intent": intent,
                                "tx_hash": tx.get("transaction_id"),
                                "inputs": in_count,
                                "outputs": out_count
                            })
        except Exception as e:
            logger.error(f"Kaspa get_utxos error: {e}")
        return events
