import asyncio
import logging
import json
import re
import aiohttp
from bs4 import BeautifulSoup
from datetime import datetime
from services.database_connector import db_engine
import urllib.parse

logger = logging.getLogger("NemesisDarknet")

# Common Tor2Web Proxies to bypass Tor requirement on PaaS
TOR2WEB_PROXIES = [
    ".onion.ly",
    ".onion.pet",
    ".onion.ws"
]

# Seed URLs (Darknet Forums/Markets, ransom watch sites, etc)
SEED_URLS = [
    "http://ransomwr3tty3p4o3.onion", # Mock URL
    "http://exploitxy2abc123.onion",
    "http://cardingmafiax5p.onion"
]

class DarknetCrawlerEngine:
    def __init__(self):
        self.db = None
        self.session = None
        self.stats = {
            "status": "idle",
            "urls_crawled": 0,
            "entities_extracted": 0,
            "last_crawl": None,
            "current_target": None
        }

    async def init_db(self):
        if not self.db:
            await db_engine.connect()
            self.db = db_engine.db

    async def _get_session(self):
        if not self.session:
            self.session = aiohttp.ClientSession(headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            })
        return self.session

    def convert_to_tor2web(self, onion_url):
        """Converts an .onion URL to a Tor2Web proxy URL"""
        if not onion_url.endswith(".onion"):
            return onion_url
            
        # Strip scheme
        clean = onion_url.replace("http://", "").replace("https://", "")
        # Pick random proxy for load balancing
        proxy = TOR2WEB_PROXIES[0] # use .onion.ly for simplicity in this version
        return f"https://{clean.replace('.onion', '')}{proxy}"

    def extract_entities(self, text):
        """Basic Regex Extraction for Crypto & Intel"""
        entities = []
        
        # BTC
        btc_matches = re.findall(r"\b([13][a-km-zA-HJ-NP-Z1-9]{25,34}|bc1[ac-hj-np-z02-9]{11,71})\b", text)
        for m in set(btc_matches):
            entities.append({"type": "CRYPTO_WALLET", "value": m, "chain": "BTC"})
            
        # ETH/EVM
        eth_matches = re.findall(r"\b(0x[a-fA-F0-9]{40})\b", text)
        for m in set(eth_matches):
            entities.append({"type": "CRYPTO_WALLET", "value": m, "chain": "EVM"})
            
        # Emails
        email_matches = re.findall(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", text)
        for m in set(email_matches):
            entities.append({"type": "EMAIL", "value": m})
            
        return entities

    async def crawl_site(self, original_url):
        url = self.convert_to_tor2web(original_url)
        self.stats["current_target"] = original_url
        logger.info(f"[DARKNET] Crawling: {url}")
        
        try:
            session = await self._get_session()
            async with session.get(url, timeout=15) as resp:
                if resp.status == 200:
                    html = await resp.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    text_content = soup.get_text(separator=' ', strip=True)
                    title = soup.title.string if soup.title else original_url
                    
                    entities = self.extract_entities(text_content)
                    
                    # Store in DB
                    doc = {
                        "url": original_url,
                        "proxy_url": url,
                        "title": title,
                        "content_snippet": text_content[:500] + "...",
                        "web_info": {
                            "title": title,
                            "content": text_content,
                            "url": original_url
                        },
                        "uie_entities": entities,
                        "crawled_at": datetime.utcnow()
                    }
                    
                    await self.db.darknet_data.update_one(
                        {"url": original_url},
                        {"$set": doc},
                        upsert=True
                    )
                    
                    self.stats["urls_crawled"] += 1
                    self.stats["entities_extracted"] += len(entities)
                    logger.info(f"[DARKNET] Extracted {len(entities)} entities from {original_url}")
                else:
                    logger.warning(f"[DARKNET] Failed {url} with status {resp.status}")
        except Exception as e:
            logger.error(f"[DARKNET] Error crawling {url}: {e}")

    async def run_crawler_cycle(self):
        self.stats["status"] = "running"
        await self.init_db()
        
        for url in SEED_URLS:
            await self.crawl_site(url)
            await asyncio.sleep(2) # rate limit
            
        self.stats["status"] = "idle"
        self.stats["last_crawl"] = datetime.utcnow().isoformat()
        self.stats["current_target"] = None
        logger.info("[DARKNET] Crawl cycle complete.")

darknet_crawler_engine = DarknetCrawlerEngine()
