from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from playwright.async_api import async_playwright
import asyncio

app = FastAPI(title="NEMESIS OSINT Scraper")

class ScrapeRequest(BaseModel):
    address: str
    chain: str

EXPLORER_DOMAINS = {
    "ETHEREUM": "etherscan.io", "BSC": "bscscan.com", "POLYGON": "polygonscan.com",
    "AVALANCHE": "snowtrace.io", "ARBITRUM": "arbiscan.io", "OPTIMISM": "optimistic.etherscan.io",
    "BASE": "basescan.org", "CELO": "celoscan.io", "LINEA": "lineascan.build",
    "ZKSYNC": "explorer.zksync.io", "SCROLL": "scrollscan.com"
}

@app.post("/scrape_entity")
async def scrape_entity(req: ScrapeRequest):
    domain = EXPLORER_DOMAINS.get(req.chain, "etherscan.io")
    url = f"https://{domain}/address/{req.address}"
    label = None
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"])
        context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        page = await context.new_page()
        
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=15000)
            try:
                title = await page.title()
                if "Just a moment" in title or "Cloudflare" in title: 
                    await page.wait_for_timeout(5000)
            except: pass
            
            tags = set()
            container = page.locator(".d-flex.flex-wrap.align-items-center.gap-1").first
            if await container.count() > 0:
                hashtags = await container.locator(".hash-tag").all_inner_texts()
                badges = await container.locator(".badge").all_inner_texts()
                for item in hashtags + badges:
                    txt = item.strip().replace('\n', ' ')
                    if txt and "Source Code" not in txt and txt != "Txns": tags.add(txt)
            
            if tags: label = " | ".join(list(tags))
        except Exception as e:
            print(f"Scrape error: {e}")
        finally:
            await browser.close()
            
    return {"address": req.address, "label": label}
