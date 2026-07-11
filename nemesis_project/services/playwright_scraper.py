import asyncio
import json
import logging
from playwright.async_api import async_playwright
from datetime import datetime, timezone
from config import APP_CONFIG

logger = logging.getLogger("PlaywrightScraper")

import re

class HeadlessExplorerScraper:
    def __init__(self):
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        ]
        
    def _get_explorer_url(self, chain, address):
        mapping = {
            "ETHEREUM": f"https://etherscan.io/address/{address}",
            "BSC": f"https://bscscan.com/address/{address}",
            "POLYGON": f"https://polygonscan.com/address/{address}",
            "TRON": f"https://tronscan.org/#/address/{address}",
            "SOLANA": f"https://solscan.io/account/{address}",
            "BITCOIN": f"https://www.oklink.com/btc/address/{address}"
        }
        return mapping.get(chain.upper(), mapping["ETHEREUM"])

    async def extract_wallet_labels(self, page):
        """
        Resolves entity labels to full wallet addresses from a web interface 
        where addresses are truncated via CSS and labels are in tooltips.
        """
        resolved_entities = {}
        try:
            # Wait for dynamic address containers to populate
            await page.wait_for_selector('[class*="address-"], [class*="text--"]', state="attached", timeout=5000)
            
            # The label wrapper
            label_locators = page.locator('.text-ellipsis')
            count = await label_locators.count()
            
            for i in range(count):
                label_loc = label_locators.nth(i)
                label_text = await label_loc.inner_text()
                
                # Target the address using partial class matches or proximity
                address_locators = page.locator('[class*="address-"], [class*="text--"]').filter(has_text=re.compile(r"^0x", re.IGNORECASE))
                
                if await address_locators.count() > 0:
                    # Hover to expose tooltip if needed
                    # await label_loc.hover()
                    full_address = await address_locators.first.text_content()
                    
                    clean_label = re.sub(r'#', '', label_text).strip()
                    if clean_label and full_address:
                        resolved_entities[full_address] = clean_label
                        logger.info(f"Resolved Entity: {clean_label} -> Address: {full_address}")
                        
        except Exception as e:
            logger.error(f"Failed to extract wallet labels: {e}")
            
        return resolved_entities

    async def scrape_transactions(self, chain, address, max_pages=1):
        """
        Bypasses Cloudflare and parses the DOM to extract transactions
        when APIs fail or rotate out.
        """
        if APP_CONFIG.get("ICF_USE_BROWSER_SCRAPER", "false").lower() != "true":
            logger.warning("Browser scraper disabled in .env")
            return []

        results = []
        url = self._get_explorer_url(chain, address)
        
        logger.info(f"Initiating Playwright stealth scrape for {chain} : {address}")
        
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    user_agent=self.user_agents[0],
                    viewport={'width': 1280, 'height': 800}
                )
                page = await context.new_page()
                
                # Navigate and wait for DOM load
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                await asyncio.sleep(3) # Wait for Cloudflare JS challenge if present
                
                # Attempt to extract any hidden labels on the page
                labels = await self.extract_wallet_labels(page)
                
                try:
                    # Generic selector that might match typical explorer rows
                    rows = await page.query_selector_all("table tbody tr")
                    for row in rows[:50]: # Scrape up to 50 txs per page
                        text = await row.inner_text()
                        cols = text.split('\n')
                        if len(cols) > 3:
                            # Mocking extraction logic
                            raw_to = cols[2] if len(cols) > 2 else "Unknown"
                            # Map to label if discovered
                            mapped_to = labels.get(raw_to, raw_to)
                            
                            results.append({
                                "hash": cols[0][:15] + "...", 
                                "from": address,
                                "to": mapped_to,
                                "value": cols[3] if len(cols) > 3 else "0",
                                "timeStamp": str(int(datetime.now(timezone.utc).timestamp())),
                                "_source": "playwright_dom_scraper"
                            })
                except Exception as e:
                    logger.error(f"DOM parsing failed: {e}")
                
                await browser.close()
        except Exception as e:
            logger.error(f"Playwright failed: {e}")
            
        return results

scraper_engine = HeadlessExplorerScraper()
