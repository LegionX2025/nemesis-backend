import os
import asyncio
import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from playwright_stealth import stealth

logger = logging.getLogger("OmniScraper")
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Nemesis Omni-Scraper")

class ScrapeRequest(BaseModel):
    address: str
    chain: str = "ETHEREUM"
    max_pages: int = 5

class ScraperEngine:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
        self.semaphore = asyncio.Semaphore(3)  # Anti-bot rate limiting / memory limiting

    async def start(self):
        self.playwright = await async_playwright().start()
        # Launch chromium with anti-bot arguments
        self.browser = await self.playwright.chromium.launch(
            headless=True,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-setuid-sandbox'
            ]
        )
        self.context = await self.browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

    async def get_page(self):
        if not self.context:
            await self.start()
        page = await self.context.new_page()
        await stealth(page)
        return page

engine = ScraperEngine()

@app.on_event("startup")
async def on_startup():
    await engine.start()

@app.post("/api/scrape/deep")
async def deep_scrape(req: ScrapeRequest):
    async with engine.semaphore:
        page = await engine.get_page()
        try:
            # We'll just proxy the Blockscan logic here for demo
            url = f"https://blockscan.com/address/{req.address}"
            await page.goto(url, wait_until="domcontentloaded", timeout=25000)
            await page.wait_for_timeout(3000)
            
            content = await page.content()
            soup = BeautifulSoup(content, 'html.parser')
            
            tags = []
            for tag in soup.find_all(['span', 'a'], class_=lambda x: x and ('badge' in x.lower() or 'label' in x.lower() or 'btn' in x.lower())):
                tags.append(tag.get_text(separator=' ', strip=True))
                
            return {
                "address": req.address,
                "chain": req.chain,
                "tags": tags,
                "source": "Playwright Stealth Service"
            }
        except Exception as e:
            logger.error(f"Scrape failed for {req.address}: {e}")
            raise HTTPException(status_code=500, detail=str(e))
        finally:
            await page.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
