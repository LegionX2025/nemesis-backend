import aiohttp
import asyncio
import logging

logger = logging.getLogger("OmniChainEngine.UTXO")

class UTXOAdapter:
    def __init__(self):
        self.mempool_api = "https://mempool.space/api"

    async def get_transactions(self, address: str):
        # Fetch UTXO transactions from mempool.space for Bitcoin
        logger.info(f"Fetching UTXO transactions for {address}")
        try:
            url = f"{self.mempool_api}/address/{address}/txs"
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        return await response.json()
        except Exception as e:
            logger.warning(f"Failed to fetch UTXO transactions for {address}: {e}")
        return []
