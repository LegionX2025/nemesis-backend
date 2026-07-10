import asyncio
import logging
import json
import os
from .scraper_engine import scraper_instance
from .api_rotator import api_rotator

logger = logging.getLogger("SwarmOrchestrator")

class SwarmOrchestrator:
    def __init__(self, max_concurrent=10):
        # Limit parallel scraping to avoid OOM
        self.semaphore = asyncio.Semaphore(max_concurrent)

    async def _fetch_tier1_api(self, session, address: str, chain: str) -> list:
        """Fallback Tier 1: Ankr Advanced API for Multi-Chain Transaction History"""
        chain = chain.upper()
        
        # Map our internal chain names to Ankr's expected blockchain names
        ankr_chain_map = {
            "ETHEREUM": "eth",
            "BSC": "bsc",
            "POLYGON": "polygon",
            "ARBITRUM": "arbitrum",
            "BASE": "base",
            "OPTIMISM": "optimism",
            "AVALANCHE": "avalanche",
            "FANTOM": "fantom",
            "SYSCOIN": "syscoin",
            "LINEA": "linea"
        }
        
        ankr_chain = ankr_chain_map.get(chain)
        if not ankr_chain:
            logger.warning(f"Ankr API does not support {chain}. Skipping Tier 1.")
            return None

        # Fetch Ankr key from api_rotator or env
        ankr_key = os.environ.get("ANKR_API_KEY", "d0ebdc10f7a98d2c08105ddcef64d9353e5b92e1d59e545debed8af8bce60fbc")
        url = f"https://rpc.ankr.com/multichain/{ankr_key}"
        
        all_txs = []
        
        if chain == "TRON":
            try:
                tron_url = f"https://api.trongrid.io/v1/accounts/{address}/transactions/trc20?limit=20"
                async with session.get(tron_url, timeout=15) as r:
                    if r.status == 200:
                        data = await r.json()
                        txs = data.get("data", [])
                        for tx in txs:
                            all_txs.append({
                                "hash": tx.get("transaction_id"),
                                "from": str(tx.get("from", "")).lower(),
                                "to": str(tx.get("to", "")).lower(),
                                "value": tx.get("value", "0"),
                                "timeStamp": str(int(tx.get("block_timestamp", 0)) // 1000),
                                "contractAddress": str(tx.get("token_info", {}).get("address", "")).lower()
                            })
                tron_url_trx = f"https://api.trongrid.io/v1/accounts/{address}/transactions?limit=20"
                async with session.get(tron_url_trx, timeout=15) as r:
                    if r.status == 200:
                        data = await r.json()
                        txs = data.get("data", [])
                        for tx in txs:
                            raw = tx.get("raw_data", {}).get("contract", [{}])[0].get("parameter", {}).get("value", {})
                            val = str(raw.get("amount", 0))
                            if not val or val == "0": continue
                            all_txs.append({
                                "hash": tx.get("txID"),
                                "from": str(raw.get("owner_address", "")).lower(),
                                "to": str(raw.get("to_address", "")).lower(),
                                "value": val,
                                "timeStamp": str(int(tx.get("raw_data", {}).get("timestamp", 0)) // 1000)
                            })
            except Exception as e:
                logger.error(f"TronGrid Request failed: {e}")
            return all_txs

        page_token = ""
        
        while True:
            payload = {
                "jsonrpc": "2.0",
                "method": "ankr_getTransactionsByAddress",
                "params": {
                    "blockchain": ankr_chain,
                    "address": address,
                    "descOrder": True
                },
                "id": 1
            }
            if page_token:
                payload["params"]["pageToken"] = page_token
                
            try:
                async with session.post(url, json=payload, timeout=15) as r:
                    if r.status != 200:
                        logger.error(f"Ankr API Error on {chain}: {r.status} {await r.text()}")
                        return None
                        
                    data = await r.json()
                    
                    if "error" in data:
                        logger.error(f"Ankr API Error Payload on {chain}: {data['error']}")
                        return None
                        
                    result = data.get("result", {})
                    txs = result.get("transactions", [])
                    
                    # Normalize Ankr tx format to Etherscan format for downstream parser
                    for tx in txs:
                        val = tx.get("value", "0")
                        if val.startswith("0x"): val = str(int(val, 16))
                        
                        all_txs.append({
                            "hash": tx.get("hash"),
                            "from": str(tx.get("from", "")).lower(),
                            "to": str(tx.get("to", "")).lower(),
                            "value": val,
                            "timeStamp": str(tx.get("timestamp", 0)),
                            "methodId": tx.get("input", "0x")[:10],
                            "contractAddress": str(tx.get("contractAddress", "")).lower()
                        })
                        
                    next_page = result.get("nextPageToken")
                    if not next_page or not txs:
                        break
                        
                    page_token = next_page
                    await asyncio.sleep(0.5)
                    
            except Exception as e:
                logger.error(f"Ankr Request failed on {chain}: {e}")
                return None
                
        logger.info(f"[Swarm Agent] Extracted {len(all_txs)} historical TXs from Tier 1 (Ankr) API for {address} on {chain}")
        return all_txs

    async def _fetch_tier2_scraper(self, address: str, chain: str) -> list:
        """Fallback Tier 2: Deep DOM Headless Scraper with Pagination loops"""
        async with self.semaphore:
            logger.info(f"[Swarm Agent] Scraping {chain} for {address}...")
            return await scraper_instance.scrape_evm_explorer(address, chain) # Assuming it handles pagination internally or we augment it

    async def fetch_chain_data(self, session, address: str, chain: str) -> list:
        """Execute the fallback waterfall for a specific chain."""
        # Try API first
        txs = await self._fetch_tier1_api(session, address, chain)
        if txs is not None:
            # API succeeded (even if 0 transactions were found)
            return txs
            
        # Fallback to Deep DOM Scraper for Entity Identity (Cannot scrape raw TXs easily via DOM)
        logger.warning(f"Tier 1 API failed for {address} on {chain}. Delegating to Swarm Headless Scraper (Tier 2)...")
        label, cluster = await self._fetch_tier2_scraper(address, chain)
        if label or cluster:
            logger.info(f"[Swarm Agent] Scraped entity identity via DOM: {label} ({cluster})")
            
        # We must return an empty list of transactions to prevent NoneType errors in tracer
        return []

    async def swarm_fetch(self, session, address: str, chains: list) -> dict:
        """Parallel fetch across multiple chains using a swarm of workers."""
        logger.info(f"[*] Dispatching swarm agents for {address} across {len(chains)} chains...")
        
        tasks = []
        for chain in chains:
            tasks.append(self.fetch_chain_data(session, address, chain))
            
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        aggregated_data = {}
        for idx, chain in enumerate(chains):
            res = results[idx]
            if isinstance(res, Exception):
                logger.error(f"[Swarm Error] Agent failed on {chain}: {res}")
                aggregated_data[chain] = []
            else:
                aggregated_data[chain] = res
                
        return aggregated_data

# Singleton
swarm_instance = SwarmOrchestrator()
