import asyncio
import logging
from .scraper_engine import scraper_instance

logger = logging.getLogger("SwarmOrchestrator")

class SwarmOrchestrator:
    def __init__(self, max_concurrent=5):
        # Limit parallel scraping to avoid OOM
        self.semaphore = asyncio.Semaphore(max_concurrent)

    async def _fetch_tier1_api(self, address: str, chain: str) -> tuple:
        """Fallback Tier 1: API (Stubbed for now, normally calls Etherscan/Alchemy API)"""
        # In a production system this would use aiohttp to hit an API endpoint.
        await asyncio.sleep(0.1)
        return None, None

    async def _fetch_tier2_scraper(self, address: str, chain: str) -> tuple:
        """Fallback Tier 2: Deep DOM Headless Scraper"""
        async with self.semaphore:
            logger.info(f"[Swarm Agent] Scraping {chain} for {address}...")
            return await scraper_instance.scrape_evm_explorer(address, chain)

    async def _fetch_tier3_osint(self, address: str) -> tuple:
        """Fallback Tier 3: OSINT/Darknet Search"""
        async with self.semaphore:
            # Re-use blockscan as an OSINT multi-chain proxy
            return await scraper_instance.scrape_blockscan(address)

    async def fetch_chain_data(self, address: str, chain: str) -> tuple:
        """Execute the fallback waterfall for a specific chain."""
        # Try API first
        label, cluster = await self._fetch_tier1_api(address, chain)
        if label or cluster:
            return label, cluster
            
        # Fallback to Deep DOM Scraper
        label, cluster = await self._fetch_tier2_scraper(address, chain)
        if label or cluster:
            return label, cluster
            
        # Fallback to general OSINT
        return await self._fetch_tier3_osint(address)

    async def swarm_fetch(self, address: str, chains: list) -> dict:
        """Parallel fetch across multiple chains using a swarm of workers."""
        logger.info(f"[*] Dispatching swarm agents for {address} across {len(chains)} chains...")
        
        tasks = []
        for chain in chains:
            tasks.append(self.fetch_chain_data(address, chain))
            
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        aggregated_data = {}
        for idx, chain in enumerate(chains):
            res = results[idx]
            if isinstance(res, Exception):
                logger.error(f"[Swarm Error] Agent failed on {chain}: {res}")
                aggregated_data[chain] = (None, None)
            else:
                aggregated_data[chain] = res
                
        return aggregated_data

# Singleton
swarm_instance = SwarmOrchestrator()
