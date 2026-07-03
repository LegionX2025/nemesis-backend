import os
import json
import asyncio
import aiohttp
import logging
from playwright.async_api import async_playwright
from datetime import datetime, timezone
import re

logger = logging.getLogger("OKLinkScraper")

class OKLinkScraper:
    def __init__(self, d1_url=None, d1_token=None):
        self.d1_url = d1_url or os.environ.get("D1_WORKER_URL", "https://nemesis-api.legionxgaming2021.workers.dev")
        self.d1_token = d1_token or os.environ.get("D1_WORKER_AUTH_TOKEN", "lgn-stealth-api-key-2026")
        
    async def _post_d1_query(self, query: str, params: list):
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.d1_token}", 
                    "Content-Type": "application/json"
                }
                payload = {"query": query, "params": params}
                async with session.post(f"{self.d1_url}/db-api/query", json=payload, headers=headers, timeout=10) as resp:
                    if resp.status == 200:
                        return await resp.json()
                    else:
                        logger.error(f"D1 POST failed with status {resp.status}: {await resp.text()}")
        except Exception as e:
            logger.error(f"D1 API error: {e}")
        return None

    async def _save_entity(self, address: str, chain: str, tags: list, clustered: list):
        # Prepare data for D1
        addr_lower = address.lower()
        chain_upper = chain.upper()
        entity_id = f"{addr_lower}_{chain_upper}"
        labels_json = json.dumps(tags)
        clustered_json = json.dumps(clustered)
        
        # Upsert query for entities table
        query = """
        INSERT INTO entities (id, address, chain, type, labels, clustered_addresses, source, last_seen) 
        VALUES (?, ?, ?, 'wallet', ?, ?, 'oklink', CURRENT_TIMESTAMP)
        ON CONFLICT(id) DO UPDATE SET 
            labels=excluded.labels, 
            clustered_addresses=excluded.clustered_addresses,
            last_seen=CURRENT_TIMESTAMP
        """
        params = [entity_id, addr_lower, chain_upper, labels_json, clustered_json]
        await self._post_d1_query(query, params)
        logger.info(f"[*] Saved entity {address} to D1.")

    async def scrape_address(self, page, chain: str, address: str):
        url = f"https://www.oklink.com/{chain.lower()}/address/{address}"
        logger.info(f"[*] Targeting: {url}")
        
        tags = []
        clustered = []
        
        try:
            # Navigate to the OKLink address page
            await page.goto(url, wait_until="networkidle", timeout=20000)
            
            # Wait for the tags container to be hydrated in the DOM
            try:
                await page.wait_for_selector('div[class*="tagsList"], div[class*="tag-md"]', timeout=8000)
            except Exception as e:
                logger.warning(f"[!] Timeout waiting for tags list on {address}")
            
            # 1. Chain Name
            try:
                scraped_chain = await page.locator('div[class*="chainName"]').inner_text()
                scraped_chain = scraped_chain.strip()
            except:
                scraped_chain = chain
                
            # 2. Extract Tags
            tag_locators = page.locator('.text-ellipsis, div[class*="tag-md"] .text-ellipsis')
            count = await tag_locators.count()
            
            for i in range(count):
                text = await tag_locators.nth(i).inner_text()
                clean_text = text.lstrip('#').strip()
                if clean_text and len(clean_text) > 2 and clean_text not in ["Overview", "Transactions", "Token"]:
                    tags.append(clean_text)
                    
            tags = list(set(tags))
            
            # 3. Discover Clustered Addresses (Look for related wallet links)
            # Find links that point to other addresses
            link_locators = page.locator('a[href*="/address/0x"]')
            link_count = await link_locators.count()
            
            for i in range(link_count):
                href = await link_locators.nth(i).get_attribute("href")
                if href:
                    match = re.search(r'/address/(0x[a-fA-F0-9]{40})', href)
                    if match:
                        found_addr = match.group(1).lower()
                        if found_addr != address.lower() and found_addr not in clustered:
                            clustered.append(found_addr)
                            
            # Ensure unique clusters up to a limit
            clustered = list(set(clustered))[:50] # Limit to 50 clustered addresses
            
            return {
                "chain": scraped_chain,
                "address": address,
                "tags": tags,
                "clustered": clustered
            }
            
        except Exception as e:
            logger.error(f"[!] Error during scraping {address}: {e}")
            return None

    async def crawl_and_cluster(self, address: str, chain: str, max_depth=1):
        """Recursively scrapes labels and clustered addresses, saving to D1."""
        visited = set()
        queue = [(address, chain, 0)]
        results = []
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            
            while queue:
                curr_addr, curr_chain, depth = queue.pop(0)
                if curr_addr.lower() in visited:
                    continue
                    
                visited.add(curr_addr.lower())
                
                data = await self.scrape_address(page, curr_chain, curr_addr)
                if data:
                    results.append(data)
                    # Save to DB
                    await self._save_entity(curr_addr, curr_chain, data['tags'], data['clustered'])
                    
                    # Add to queue if under max_depth
                    if depth < max_depth:
                        for cluster_addr in data['clustered']:
                            if cluster_addr.lower() not in visited:
                                queue.append((cluster_addr, curr_chain, depth + 1))
                                
            await browser.close()
            
        return results

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    scraper = OKLinkScraper()
    asyncio.run(scraper.crawl_and_cluster("0xd90e2f925da726b50c4ed8d0fb90ad053324f31b", "eth", max_depth=0))
