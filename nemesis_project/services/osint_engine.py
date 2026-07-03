import asyncio
import logging
import re
import urllib.parse
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

logger = logging.getLogger("NemesisOSINT.Engine")

class OSINTEngine:
    """
    Global OSINT Intelligence Pipeline for Wallet Entity Resolution.
    Crawls search engines, GitHub, X (Twitter), and forums using Dorks.
    """
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
        self.semaphore = asyncio.Semaphore(2) # Max 2 concurrent heavy OSINT crawls
        
        self.SEARCH_ENGINES = {
            "DUCKDUCKGO": "https://html.duckduckgo.com/html/?q={query}",
            "BING": "https://www.bing.com/search?q={query}"
        }
        
        # Regex patterns for intelligence extraction
        self.PATTERNS = {
            "TWITTER": r"(?:twitter\.com|x\.com)/([a-zA-Z0-9_]{1,15})",
            "GITHUB": r"github\.com/([a-zA-Z0-9_-]+)(?:/[a-zA-Z0-9_-]+)?",
            "EMAIL": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
            "TELEGRAM": r"t\.me/([a-zA-Z0-9_]{5,32})",
            "ENS": r"([a-zA-Z0-9-]+\.eth)"
        }

    async def start(self):
        try:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=True,
                args=['--disable-blink-features=AutomationControlled']
            )
            self.context = await self.browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={"width": 1920, "height": 1080}
            )
            logger.info("OSINT Swarm Engine initialized.")
        except Exception as e:
            logger.error(f"Failed to initialize OSINT Engine: {e}")

    async def stop(self):
        if self.context: await self.context.close()
        if self.browser: await self.browser.close()
        if self.playwright: await self.playwright.stop()

    def generate_dorks(self, address: str) -> list:
        """Generates Google/Search dorks for the target wallet."""
        return [
            f'"{address}"',
            f'"{address}" site:github.com',
            f'"{address}" site:x.com OR site:twitter.com',
            f'"{address}" site:reddit.com',
            f'"{address}" scam OR hack OR exploit OR phishing',
            f'"{address}" filetype:pdf OR filetype:txt'
        ]

    async def extract_artifacts(self, text_corpus: str, source_url: str) -> list:
        """Extracts usernames, emails, ENS names from a raw text payload."""
        artifacts = []
        
        for platform, pattern in self.PATTERNS.items():
            matches = re.findall(pattern, text_corpus, re.IGNORECASE)
            for match in set(matches):
                # Filter out false positives
                if match.lower() in ["search", "login", "home", "explore", "status"]: continue
                
                artifacts.append({
                    "type": platform,
                    "value": match,
                    "source": source_url,
                    "evidence_type": "OSINT Extracted"
                })
                
        return artifacts

    async def execute_search(self, dork: str, engine: str = "DUCKDUCKGO") -> list:
        """Executes a dork against a search engine and returns extracted links and snippets."""
        if not self.context: return []
        
        async with self.semaphore:
            page = await self.context.new_page()
            results = []
            try:
                query = urllib.parse.quote_plus(dork)
                url = self.SEARCH_ENGINES[engine].format(query=query)
                logger.info(f"[OSINT] Executing Dork: {dork} on {engine}")
                
                await page.goto(url, wait_until="domcontentloaded", timeout=15000)
                await page.wait_for_timeout(2000) # Anti-bot bypass delay
                
                content = await page.content()
                soup = BeautifulSoup(content, 'html.parser')
                
                if engine == "DUCKDUCKGO":
                    for a in soup.find_all('a', class_='result__url'):
                        link = a.get('href')
                        if link and "duckduckgo" not in link:
                            snippet = a.parent.parent.get_text(separator=" ", strip=True)
                            results.append({"url": link, "snippet": snippet})
                            
                elif engine == "BING":
                    for li in soup.find_all('li', class_='b_algo'):
                        a = li.find('a')
                        if a and a.get('href'):
                            snippet = li.get_text(separator=" ", strip=True)
                            results.append({"url": a.get('href'), "snippet": snippet})
                            
            except Exception as e:
                logger.error(f"[OSINT] Search failed for '{dork}': {e}")
            finally:
                await page.close()
                
            return results

    async def run_full_osint_pipeline(self, address: str) -> dict:
        """
        Runs the full intelligence pipeline: searches, artifact extraction, and correlation prep.
        """
        dorks = self.generate_dorks(address)
        master_results = {
            "address": address,
            "raw_mentions": [],
            "artifacts": [],
            "domains": set(),
            "status": "completed"
        }
        
        # We will only run the first 3 highly targeted dorks to prevent rate-limiting in production default
        tasks = [self.execute_search(d, "DUCKDUCKGO") for d in dorks[:3]]
        search_results_list = await asyncio.gather(*tasks, return_exceptions=True)
        
        combined_text_corpus = ""
        
        for search_results in search_results_list:
            if isinstance(search_results, Exception): continue
            
            for res in search_results:
                master_results["raw_mentions"].append(res)
                master_results["domains"].add(urllib.parse.urlparse(res["url"]).netloc)
                combined_text_corpus += " " + res["snippet"]
                
        # Extract identities
        master_results["artifacts"] = await self.extract_artifacts(combined_text_corpus, "Search Engine Aggregation")
        master_results["domains"] = list(master_results["domains"])
        
        return master_results

osint_engine = OSINTEngine()
