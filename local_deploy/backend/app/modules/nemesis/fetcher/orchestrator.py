# nemesis/fetcher/orchestrator.py

import asyncio
import logging
import threading
import sys
import aiohttp
from typing import List, Dict, Optional, Any
from playwright.async_api import async_playwright
from nemesis.core.config import settings
from nemesis.observability.telemetry import tracer, logger, telemetry

EVM_DOMAINS = {
    "ETHEREUM": "api.etherscan.io", "BSC": "api.bscscan.com",
    "POLYGON": "api.polygonscan.com", "ARBITRUM": "api.arbiscan.io",
    "BASE": "api.basescan.org", "AVALANCHE": "api.snowtrace.io",
    "OPTIMISM": "api-optimistic.etherscan.io"
}

class ParallelFetchOrchestrator:
    """
    Advanced Data Acquisition Engine.
    Uses asyncio TaskGroups (Python 3.11+) or asyncio.gather to race 
    stealth Playwright scrapers against public API endpoints.
    """
    def __init__(self):
        self.pw_contexts = []
        self.pw_thread = None
        self.pw_loop = None
        self._session_pool: Optional[aiohttp.ClientSession] = None
        self._rate_limiters: Dict[str, asyncio.Semaphore] = {
            chain: asyncio.Semaphore(5) for chain in EVM_DOMAINS.keys()
        }

    def _start_thread(self):
        ready_event = threading.Event()
        def run_loop():
            if sys.platform == "win32":
                asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
            self.pw_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.pw_loop)
            ready_event.set()
            self.pw_loop.run_forever()
        self.pw_thread = threading.Thread(target=run_loop, daemon=True)
        self.pw_thread.start()
        ready_event.wait()

    async def start_engines(self):
        logger.info("Initializing Stealth Playwright Swarm and Connection Pools...")
        if not self._session_pool:
            connector = aiohttp.TCPConnector(limit=100, keepalive_timeout=300)
            self._session_pool = aiohttp.ClientSession(connector=connector)

        if self.pw_contexts: return
        if self.pw_thread is None: self._start_thread()
        
        async def _init_pw():
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(headless=True)
            for _ in range(2): 
                self.pw_contexts.append(await self.browser.new_context(user_agent="Mozilla/5.0"))
                
        try:
            future = asyncio.run_coroutine_threadsafe(_init_pw(), self.pw_loop)
            await asyncio.wrap_future(future)
            logger.info("Stealth Playwright Swarm Active.")
        except Exception as e:
            logger.error(f"Playwright Swarm Initialization Failed: {e}")

    async def stop_engines(self):
        logger.info("Shutting down Fetcher Engines...")
        if self._session_pool:
            await self._session_pool.close()
            
        if not self.pw_loop: return
        async def _stop_pw():
            for ctx in self.pw_contexts: await ctx.close()
            self.pw_contexts = []
        future = asyncio.run_coroutine_threadsafe(_stop_pw(), self.pw_loop)
        await asyncio.wrap_future(future)

    @tracer.start_as_current_span("fetcher._lane_api")
    async def _lane_api(self, url: str, addr: str, chain: str) -> Optional[List[Dict[str, Any]]]:
        if not self._session_pool: return None
        
        async with self._rate_limiters.get(chain, asyncio.Semaphore(5)):
            try:
                async with self._session_pool.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15) as r:
                    telemetry.prom_api_calls.labels(chain=chain, status=r.status).inc()
                    if r.status == 200:
                        data = await r.json()
                        if data.get("status") == "1": 
                            logger.info(f"⚡ [API LANE] Success for {addr[:8]}...")
                            return data.get("result", [])
                        elif data.get("message") == "No transactions found":
                            return []
            except Exception as e:
                logger.warning(f"⚠️ [API LANE] Error querying node: {e}")
                telemetry.prom_api_calls.labels(chain=chain, status="error").inc()
        return None

    @tracer.start_as_current_span("fetcher._lane_scraper")
    async def _lane_scraper(self, addr: str, chain: str) -> Optional[List[Dict[str, Any]]]:
        if not self.pw_contexts or not self.pw_loop: return None
        
        async def _pw_task():
            import random
            agent = random.choice(self.pw_contexts)
            domain = EVM_DOMAINS.get(chain, "etherscan.io").replace("api.", "")
            url = f"https://{domain}/address/{addr}"
            txs = []
            page = None
            try:
                page = await agent.new_page()
                await page.goto(url, wait_until="domcontentloaded", timeout=15000)
                try:
                    await page.wait_for_selector('table tbody tr', timeout=5000)
                except:
                    content = await page.content()
                    if "There are no matching entries" in content or "0 transactions" in content.lower():
                        return []
                    return None

                extracted = await page.evaluate('''() => {
                    const results = [];
                    document.querySelectorAll("table tbody tr").forEach(r => {
                        let hashLink = r.querySelector('a[href*="/tx/0x"]');
                        if (!hashLink) return;
                        let hash = hashLink.href.split("/tx/")[1].split("?")[0].split("#")[0];
                        let valStr = "0"; let timeStamp = "0";
                        let valMatch = r.innerText.replace(/,/g, '').match(/([0-9]+\\.?[0-9]*)\\s+([A-Z0-9]{2,10})/i);
                        if(valMatch) valStr = valMatch[1];
                        r.querySelectorAll("[data-bs-title], [title]").forEach(node => {
                            let t = node.getAttribute("data-bs-title") || node.getAttribute("title");
                            if (t && t.match(/\\d{4}-\\d{2}-\\d{2}/)) timeStamp = new Date(t).getTime() / 1000;
                        });
                        let isOut = r.innerText.toUpperCase().includes("OUT");
                        let inputData = "0x";
                        let toAddr = "Unknown";
                        if (isOut) {
                            let toLink = r.querySelector('a[href*="/address/0x"]:not([href*="'+window.location.pathname+'"])');
                            if(toLink) toAddr = toLink.href.split("/address/")[1].split("?")[0].split("#")[0];
                        }
                        results.push({hash: hash, is_out: isOut, value: valStr, timeStamp: timeStamp, to: toAddr, input: inputData});
                    });
                    return results;
                }''')
                for t in extracted:
                    if t['is_out'] and float(t['value']) > 0 and t['to'] != "Unknown":
                        txs.append({"hash": t['hash'], "from": addr, "to": t['to'], "value": t['value'], "timeStamp": t['timeStamp'], "input": t['input']})
                logger.info(f"🕷️ [SCRAPER LANE] Extracted {len(txs)} txs via Stealth Chrome.")
                return txs
            except Exception as e: 
                logger.warning(f"⚠️ [SCRAPER LANE] Execution failed: {e}")
                return None
            finally:
                if page: await page.close()
                
        future = asyncio.run_coroutine_threadsafe(_pw_task(), self.pw_loop)
        return await asyncio.wrap_future(future)

    @tracer.start_as_current_span("fetcher.fetch_parallel")
    async def fetch_parallel(self, addr: str, chain: str) -> List[Dict[str, Any]]:
        domain = EVM_DOMAINS.get(chain, "api.etherscan.io")
        api_key = settings.get_api_key(chain)
        api_url = f"https://{domain}/api?module=account&action=txlist&address={addr}&startblock=0&endblock=99999999&page=1&offset=500&sort=desc"
        
        if api_key:
            api_url += f"&apikey={api_key}"
            
        tasks = [
            asyncio.create_task(self._lane_api(api_url, addr, chain)),
            asyncio.create_task(self._lane_scraper(addr, chain))
        ]
        
        while tasks:
            done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED, timeout=15)
            for task in done:
                try:
                    result = task.result()
                    if result is not None: 
                        for p in pending: p.cancel()
                        return result
                except: pass
            
            tasks = list(pending)
            if not tasks: break
            
        return []

# Singleton instance
orchestrator = ParallelFetchOrchestrator()
