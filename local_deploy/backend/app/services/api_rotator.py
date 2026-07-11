import os
import random
import asyncio
import aiohttp
import logging
import itertools
from dotenv import load_dotenv
from playwright.async_api import async_playwright

load_dotenv()
logger = logging.getLogger("ApiRotator")

class ApiRotator:
    def __init__(self):
        self.keys = {
            "ETHERSCAN": os.getenv("ETHERSCAN_API_KEY", "").split(","),
            "BSCSCAN": os.getenv("BSCSCAN_API_KEY", "").split(","),
            "POLYGONSCAN": os.getenv("POLYGONSCAN_API_KEY", "").split(","),
            "ARBISCAN": os.getenv("ARBISCAN_API_KEY", "").split(","),
            "INFURA": os.getenv("INFURA_API_KEY", "").split(","),
            "ALCHEMY": os.getenv("ALCHEMY_API_KEY", "").split(","),
            "ANKR": os.getenv("ANKR_API_KEY", "").split(","),
            "TATUM": os.getenv("TATUM_API_KEY", "").split(","),
            "ETHPLORER": os.getenv("ETHPLORER_API_KEY", "").split(","),
            "BITQUERY": os.getenv("BITQUERY_API_TOKEN", "").split(",")
        }
        
        # Strip empty strings
        for k in self.keys:
            self.keys[k] = [key.strip() for key in self.keys[k] if key.strip()]

        # Proxies
        proxy_string = os.getenv("PROXY_URLS", "")
        self.proxies = [p.strip() for p in proxy_string.split(",")] if proxy_string else []
        self.proxy_cycle = itertools.cycle(self.proxies) if self.proxies else None

        self.endpoints = {
            "ETHEREUM": {
                "api": ["https://api.etherscan.io/v2/api?chainid=1"],
                "rpc": ["https://cloudflare-eth.com", "https://eth.drpc.org", "https://1rpc.io/eth", "https://ethereum.publicnode.com", "https://mainnet.infura.io/v3/{}", "https://eth-mainnet.g.alchemy.com/v2/{}", "https://rpc.ankr.com/eth/{}"]
            },
            "BSC": {
                "api": ["https://api.bscscan.com/api"],
                "rpc": ["https://bsc-dataseed1.defibit.io", "https://bsc-dataseed1.ninicoin.io", "https://bsc.publicnode.com", "https://rpc.ankr.com/bsc/{}"]
            },
            "POLYGON": {
                "api": ["https://api.polygonscan.com/api"],
                "rpc": ["https://polygon-rpc.com", "https://polygon.drpc.org", "https://1rpc.io/matic", "https://polygon-mainnet.infura.io/v3/{}", "https://polygon-mainnet.g.alchemy.com/v2/{}", "https://rpc.ankr.com/polygon/{}"]
            },
            "ARBITRUM": {
                "api": ["https://api.arbiscan.io/api"],
                "rpc": ["https://arb1.arbitrum.io/rpc", "https://arbitrum.drpc.org", "https://1rpc.io/arb", "https://arbitrum-mainnet.infura.io/v3/{}", "https://arb-mainnet.g.alchemy.com/v2/{}", "https://rpc.ankr.com/arbitrum/{}"]
            },
            "BASE": {
                "api": ["https://api.basescan.org/api"],
                "rpc": ["https://mainnet.base.org", "https://base.drpc.org", "https://base.publicnode.com", "https://rpc.ankr.com/base/{}"]
            },
            "OPTIMISM": {
                "api": ["https://api-optimistic.etherscan.io/api"],
                "rpc": ["https://mainnet.optimism.io", "https://optimism.drpc.org", "https://1rpc.io/op", "https://rpc.ankr.com/optimism/{}"]
            }
        }
        
    def get_proxy(self):
        if self.proxy_cycle:
            return next(self.proxy_cycle)
        return None

    def _get_api_key(self, service_name):
        keys = self.keys.get(service_name.upper(), [])
        if keys: return random.choice(keys)
        return None

    def _format_rpc_url(self, url_template):
        if "{}" not in url_template: return url_template
        
        if "infura" in url_template:
            key = self._get_api_key("INFURA")
            return url_template.format(key) if key else None
        if "alchemy" in url_template:
            key = self._get_api_key("ALCHEMY")
            return url_template.format(key) if key else None
        if "ankr" in url_template:
            key = self._get_api_key("ANKR")
            return url_template.format(key) if key else None
        return None

    async def fetch_with_fallback(self, session, url_template, params=None, max_retries=3):
        """Robust GET fetching with API key rotation and proxy rotation."""
        retries = 0
        while retries < max_retries:
            # Hybrid Key Rotation: V2 for ETH, V1 for others
            api_key = None
            if "chainid=1" in url_template: api_key = self._get_api_key("ETHERSCAN")
            elif "bscscan" in url_template: api_key = self._get_api_key("BSCSCAN")
            elif "polygonscan" in url_template: api_key = self._get_api_key("POLYGONSCAN")
            elif "arbiscan" in url_template: api_key = self._get_api_key("ARBISCAN")
            elif "basescan" in url_template: api_key = self._get_api_key("BASESCAN")
            
            if api_key:
                if params is None:
                    params = {}
                params['apikey'] = api_key
            elif params and 'apikey' in params and params['apikey'] is None:
                del params['apikey']
            
            proxy = self.get_proxy()
            try:
                async with session.get(url_template, params=params, proxy=proxy, timeout=10) as r:
                    if r.status == 200:
                        data = await r.json()
                        # Check for rate limiting in Etherscan format
                        if data.get("status") == "0" and "rate limit" in data.get("message", "").lower():
                            logger.warning(f"Rate limited by {url_template}. Rotating key/proxy...")
                            retries += 1
                            await asyncio.sleep(1)
                            continue
                        return data
                    else:
                        retries += 1
                        await asyncio.sleep(1)
            except Exception as e:
                logger.warning(f"Fetch failed: {e}. Retrying...")
                retries += 1
                await asyncio.sleep(1)
                
        return None

    async def fetch_transaction_receipt(self, session, tx_hash, chain="ETHEREUM"):
        """Fetches the transaction receipt containing logs for DeFi/Wrapped correlations using round-robin RPCs."""
        chain = chain.upper()
        rpc_templates = self.endpoints.get(chain, {}).get("rpc", [])
        
        payload = {
            "jsonrpc": "2.0",
            "method": "eth_getTransactionReceipt",
            "params": [tx_hash],
            "id": 1
        }
        
        for rpc_template in rpc_templates:
            rpc_url = self._format_rpc_url(rpc_template)
            if not rpc_url: continue
            
            proxy = self.get_proxy()
            try:
                async with session.post(rpc_url, json=payload, proxy=proxy, timeout=8) as r:
                    if r.status == 200:
                        data = await r.json()
                        if "result" in data and data["result"]:
                            return data["result"].get("logs", [])
            except Exception as e:
                logger.warning(f"RPC failure on {rpc_url}: {e}")
                
        # If all RPC APIs fail, fallback to Playwright Swarm Agent
        logger.warning(f"All RPCs failed for receipt {tx_hash} on {chain}. Orchestrating Swarm Scraper fallback...")
        return await self._playwright_fallback_receipt(tx_hash, chain)

    async def _playwright_fallback_receipt(self, tx_hash, chain):
        # Swarm Agent Scraper fallback
        domain_map = {
            "ETHEREUM": "etherscan.io",
            "BSC": "bscscan.com",
            "POLYGON": "polygonscan.com",
            "ARBITRUM": "arbiscan.io",
            "BASE": "basescan.org"
        }
        domain = domain_map.get(chain, "etherscan.io")
        url = f"https://{domain}/tx/{tx_hash}#eventlog"
        
        logs = []
        try:
            # Inject randomized anti-bot headers and fingerprints here in a real production environment
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    proxy={"server": self.get_proxy()} if self.get_proxy() else None
                )
                page = await context.new_page()
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                
                # Parse logs from DOM
                log_elements = await page.locator(".log-record").all()
                for el in log_elements:
                    try:
                        topic0 = await el.locator(".topic0").inner_text(timeout=2000)
                        logs.append({"topics": [topic0]})
                    except:
                        continue
                        
                await browser.close()
        except Exception as e:
            logger.error(f"Swarm Playwright scraping failed for {url}: {e}")
            
        return logs
        
api_rotator = ApiRotator()
