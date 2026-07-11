import os
import aiohttp
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import logging
from bs4 import BeautifulSoup
import json

logger = logging.getLogger("OmniChainEngine.OSINT")

class OSINTScraper:
    def __init__(self, mongo_uri="mongodb://localhost:27017"):
        self.client = AsyncIOMotorClient(mongo_uri)
        self.db = self.client["lionsgate_forensics"]
        self.labels_col = self.db["wallet_labels"]
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

    async def auto_resolve_label(self, address: str, network: str = "eth"):
        # Check cache first
        cached = await self.labels_col.find_one({"address": address.lower()})
        if cached:
            return cached.get("label")

        label = None
        
        # 1. Try canonical EVM explorer if we know the chain
        label = await self._scrape_canonical_explorer(address, network)
        
        # 2. Try Ethplorer API / Search
        if not label:
            label = await self._scrape_ethplorer(address)
            
        # 3. Try OKLink
        if not label:
            label = await self._scrape_oklink(address, network)

        if label:
            await self.labels_col.update_one(
                {"address": address.lower()},
                {"$set": {"address": address.lower(), "label": label, "network": network}},
                upsert=True
            )
            return label
        return None
        
    async def _scrape_canonical_explorer(self, address: str, network: str):
        base_urls = {
            "ETH": "https://etherscan.io",
            "BASE": "https://basescan.org",
            "ARB": "https://arbiscan.io",
            "OPT": "https://optimistic.etherscan.io",
            "POLY": "https://polygonscan.com",
            "BSC": "https://bscscan.com",
            "AVA": "https://snowtrace.io",
            "FTM": "https://ftmscan.com"
        }
        net_upper = network.upper()
        base = next((url for key, url in base_urls.items() if key in net_upper), None)
        if not base:
            return None
            
        try:
            url = f"{base}/address/{address}"
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers, timeout=5) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, "html.parser")
                        # Try to find Etherscan public name tag
                        # Usually in a span or div with specific classes, or title
                        tag = soup.find(class_="hash-tag text-truncate")
                        if tag and tag.text.strip():
                            if address.lower() not in tag.text.lower():
                                return tag.text.strip()
                        
                        text = soup.get_text().lower()
                        return self._match_keywords(text)
        except Exception as e:
            logger.warning(f"Canonical explorer scrape failed for {address} on {network}: {e}")
        return None

    def _match_keywords(self, text: str):
        keywords = ["mixers", "dapp", "dex", "defi", "exchange", "cex", "custodial", "swap", "hot wallet", "cold wallet", "darknet", "sanctions", "ofac", "blacklisted"]
        for kw in keywords:
            if kw in text:
                return kw.upper()
        return None

    async def _scrape_ethplorer(self, address: str):
        try:
            url = f"https://ethplorer.io/search/{address}"
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers, timeout=5) as response:
                    if response.status == 200:
                        html = await response.text()
                        return self._match_keywords(html.lower())
        except Exception as e:
            logger.warning(f"Ethplorer scrape failed for {address}: {e}")
        return None

    async def _scrape_oklink(self, address: str, network: str):
        try:
            # Fallback to eth if network not recognized by oklink
            oklink_net = network.lower() if network else "eth"
            if "bsc" in oklink_net or "bnb" in oklink_net: oklink_net = "bsc"
            elif "poly" in oklink_net or "matic" in oklink_net: oklink_net = "polygon"
            
            url = f"https://www.oklink.com/{oklink_net}/address/{address}"
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers, timeout=5) as response:
                    if response.status == 200:
                        html = await response.text()
                        return self._match_keywords(html.lower())
        except Exception as e:
            logger.warning(f"OKLink scrape failed for {address}: {e}")
        return None
