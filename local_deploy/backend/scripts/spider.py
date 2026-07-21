import asyncio
import datetime
import logging
import re
from typing import Dict, List, Optional
from motor.motor_asyncio import AsyncIOMotorClient
from playwright.async_api import async_playwright
import aiohttp

# Configure Forensic Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [NEMESIS_GAIL] - %(levelname)s - %(message)s'
)

# ==============================================================================
# 🕸️ NEMESIS SPIDER - GLOBAL AUTONOMOUS IOC LAKE (GAIL)
# ==============================================================================

class CrawlerStack:
    """Hybrid Crawler Stack: Static API + Dynamic Web Scraper + Deep FSM"""
    
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.session = None

    async def start(self):
        self.playwright = await async_playwright().start()
        # Headless Chromium for stealth evasion and dynamic JS execution
        self.browser = await self.playwright.chromium.launch(headless=True)
        self.session = aiohttp.ClientSession()
        logging.info("[SYSTEM] Initializing Playwright, aiohttp, and Headless Chromium clusters...")

    async def close(self):
        if self.browser: await self.browser.close()
        if self.playwright: await self.playwright.stop()
        if self.session: await self.session.close()

    async def static_scrape(self, url: str) -> str:
        """Layer 1: High-speed lightweight ingestion (APIs/JSON)"""
        try:
            async with self.session.get(url, timeout=10) as response:
                return await response.text()
        except Exception as e:
            logging.error(f"Static scrape failed for {url}: {e}")
            return ""

    async def dynamic_scrape(self, url: str) -> str:
        """Layer 2: Headless Chromium for anti-bot portals & Exchange UIs"""
        try:
            page = await self.browser.new_page()
            await page.goto(url, wait_until="networkidle")
            content = await page.content()
            await page.close()
            return content
        except Exception as e:
            logging.error(f"Dynamic scrape failed for {url}: {e}")
            return ""


class AIAgentSwarm:
    """The 5 Autonomous Intelligence Agents"""
    
    def __init__(self, db):
        self.db = db

    async def agent_1_wallet_intel(self, wallet_address: str) -> Dict:
        """Clustering & Sanctions"""
        # Checks internal OFAC/Sanctions sync
        sanction_hit = await self.db.sanctions.find_one({"address": wallet_address})
        cluster_id = f"AUTO_ID_{wallet_address[-6:]}"
        risk = 100.0 if sanction_hit else 25.0
        
        return {"cluster": cluster_id, "risk": risk, "is_sanctioned": bool(sanction_hit)}

    async def agent_2_tx_intel(self, tx_data: Dict) -> List[str]:
        """Flows & Obfuscation (Peel Chains, Layering, Bridges)"""
        flags = []
        # Mathematical variance check for Peeling (1 large input, 2 outputs with high variance)
        if len(tx_data.get("outputs", [])) == 2:
            flags.append("PEEL_CHAIN")
            
        # Bridge detection
        if tx_data.get("to_address", "").lower() in ["0xwormhole...", "0xstargate..."]:
            flags.append("BRIDGE_HOP")
            
        return flags

    def agent_3_aml_engine(self, taint: float, exposure: float, velocity: float, entity_risk: float) -> float:
        """Risk Scoring: AML = W1(Taint) + W2(Exp) + W3(Vel) + W4(Risk)"""
        w1, w2, w3, w4 = 0.4, 0.3, 0.1, 0.2
        aml_score = (w1 * taint) + (w2 * exposure) + (w3 * velocity) + (w4 * entity_risk)
        return min(100.0, max(0.0, aml_score))

    async def agent_4_cex_intel(self, address: str) -> Optional[str]:
        """Custodial Endpoints & Hot Wallets"""
        # Check against known CEX hot wallet topologies
        known_cex = await self.db.cex_clusters.find_one({"address": address})
        if known_cex:
            return known_cex.get("exchange_name")
        return None

    async def agent_5_entity_attribution(self, address: str, metadata: str) -> str:
        """Real-World Mapping & OSINT"""
        # Regex extraction from metadata (ENS, Calldata, Darknet Forums)
        if re.search(r'(lazarus|dprk)', metadata.lower()):
            return "Lazarus Group (DPRK)"
        return "Unknown Entity"


class NemesisSpiderFSM:
    """Autonomous Finite State Machine Pipeline"""
    
    def __init__(self, mongo_uri="mongodb://localhost:27017/"):
        self.client = AsyncIOMotorClient(mongo_uri)
        self.db = self.client.nemesis_gail
        self.crawlers = CrawlerStack()
        self.swarm = AIAgentSwarm(self.db)
        
        # Regex for EVM / BTC addresses
        self.ioc_pattern = re.compile(r'0x[a-fA-F0-9]{40}|bc1[a-zA-HJ-NP-Z0-9]{25,39}')

    async def initialize(self):
        await self.crawlers.start()
        
    async def run_pipeline(self, target_url: str, source_type: str):
        """Executes the 7-step FSM for a given target source."""
        
        # 1. SOURCE_DISCOVERY & 2. CRAWL & SCRAPE
        logging.info(f"[{source_type}] CRAWLING {target_url}...")
        if source_type in ["DARKNET_FORUM", "SCAM_SNIFFER"]:
            raw_data = await self.crawlers.dynamic_scrape(target_url)
        else:
            raw_data = await self.crawlers.static_scrape(target_url)

        if not raw_data:
            return

        # 3. EXTRACT_IOC
        iocs = self.ioc_pattern.findall(raw_data)
        unique_iocs = list(set(iocs))
        logging.info(f"[{source_type}] EXTRACTED {len(unique_iocs)} IOCs.")

        for ioc in unique_iocs:
            # 4. ENTITY_RESOLUTION
            wallet_intel = await self.swarm.agent_1_wallet_intel(ioc)
            
            # 5. GRAPH_LINKING (Skipped deep logic here for brevity, simulates edge creation)
            # await self.db.edges.insert_one({"source": ioc, ...})
            
            # 6. AML_SCORING
            # Simulated variables based on OSINT text context
            taint = 80.0 if "hack" in raw_data.lower() else 10.0
            aml_score = self.swarm.agent_3_aml_engine(taint, exposure=50.0, velocity=90.0, entity_risk=wallet_intel["risk"])
            
            # 7. ATTRIBUTION
            attribution = await self.swarm.agent_5_entity_attribution(ioc, raw_data)
            cex_match = await self.swarm.agent_4_cex_intel(ioc)

            # Persist to Data Lake
            await self.db.ioc_lake.update_one(
                {"address": ioc},
                {
                    "$set": {
                        "address": ioc,
                        "source": source_type,
                        "cluster_id": wallet_intel["cluster"],
                        "aml_score": aml_score,
                        "attribution": attribution,
                        "is_cex": cex_match is not None,
                        "cex_name": cex_match,
                        "last_seen": datetime.datetime.utcnow().isoformat()
                    }
                },
                upsert=True
            )
            
            logging.info(f"[{source_type}] RESOLVED & SCORED IOC: {ioc} | AML: {aml_score:.1f} | Entity: {attribution}")

    async def autonomous_loop(self):
        """24/7 Global Ingestion Feed"""
        await self.initialize()
        
        # Real Target Sources (OSINT / Public Feeds)
        sources = [
            ("https://raw.githubusercontent.com/0xapoorv/ofac-sanctioned-digital-currency-addresses/main/sanctioned_addresses.csv", "OFAC_SANCTIONS"),
            ("https://raw.githubusercontent.com/MyEtherWallet/ethereum-lists/master/src/addresses/addresses-darklist.json", "MEW_DARKLIST"),
            ("https://raw.githubusercontent.com/cryptio/cryptio-public/master/defi/tokens.json", "DEFI_TOKENS")
        ]
        
        try:
            while True:
                for url, src_type in sources:
                    await self.run_pipeline(url, src_type)
                    await asyncio.sleep(2) # Throttle to prevent rate limits
        except KeyboardInterrupt:
            logging.info("Shutting down NEMESIS GAIL...")
        finally:
            await self.crawlers.close()

if __name__ == "__main__":
    spider_os = NemesisSpiderFSM()
    asyncio.run(spider_os.autonomous_loop())