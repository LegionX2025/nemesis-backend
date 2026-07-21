import os
import asyncio
import logging
import requests

logger = logging.getLogger("OmniChainEngine.Scraper")

# Keywords to classify wallets
BEHAVIOR_KEYWORDS = {
    "MIXER": ["mixer", "tornado", "coinjoin", "blender", "tumbler", "mixing"],
    "CEX": ["exchange", "binance", "coinbase", "kraken", "kucoin", "okx", "huobi", "bybit", "cex", "custodial", "hot wallet", "cold wallet"],
    "DEX": ["dex", "uniswap", "sushiswap", "pancakeswap", "curve", "swap", "1inch", "amm", "liquidity"],
    "DEFI": ["defi", "lending", "aave", "compound", "maker", "yield", "vault", "staking"],
    "BRIDGE": ["bridge", "portal", "wormhole", "multichain", "layerzero", "hop", "stargate", "wrapped", "wrap", "unwrap"],
    "DARKNET": ["darknet", "silk road", "hydra", "black market", "sanctioned", "ofac", "blacklisted", "scam", "phishing", "hack", "exploiter"],
}

EXPLORER_REGISTRY = {
    "ETHEREUM": "https://etherscan.io",
    "ETH": "https://etherscan.io",
    "BASE": "https://basescan.org",
    "ARBITRUM": "https://arbiscan.io",
    "OPTIMISM": "https://optimistic.etherscan.io",
    "POLYGON": "https://polygonscan.com",
    "BSC": "https://bscscan.com",
    "AVALANCHE": "https://snowtrace.io",
    "FANTOM": "https://ftmscan.com",
    "SONIC": "https://sonicscan.org",
    "SCROLL": "https://scrollscan.com",
    "LINEA": "https://lineascan.build",
    "BLAST": "https://blastscan.io",
    "MANTLE": "https://mantlescan.xyz",
    "CRONOS": "https://cronoscan.com",
    "GNOSIS": "https://gnosisscan.io"
}

class AutoScraper:
    def __init__(self):
        self.service_url = os.getenv("OMNI_SCRAPER_URL", "http://localhost:8002")
        
    async def start(self):
        pass

    async def stop(self):
        pass
            
    def _classify_text(self, text: str) -> tuple:
        if not text:
            return None, None
            
        text = text.lower()
        found_cluster = None
        found_label = None
        
        for cluster, keywords in BEHAVIOR_KEYWORDS.items():
            for kw in keywords:
                if kw in text:
                    found_cluster = cluster
                    found_label = kw.title() + " " + cluster
                    if "binance" in text: found_label = "Binance"
                    if "coinbase" in text: found_label = "Coinbase"
                    if "kraken" in text: found_label = "Kraken"
                    if "tornado" in text: found_label = "Tornado Cash"
                    break
            if found_cluster:
                break
                
        return found_label, found_cluster

    async def _fetch_from_service(self, address: str, chain: str) -> tuple:
        try:
            # We use a thread to avoid blocking the event loop with synchronous requests,
            # or in Cloudflare Workers requests might just be patched.
            url = f"{self.service_url}/api/scrape/deep"
            response = requests.post(url, json={"address": address, "chain": chain}, timeout=30)
            if response.status_code == 200:
                data = response.json()
                tags = data.get("tags", [])
                text_blob = " | ".join(tags)
                return self._classify_text(text_blob)
            return None, None
        except Exception as e:
            logger.error(f"Failed to fetch from OmniScraper for {address}: {e}")
            return None, None

    async def scrape_ethplorer(self, address: str) -> tuple:
        return await self._fetch_from_service(address, "ETHEREUM")

    async def scrape_blockscan(self, address: str) -> tuple:
        return await self._fetch_from_service(address, "MULTI-EVM")

    async def scrape_oklink(self, address: str, chain: str) -> tuple:
        return await self._fetch_from_service(address, chain)

    async def run_omniscrape(self, address: str, chain: str = "EVM_AUTO") -> tuple:
        logger.info(f"Initiating OmniScrape for {address} on {chain} via External Service...")
        
        if chain in ["ETHEREUM", "EVM_AUTO", "MULTI-EVM", "ETH"]:
            l, c = await self.scrape_ethplorer(address)
            if c: return l, c
            
            l, c = await self.scrape_blockscan(address)
            if c: return l, c
            
        l, c = await self.scrape_oklink(address, chain)
        if c: return l, c
            
        return "Unclassified", "UNKNOWN"

    async def resolve_address(self, address: str, chain: str, trace_id: str):
        logger.info(f"Background resolution triggered for {address} on {chain}")
        label, cluster = await self.run_omniscrape(address, chain)
        if cluster and cluster != "UNKNOWN":
            try:
                from services.database import mongo_db
                if mongo_db is not None:
                    from datetime import datetime, timezone
                    await mongo_db.wallet_labels.update_one(
                        {"address": address.lower()},
                        {"$set": {
                            "label": label, 
                            "source": "OmniScrape", 
                            "timestamp": datetime.now(timezone.utc)
                        }},
                        upsert=True
                    )
            except Exception as e:
                logger.error(f"Failed to save OmniScrape result for {address}: {e}")

scraper_instance = AutoScraper()
