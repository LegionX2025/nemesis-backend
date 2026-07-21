import asyncio
import logging
import json
import re
import aiohttp
from bs4 import BeautifulSoup
from datetime import datetime
from services.database_connector import db_engine
import urllib.parse

logger = logging.getLogger("NemesisThreatIntel")

class ThreatIntelEngine:
    def __init__(self):
        self.db = None
        self.session = None

    async def init_db(self):
        if not self.db:
            await db_engine.connect()
            if db_engine.db is not None:
                self.db = db_engine.db
            else:
                self.db = None
                logger.warning("[THREAT_INTEL] Database is offline. Running in memory-only mode.")

    async def _get_session(self):
        if not self.session:
            self.session = aiohttp.ClientSession(headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
            })
        return self.session

    async def fetch_cftc_red_list(self):
        """Scrapes the CFTC RED (Registration Deficient) List"""
        logger.info("[THREAT_INTEL] Fetching CFTC RED List...")
        try:
            session = await self._get_session()
            async with session.get("https://www.cftc.gov/cftc-red-list") as resp:
                if resp.status == 200:
                    html = await resp.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    tables = soup.find_all('table')
                    records = []
                    for table in tables:
                        for row in table.find_all('tr')[1:]:
                            cols = row.find_all('td')
                            if len(cols) >= 2:
                                name = cols[0].get_text(strip=True)
                                website = cols[1].get_text(strip=True)
                                records.append({
                                    "source": "CFTC",
                                    "entity_name": name,
                                    "website": website,
                                    "severity": "HIGH",
                                    "tags": ["Unregistered Foreign Entity", "CFTC RED List"],
                                    "ingested_at": datetime.utcnow().isoformat()
                                })
                    
                    if records:
                        if self.db:
                            await self.db.threat_intel.delete_many({"source": "CFTC"})
                            await self.db.threat_intel.insert_many(records)
                            logger.info(f"[THREAT_INTEL] Ingested {len(records)} CFTC RED List records.")
                        else:
                            logger.info(f"[THREAT_INTEL] Memory Mode: {len(records)} CFTC RED List records found (Not Saved).")
                else:
                    logger.warning(f"[THREAT_INTEL] CFTC fetch failed: HTTP {resp.status}")
        except Exception as e:
            logger.error(f"[THREAT_INTEL] CFTC Scraper Error: {e}")

    async def fetch_sec_press_releases(self):
        """Scrapes recent SEC crypto-related enforcement actions"""
        logger.info("[THREAT_INTEL] Fetching SEC Enforcement Actions...")
        try:
            session = await self._get_session()
            async with session.get("https://www.sec.gov/news/pressreleases") as resp:
                if resp.status == 200:
                    html = await resp.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    records = []
                    for tr in soup.find_all('tr'):
                        text = tr.get_text(strip=True).lower()
                        if "crypto" in text or "bitcoin" in text or "fraud" in text or "unregistered" in text:
                            title_a = tr.find('a')
                            if title_a:
                                title = title_a.get_text(strip=True)
                                link = "https://www.sec.gov" + title_a.get('href', '')
                                
                                # Basic NLP to extract capitalized entity names (heuristic)
                                entities = re.findall(r'([A-Z][a-z]+(?:\s[A-Z][a-z]+)+)', title)
                                if "SEC" in entities: entities.remove("SEC")
                                
                                for ent in entities:
                                    records.append({
                                        "source": "SEC",
                                        "entity_name": ent,
                                        "description": title,
                                        "url": link,
                                        "severity": "HIGH",
                                        "tags": ["SEC Enforcement Action", "Regulatory"],
                                        "ingested_at": datetime.utcnow().isoformat()
                                    })
                    if records:
                        # De-duplicate by entity name
                        unique_records = {r['entity_name']: r for r in records}.values()
                        if self.db:
                            await self.db.threat_intel.insert_many(list(unique_records))
                            logger.info(f"[THREAT_INTEL] Ingested {len(unique_records)} SEC Entity flags.")
                        else:
                            logger.info(f"[THREAT_INTEL] Memory Mode: {len(unique_records)} SEC Entity flags found (Not Saved).")
        except Exception as e:
            logger.error(f"[THREAT_INTEL] SEC Scraper Error: {e}")

    async def fetch_crypto_iocs(self):
        """Fetches Open Source Crypto IoCs (Indicators of Compromise)"""
        logger.info("[THREAT_INTEL] Fetching Open Source Crypto IoCs...")
        try:
            session = await self._get_session()
            url = "https://raw.githubusercontent.com/cryptio/crypto-hacks/master/data/hacks.json"
            async with session.get(url) as resp:
                if resp.status == 200:
                    try:
                        data = await resp.json(content_type=None)
                        records = []
                        for hack in data:
                            target = hack.get('target', 'Unknown Entity')
                            addresses = hack.get('addresses', [])
                            for address in addresses:
                                records.append({
                                    "source": "GITHUB_IOC",
                                    "crypto_address": address.lower(),
                                    "entity_name": f"{target} Hacker",
                                    "description": hack.get('description', 'Known Crypto Hack'),
                                    "severity": "CRITICAL",
                                    "tags": ["HACK", "IOC", "STOLEN FUNDS"],
                                    "ingested_at": datetime.utcnow().isoformat()
                                })
                        if records:
                            if self.db:
                                await self.db.threat_intel.delete_many({"source": "GITHUB_IOC"})
                                await self.db.threat_intel.insert_many(records)
                                logger.info(f"[THREAT_INTEL] Ingested {len(records)} Crypto IoC addresses.")
                            else:
                                logger.info(f"[THREAT_INTEL] Memory Mode: {len(records)} Crypto IoC addresses found (Not Saved).")
                    except json.JSONDecodeError:
                        pass
        except Exception as e:
            logger.error(f"[THREAT_INTEL] IoC Scraper Error: {e}")

    async def fetch_ofac_sanctions(self):
        """Fetches US Treasury OFAC SDN List (Crypto Addresses subset)"""
        logger.info("[THREAT_INTEL] Fetching OFAC/OpenSanctions Crypto Addresses...")
        try:
            session = await self._get_session()
            url = "https://raw.githubusercontent.com/0xfoobar/ofac-sanctions-list/main/sanctioned_addresses.json"
            async with session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.json(content_type=None)
                    records = []
                    for address in data:
                        records.append({
                            "source": "OFAC",
                            "crypto_address": address.lower(),
                            "entity_name": "OFAC Sanctioned Entity",
                            "severity": "CRITICAL",
                            "tags": ["OFAC", "SANCTIONED", "BLOCKED"],
                            "ingested_at": datetime.utcnow().isoformat()
                        })
                    if records:
                        if self.db:
                            await self.db.threat_intel.delete_many({"source": "OFAC"})
                            await self.db.threat_intel.insert_many(records)
                            logger.info(f"[THREAT_INTEL] Ingested {len(records)} OFAC sanctioned addresses.")
                        else:
                            logger.info(f"[THREAT_INTEL] Memory Mode: {len(records)} OFAC sanctioned addresses found (Not Saved).")
        except Exception as e:
            logger.error(f"[THREAT_INTEL] OFAC Scraper Error: {e}")
            
    async def fetch_opencorporates_intel(self, entity_name: str) -> dict:
        """On-demand OpenCorporates lookup"""
        try:
            session = await self._get_session()
            query = urllib.parse.quote_plus(entity_name)
            url = f"https://opencorporates.com/companies?q={query}"
            async with session.get(url) as resp:
                if resp.status == 200:
                    html = await resp.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    results = soup.find('ul', class_='companies')
                    if results:
                        first_hit = results.find('li', class_='company_search_result')
                        if first_hit:
                            company_name = first_hit.find('a', class_='company_search_result').get_text(strip=True)
                            jurisdiction = first_hit.find('span', class_='jurisdiction').get_text(strip=True)
                            status_el = first_hit.find('span', class_='status')
                            status = status_el.get_text(strip=True) if status_el else "Unknown"
                            return {
                                "found": True,
                                "name": company_name,
                                "jurisdiction": jurisdiction,
                                "status": status,
                                "source_url": url
                            }
            return {"found": False}
        except Exception as e:
            logger.error(f"[THREAT_INTEL] OpenCorporates Query Error: {e}")
            return {"found": False, "error": str(e)}

    async def run_ingestion_cycle(self):
        """Master function to run all automated scrapers."""
        logger.info("=====================================================")
        logger.info(" 🛡️ NEMESIS THREAT INTEL ENGINE: INGESTION INITIATED")
        logger.info("=====================================================")
        await self.init_db()
        
        await asyncio.gather(
            self.fetch_cftc_red_list(),
            self.fetch_sec_press_releases(),
            self.fetch_crypto_iocs(),
            self.fetch_ofac_sanctions()
        )
        
        logger.info("=====================================================")
        logger.info(" ✅ NEMESIS THREAT INTEL ENGINE: INGESTION COMPLETE")
        logger.info("=====================================================")

threat_intel_engine = ThreatIntelEngine()
