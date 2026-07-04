import os
os.environ["PLAYWRIGHT_BROWSERS_PATH"] = "0"
import asyncio
import re
import logging
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

logger = logging.getLogger("OmniChainEngine.Scraper")

# Keywords to classify wallets
BEHAVIOR_KEYWORDS = {
    "MIXER": ["mixer", "tornado", "coinjoin", "blender", "tumbler", "mixing"],
    "CEX": ["exchange", "binance", "coinbase", "kraken", "kucoin", "okx", "huobi", "bybit", "cex", "custodial", "hot wallet", "cold wallet"],
    "DEX": ["dex", "uniswap", "sushiswap", "pancakeswap", "curve", "swap", "1inch", "amm", "liquidity"],
    "DEFI": ["defi", "lending", "aave", "compound", "maker", "yield", "vault", "staking"],
    "BRIDGE": ["bridge", "portal", "wormhole", "multichain", "layerzero", "hop", "stargate", "wrapped", "wrap", "unwrap"],
    "DARKNET": ["darknet", "silk road", "hydra", "black market", "sanctioned", "ofac", "blacklisted", "scam", "phishing", "hack", "exploiter"],
}

# Universal EVM Explorer Endpoints
EXPLORER_REGISTRY = {
    "ETHEREUM": "https://etherscan.io",
    "ETH": "https://etherscan.io",
    "BASE": "https://basescan.org",
    "ARBITRUM": "https://arbiscan.io",
    "OPTIMISM": "https://optimistic.etherscan.io",
    "POLYGON": "https://polygonscan.com",
    "BSC": "https://bscscan.com",
    "AVALANCHE": "https://snowtrace.io",
    "FANTOM": "https://ftmscan.com",
    "SONIC": "https://sonicscan.org",
    "SCROLL": "https://scrollscan.com",
    "LINEA": "https://lineascan.build",
    "BLAST": "https://blastscan.io",
    "MANTLE": "https://mantlescan.xyz",
    "CRONOS": "https://cronoscan.com",
    "GNOSIS": "https://gnosisscan.io"
}

class AutoScraper:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
        self.swarm_semaphore = asyncio.Semaphore(3) # Max 3 concurrent Playwright tabs to prevent OOM
        
    async def start(self):
        try:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=True,
                args=['--log-level=3', '--disable-logging']
            )
            self.context = await self.browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
            )
            logger.info("Playwright Auto-Scraper initialized.")
        except Exception as e:
            logger.error(f"Failed to initialize Playwright: {e}. Please ensure 'playwright install chromium' has been run.")

    async def stop(self):
        if self.context: await self.context.close()
        if self.browser: await self.browser.close()
        if self.playwright: await self.playwright.stop()
            
    def _classify_text(self, text: str) -> tuple:
        """Takes a blob of text from a block explorer and returns a cluster/label based on keywords."""
        if not text:
            return None, None
            
        text = text.lower()
        found_cluster = None
        found_label = None
        
        # Look for explicit names if we can extract them, otherwise just classify
        for cluster, keywords in BEHAVIOR_KEYWORDS.items():
            for kw in keywords:
                if kw in text:
                    found_cluster = cluster
                    # Attempt to find a capitalized word near the keyword as the label
                    # Simplified: just use the keyword as a starting point
                    found_label = kw.title() + " " + cluster
                    # Specific overrides for well-known exchanges
                    if "binance" in text: found_label = "Binance"
                    if "coinbase" in text: found_label = "Coinbase"
                    if "kraken" in text: found_label = "Kraken"
                    if "tornado" in text: found_label = "Tornado Cash"
                    break
            if found_cluster:
                break
                
        return found_label, found_cluster

    async def scrape_ethplorer(self, address: str) -> tuple:
        """Scrape Ethplorer for Ethereum addresses."""
        if not self.context: return None, None
        page = await self.context.new_page()
        try:
            url = f"https://ethplorer.io/search/{address}"
            await page.goto(url, wait_until="domcontentloaded", timeout=20000)
            await page.wait_for_timeout(3000) # Wait for React router
            content = await page.content()
            
            soup = BeautifulSoup(content, 'html.parser')
            tags = []
            # Extract common tag containers
            for tag in soup.find_all('div', class_=lambda x: x and 'tag' in x.lower()):
                tags.append(tag.get_text(separator=' ', strip=True))
            for tag in soup.find_all('a', class_=lambda x: x and 'label' in x.lower()):
                tags.append(tag.get_text(separator=' ', strip=True))
                
            text_blob = " | ".join(tags) + " " + soup.get_text()
            return self._classify_text(text_blob)
        except Exception as e:
            logger.error(f"Ethplorer scrape failed for {address}: {e}")
            return None, None
        finally:
            await page.close()

    async def scrape_blockscan(self, address: str) -> tuple:
        """Scrape Blockscan for multi-EVM addresses."""
        if not self.context: return None, None
        page = await self.context.new_page()
        try:
            url = f"https://blockscan.com/address/{address}"
            await page.goto(url, wait_until="domcontentloaded", timeout=15000)
            await page.wait_for_timeout(2000) # Let react render
            content = await page.content()
            
            soup = BeautifulSoup(content, 'html.parser')
            tags = []
            for tag in soup.find_all(['span', 'a'], class_=lambda x: x and ('badge' in x.lower() or 'label' in x.lower() or 'btn' in x.lower())):
                tags.append(tag.get_text(separator=' ', strip=True))
                
            text_blob = " | ".join(tags) + " " + soup.get_text()
            return self._classify_text(text_blob)
        except Exception as e:
            logger.error(f"Blockscan scrape failed for {address}: {e}")
            return None, None
        finally:
            await page.close()

    async def scrape_oklink(self, address: str, chain: str) -> tuple:
        """Scrape OkLink using specific chain URL."""
        if not self.context: return None, None
        page = await self.context.new_page()
        try:
            chain_map = {
                "ETHEREUM": "eth", "MULTI-EVM": "eth", "EVM_AUTO": "eth", "ETH": "eth",
                "BSC": "bsc", "POLYGON": "polygon", "BASE": "base", 
                "ARBITRUM": "arbitrum", "OPTIMISM": "optimism",
                "BITCOIN": "btc", "SOLANA": "sol", "TRON": "trx", 
                "RIPPLE": "xrp", "STELLAR": "xlm"
            }
            ok_chain = chain_map.get(chain, "eth")
            url = f"https://www.oklink.com/{ok_chain}/address/{address}"
            await page.goto(url, wait_until="domcontentloaded", timeout=15000)
            
            # Wait for network idle to ensure redirects complete before evaluation
            try:
                await page.wait_for_load_state("networkidle", timeout=8000)
            except:
                await page.wait_for_timeout(4000)
                
            btc_gas_price = None
            if ok_chain == "btc":
                try:
                    # Look for the specific bitcoin gas price tooltip requested by the user
                    gas_el = await page.query_selector('.text-ellipsis a span:first-of-type')
                    if gas_el:
                        btc_gas_price = await gas_el.inner_text()
                except Exception as e:
                    logger.warning(f"Could not extract Bitcoin gas price: {e}")
            
            # 2. Extract Tags using fallback selectors for robust scraping
            tags = []
            try:
                tag_locators = await page.locator('.text-ellipsis, div[class*="tag-md"] .text-ellipsis').all()
                for locator in tag_locators:
                    text = await locator.inner_text()
                    clean_text = text.strip().lstrip('#').strip()
                    if clean_text and len(clean_text) > 2 and clean_text not in ["Overview", "Transactions", "Token"]:
                        tags.append(clean_text)
            except Exception as e:
                logger.warning(f"OkLink tag locator failed: {e}")
                
            tags = list(set(tags))
            text_blob = " | ".join(tags)
            
            # Try multi-search layout as well if tags are empty
            if not tags:
                multi_url = f"https://www.oklink.com/multi-search#key={address}"
                try:
                    await page.goto(multi_url, wait_until="domcontentloaded", timeout=10000)
                    await page.wait_for_timeout(3000)
                    multi_content = await page.content()
                    soup = BeautifulSoup(multi_content, 'html.parser')
                    text_blob += " " + soup.get_text()
                except Exception:
                    pass
            
            label, cluster = self._classify_text(text_blob)
            
            # Pack BTC Gas into label if needed
            if btc_gas_price and label:
                label += f" (BTC Gas: {btc_gas_price})"
            elif btc_gas_price and not label:
                label = f"BTC Gas: {btc_gas_price}"
                
            # Prefer extracted tags directly if classification failed
            if not label and tags:
                label = tags[0]
                
            return label, cluster
        except Exception as e:
            logger.error(f"OkLink scrape failed for {address}: {e}")
            return None, None
        finally:
            await page.close()

    async def scrape_solana(self, address: str) -> tuple:
        """Scrape Solscan for Solana addresses."""
        if not self.context: return None, None
        page = await self.context.new_page()
        try:
            url = f"https://solscan.io/account/{address}"
            await page.goto(url, wait_until="domcontentloaded", timeout=15000)
            await page.wait_for_timeout(3000)
            content = await page.content()
            soup = BeautifulSoup(content, 'html.parser')
            
            # Extract badges/labels
            tags = []
            for tag in soup.find_all(['span', 'div'], class_=lambda x: x and ('ant-tag' in x.lower() or 'label' in x.lower())):
                tags.append(tag.get_text(separator=' ', strip=True))
                
            text_blob = " | ".join(tags) + " " + soup.get_text()
            return self._classify_text(text_blob)
        except Exception as e:
            logger.error(f"Solscan scrape failed for {address}: {e}")
            return None, None
        finally:
            await page.close()

    async def scrape_ripple(self, address: str) -> tuple:
        """Scrape Bithomp for Ripple (XRP) addresses."""
        if not self.context: return None, None
        page = await self.context.new_page()
        try:
            url = f"https://bithomp.com/explorer/{address}"
            await page.goto(url, wait_until="domcontentloaded", timeout=15000)
            await page.wait_for_timeout(2000)
            content = await page.content()
            soup = BeautifulSoup(content, 'html.parser')
            
            # Bithomp usually shows known exchanges in a title or alert box
            text_blob = soup.get_text()
            return self._classify_text(text_blob)
        except Exception as e:
            logger.error(f"Bithomp scrape failed for {address}: {e}")
            return None, None
        finally:
            await page.close()

    async def scrape_stellar(self, address: str) -> tuple:
        """Scrape Stellar.expert for Stellar addresses."""
        if not self.context: return None, None
        page = await self.context.new_page()
        try:
            url = f"https://stellar.expert/explorer/public/account/{address}"
            await page.goto(url, wait_until="domcontentloaded", timeout=15000)
            await page.wait_for_timeout(2000)
            content = await page.content()
            soup = BeautifulSoup(content, 'html.parser')
            
            # Look for account tags or warnings
            tags = []
            for tag in soup.find_all(['span', 'div'], class_=lambda x: x and ('account-tag' in x.lower() or 'badge' in x.lower())):
                tags.append(tag.get_text(separator=' ', strip=True))
                
            text_blob = " | ".join(tags) + " " + soup.get_text()
            return self._classify_text(text_blob)
        except Exception as e:
            logger.error(f"StellarExpert scrape failed for {address}: {e}")
            return None, None
        finally:
            await page.close()

    async def resolve_address(self, address: str, chain: str, trace_id: str = None) -> dict:
        """Master resolver that tries applicable block explorers."""
        label, cluster = None, None
        
        # Try Blockscan for EVM chains first as it's the best multichain label aggregator
        if chain in ["ETHEREUM", "MULTI-EVM", "EVM_AUTO", "ETH", "BSC", "POLYGON", "ARBITRUM", "OPTIMISM", "BASE"]:
            label, cluster = await self.scrape_blockscan(address)
        
        # Then try Ethplorer for ETH specifically
        if not label and chain in ["ETHEREUM", "MULTI-EVM", "EVM_AUTO", "ETH"]:
            label, cluster = await self.scrape_ethplorer(address)
            
        # Try Alt-Chain specific scrapers
        if not label:
            if chain == "SOLANA":
                label, cluster = await self.scrape_solana(address)
            elif chain == "RIPPLE":
                label, cluster = await self.scrape_ripple(address)
            elif chain == "STELLAR":
                label, cluster = await self.scrape_stellar(address)
            
        # Fallback or global use OkLink
        if not label:
            label, cluster = await self.scrape_oklink(address, chain)
            
        if label or cluster:
            result = {
                "address": address.lower(),
                "label": label or f"Identified {cluster}",
                "cluster": cluster or "UNKNOWN",
                "source": "Playwright Auto-Scraper"
            }
            
            # Save to Universal Databases immediately
            from services.database_connector import db_connector
            
            # Fire and forget auto-save
            asyncio.create_task(db_connector.save_entity(
                address=address,
                chain=chain,
                label=result["label"],
                cluster=result["cluster"],
                tags=[],
                metadata={"source": result["source"]}
            ))
            
            # Broadcast to active trace websocket
            if trace_id:
                try:
                    from main import active_sessions
                    if trace_id in active_sessions:
                        engine = active_sessions[trace_id]
                        # Broadcast LABEL_UPDATE
                        import json
                        for ws in list(engine.clients):
                            await ws.send_text(json.dumps({
                                "type": "LABEL_UPDATE",
                                "address": address.lower(),
                                "label": result["label"],
                                "cluster": result["cluster"]
                            }))
                except Exception as e:
                    logger.error(f"Failed to broadcast label update: {e}")
                    
            return result
        return None

    async def universal_deep_scrape(self, address: str, chain: str = "ETHEREUM", max_pages: int = 5) -> dict:
        """Deep scrape of EVM explorers for granular parsing using parallel swarm logic."""
        if not self.context: return {"error": "Scraper not initialized"}
        
        # Resolve Base URL
        base_url = EXPLORER_REGISTRY.get(chain.upper(), "https://etherscan.io")
        
        result = {
            "address": address.lower(),
            "assets": [],
            "analytics": {},
            "transactions": [],
            "internal_transactions": [],
            "erc20_transfers": [],
            "eip7702_authorizations": [],
            "events": [],
            "cards": []
        }
        
        async with self.swarm_semaphore: # Bound concurrent Playwright tabs
            page = await self.context.new_page()
            try:
                url = f"{base_url}/address/{address}"
                logger.info(f"[DEEP SCRAPE] Swarm Agent hitting {url}")
                try:
                    await page.goto(url, wait_until="domcontentloaded", timeout=25000)
                    await page.wait_for_timeout(4000) # Wait for Cloudflare/React
                except Exception as e:
                    logger.error(f"[DEEP SCRAPE] Failed to load {url}: {e}")
                    return result
            
                # 1. Assets / Portfolio Extraction
                logger.info(f"[DEEP SCRAPE] Extracting Assets for {address}")
                try:
                    assets = await page.evaluate('''() => {
                        let items = document.querySelectorAll('ul#availableBalanceDropdown li, .list-custom-ERC20 a');
                        return Array.from(items).map(item => item.innerText.replace(/\\n/g, ' ').trim()).filter(x => x && !x.includes('Click to view'));
                    }''')
                    result["assets"] = assets
                except Exception as e:
                    logger.warning(f"Could not extract assets: {e}")

                # 2. Analytics Tab summary
                try:
                    stats = await page.evaluate('''() => {
                        let balance = document.querySelector('#ContentPlaceHolder1_divSummary div:contains("ETH Balance")')?.nextElementSibling?.innerText || '';
                        let value = document.querySelector('#ContentPlaceHolder1_divSummary div:contains("ETH Value")')?.nextElementSibling?.innerText || '';
                        return { balance: balance.trim(), value: value.trim() };
                    }''')
                    result["analytics"] = stats
                except:
                    pass

                # Helper for pagination scraping on tabs
                async def scrape_tab_table(tab_selector, iframe_id=None, row_selector='tbody tr', max_p=1):
                    data = []
                    try:
                        # Click tab if needed
                        if tab_selector:
                            await page.click(tab_selector)
                            await page.wait_for_timeout(2000)
                    
                        target_frame = page
                        if iframe_id:
                            frame_element = await page.query_selector(f"iframe#{iframe_id}")
                            if frame_element:
                                target_frame = await frame_element.content_frame()
                                await target_frame.wait_for_load_state("domcontentloaded")
                                await page.wait_for_timeout(2000)

                        for p in range(max_p):
                            rows = await target_frame.evaluate(f'''() => {{
                                let rs = document.querySelectorAll('{row_selector}');
                                return Array.from(rs).map(row => {{
                                    let cols = Array.from(row.querySelectorAll('td'));
                                    return cols.map(c => c.innerText.trim());
                                }}).filter(r => r.length > 0);
                            }}''')
                            data.extend(rows)
                        
                            # Try to click next
                            next_btn = await target_frame.query_selector('a:has-text("Next"), button:has-text("Next"), .page-link:has-text("Next")')
                            if next_btn:
                                is_disabled = await target_frame.evaluate('(btn) => btn.classList.contains("disabled") || (btn.parentElement && btn.parentElement.classList.contains("disabled")) || btn.hasAttribute("disabled")', next_btn)
                                if is_disabled: break
                                try:
                                    await next_btn.click(timeout=5000)
                                    await page.wait_for_timeout(2000)
                                except:
                                    break
                            else:
                                break
                    except Exception as e:
                        logger.warning(f"Pagination scrape failed for {tab_selector}: {e}")
                    return data

                # 3. Normal Transactions
                logger.info(f"[DEEP SCRAPE] Extracting Normal Transactions")
                txs = await scrape_tab_table('#transactions', iframe_id='toxmaintab', max_p=max_pages)
                result["transactions"] = txs
            
                # 4. Internal Transactions
                logger.info(f"[DEEP SCRAPE] Extracting Internal Transactions")
                int_txs = await scrape_tab_table('a#internal-txs-tab', iframe_id='toxmaintab', max_p=max_pages)
                result["internal_transactions"] = int_txs
            
                # 5. ERC-20 Token Transfers
                logger.info(f"[DEEP SCRAPE] Extracting ERC-20 Transfers")
                erc20 = await scrape_tab_table('a#erc20-tokens-tab', iframe_id='toxmaintab', max_p=max_pages)
                result["erc20_transfers"] = erc20

                # 6. Authorizations (EIP-7702)
                logger.info(f"[DEEP SCRAPE] Extracting EIP-7702 Authorizations")
                eip7702 = await scrape_tab_table('a#authorizations-tab', iframe_id='toxmaintab', max_p=1)
                result["eip7702_authorizations"] = eip7702
            
                # 7. Events
                logger.info(f"[DEEP SCRAPE] Extracting Events")
                events = await scrape_tab_table('a#events-tab', iframe_id='toxmaintab', max_p=max_pages)
                result["events"] = events
            
            except Exception as e:
                logger.error(f"Deep scrape failed for {address}: {e}")
                result["error"] = str(e)
            finally:
                await page.close()
            
        logger.info(f"[DEEP SCRAPE] Completed for {address}")
        return result

# Global Singleton Scraper
scraper_instance = AutoScraper()
