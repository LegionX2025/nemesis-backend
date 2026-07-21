import os
os.environ["PLAYWRIGHT_BROWSERS_PATH"] = "0"
import asyncio
import re
import logging
import json
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

# GBEO v3 Taxonomy Mapping
ONTOLOGY_MAP = {
    'exchange': 'Exchange',
    'cex': 'Exchange',
    'dex': 'DEX',
    'bridge': 'Bridge',
    'mev': 'MEV Bot',
    'mixer': 'Privacy Protocol'
}

from app.services.explorer_adapters import ExplorerAdapter

adapter = ExplorerAdapter()

class AutoScraper:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
        
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
        try:
            if self.context: await self.context.close()
            if self.browser: await self.browser.close()
            if self.playwright: await self.playwright.stop()
        except Exception as e:
            msg = str(e)
            if "Connection closed" not in msg and "Target page, context or browser has been closed" not in msg:
                logger.warning(f"Error during playwright teardown: {e}")
            
    def _classify_text(self, text: str) -> tuple:
        """Takes a blob of text from a block explorer and returns a cluster/label based on keywords."""
        if not text:
            return None, None
            
        text_lower = text.lower()
        found_cluster = None
        found_label = None
        
        # Look for explicit names if we can extract them, otherwise just classify
        for cluster, keywords in BEHAVIOR_KEYWORDS.items():
            for kw in keywords:
                if kw in text_lower:
                    found_cluster = cluster
                    # Attempt to find a capitalized word near the keyword as the label
                    # Simplified: just use the keyword as a starting point
                    found_label = kw.title() + " " + cluster
                    # Specific overrides for well-known exchanges
                    if "binance" in text_lower: found_label = "Binance"
                    if "coinbase" in text_lower: found_label = "Coinbase"
                    if "kraken" in text_lower: found_label = "Kraken"
                    if "tornado" in text_lower: found_label = "Tornado Cash"
                    break
            metadata = {"text_blob": text}
        classification = adapter.classify_wallet("UNKNOWN", "UNKNOWN", metadata)
        
        return found_cluster, classification
    async def scrape_ethplorer(self, address: str) -> tuple:
        """Scrape Ethplorer for Ethereum addresses."""
        if not self.context: return None, None
        page = await self.context.new_page()
        try:
            url = f"https://ethplorer.io/search/{address}"
            
            # Anti-bot Headers
            await page.set_extra_http_headers({
                "Accept-Language": "en-US,en;q=0.9",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                "Sec-Ch-Ua": "\"Google Chrome\";v=\"115\", \"Chromium\";v=\"115\", \"Not=A?Brand\";v=\"24\"",
                "Sec-Ch-Ua-Mobile": "?0",
                "Sec-Ch-Ua-Platform": "\"Windows\""
            })
            
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
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

    EXPLORER_URLS = {
        "ETHEREUM": "https://etherscan.io",
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
        "GNOSIS": "https://gnosisscan.io",
        "HARMONY": "https://explorer.harmony.one",
    }

    async def scrape_evm_explorer(self, address: str, chain: str, tab: str = "") -> tuple:
        """Scrape Etherscan-like or Blockscout-like explorers for deep DOM tags."""
        if not self.context: return None, None
        base_url = self.EXPLORER_URLS.get(chain.upper())
        
        if not base_url:
            # Fallback to blockscout if it's an unmapped chain
            base_url = f"https://{chain.lower()}.blockscout.com"
            
        page = await self.context.new_page()
        try:
            # Address + Tab (e.g. #tokentxns or #analytics)
            url = f"{base_url}/address/{address}{tab}"
            
            # Anti-bot Headers
            await page.set_extra_http_headers({
                "Accept-Language": "en-US,en;q=0.9",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                "Sec-Ch-Ua": "\"Google Chrome\";v=\"115\", \"Chromium\";v=\"115\", \"Not=A?Brand\";v=\"24\"",
                "Sec-Ch-Ua-Mobile": "?0",
                "Sec-Ch-Ua-Platform": "\"Windows\""
            })
            
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(3000) # Let React/NextJS render
            
            # Deep DOM Extraction for badges, labels, tooltips and contract tags
            text_blob = await page.evaluate('''() => {
                const elements = Array.from(document.querySelectorAll('.badge, .label, .btn, [data-bs-title], .tooltip, a[href*="labelcloud"]'));
                return elements.map(e => e.textContent.trim()).join(" | ") + " " + document.body.innerText;
            }''')
            
            return self._classify_text(text_blob)
        except Exception as e:
            logger.error(f"{chain} explorer scrape failed for {address}: {e}")
            return None, None
        finally:
            await page.close()

    async def scrape_blockscan(self, address: str) -> tuple:
        """Scrape Blockscan for multi-EVM addresses."""
        if not self.context: return None, None
        page = await self.context.new_page()
        try:
            url = f"https://blockscan.com/address/{address}"
            
            # Anti-bot Headers
            await page.set_extra_http_headers({
                "Accept-Language": "en-US,en;q=0.9",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                "Sec-Ch-Ua": "\"Google Chrome\";v=\"115\", \"Chromium\";v=\"115\", \"Not=A?Brand\";v=\"24\"",
                "Sec-Ch-Ua-Mobile": "?0",
                "Sec-Ch-Ua-Platform": "\"Windows\""
            })
            
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
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
        """Scrape OkLink using GBEO v3 Strategy (API Interception & Multi-Search)."""
        if not self.context: return None, None
        page = await self.context.new_page()
        
        # Intelligence Profile Template
        profile = {
            "@context": "https://nemesis.intelligence/schema",
            "@type": "IntelligenceProfile",
            "subject": { "address": address },
            "attributions": [],
            "cluster_data": None
        }
        
        try:
            chain_map = {
                "ETHEREUM": "eth", "MULTI-EVM": "eth", "EVM_AUTO": "eth", "ETH": "eth",
                "BSC": "bsc", "POLYGON": "polygon", "BASE": "base", 
                "ARBITRUM": "arbitrum", "OPTIMISM": "optimism",
                "BITCOIN": "btc", "SOLANA": "sol", "TRON": "trx", 
                "RIPPLE": "xrp", "STELLAR": "xlm"
            }
            ok_chain = chain_map.get(chain, "eth")
            
            # 1. Setup API Interception for Cluster Data
            async def handle_response(response):
                if 'search/aggregate' in response.url or '/priapi/' in response.url:
                    try:
                        data = await response.json()
                        profile['cluster_data'] = data.get('data') or data
                    except:
                       pass
                        
            page.on('response', handle_response)
            
            # 2. Navigate to Address Page
            url = adapter.get_wallet_url(chain, address, use_intelligence_explorer=True)
            await page.goto(url, wait_until="networkidle", timeout=15000)
            
            # 3. Robust DOM Scraping for Labels
            ui_data = await page.evaluate('''() => {
                const mainLabel = document.querySelector('h1, .tokenName-XSePS')?.innerText.trim() || '';
                const tags = Array.from(document.querySelectorAll('.tagsList-MN1-u .text-ellipsis, [class*="tag"], [class*="label"]'))
                    .map(el => el.innerText.trim());
                return { mainLabel, tags };
            }''')
            
            main_label = ui_data.get('mainLabel', '')
            tags = ui_data.get('tags', [])
            
            # 4. Multi-Search Discovery (Optional but powerful)
            if not main_label and not tags:
                try:
                    multi_url = f"https://www.oklink.com/multi-search#key={address}"
                    await page.goto(multi_url, wait_until="domcontentloaded", timeout=10000)
                    try:
                        await page.wait_for_selector('.home-container', timeout=8000)
                    except:
                        await page.wait_for_timeout(3000)
                        
                    results = await page.evaluate('''() => {
                        const items = Array.from(document.querySelectorAll('.home-container a[href*="/address/"]'));
                        return items.map(item => {
                            const lines = item.innerText.split('\\n').map(s => s.trim()).filter(Boolean);
                            return { label: lines[0], chain: item.href.split('/')[3] };
                        });
                    }''')
                    if results and len(results) > 0:
                        main_label = results[0].get('label', '')
                except:
                    pass
            
            # Normalize to GBEO v3 Classification
            profile["classification"] = adapter.classify_wallet(chain, address, profile)
            
            if main_label or tags:
                profile['attributions'].append({
                    "source": "OKLink",
                    "chain": ok_chain,
                    "label": main_label,
                    "tags": tags,
                    "class": profile["classification"]
                })
            
            # Also use old classifier logic to retain compatibility with graph engine
            legacy_text_blob = f"{main_label} | " + " | ".join(tags)
            legacy_label, legacy_cluster = self._classify_text(legacy_text_blob)
            
            # If our strict ontology found something, use it, otherwise use legacy
            final_label = main_label if main_label else legacy_label
            final_cluster = profile["classification"] if profile["classification"] != 'Unknown' else legacy_cluster
            
            profile['resolved_label'] = final_label
            profile['resolved_cluster'] = final_cluster
            
            return final_label, final_cluster, profile
            
        except Exception as e:
            logger.error(f"OkLink scrape failed for {address}: {e}")
            return None, None, None
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
        """Master resolver that tries applicable block explorers concurrently."""
        label, cluster = None, None
        
        tasks = []
        # Add relevant scrapers based on chain
        if chain in ["ETHEREUM", "MULTI-EVM", "EVM_AUTO", "ETH", "BSC", "POLYGON", "ARBITRUM", "OPTIMISM", "BASE"]:
            tasks.append(self.scrape_blockscan(address))
            if chain in ["ETHEREUM", "MULTI-EVM", "EVM_AUTO", "ETH"]:
                tasks.append(self.scrape_ethplorer(address))
        elif chain == "SOLANA":
            tasks.append(self.scrape_solana(address))
        elif chain == "RIPPLE":
            tasks.append(self.scrape_ripple(address))
        elif chain == "STELLAR":
            tasks.append(self.scrape_stellar(address))
            
        # Always try OKLink as fallback globally
        tasks.append(self.scrape_oklink(address, chain))
        
        # Execute all tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Find the first successful result
        for res in results:
            if isinstance(res, Exception) or res is None:
                continue
            
            # Unpack 2 or 3 elements depending on the scraper
            profile_data = None
            if len(res) == 3:
                lbl, cls, profile_data = res
            else:
                lbl, cls = res
                
            if lbl:
                label = lbl
                cluster = cls
                
                # Auto-save to Intelligence Lake if profile data exists
                if profile_data:
                    from services.intelligence_lake import intelligence_lake
                    intelligence_lake.upsert_profile(address, profile_data)
                    
                break
                
        if label or cluster:
            result = {
                "address": address.lower(),
                "label": label or f"Identified {cluster}",
                "cluster": cluster or "UNKNOWN",
                "source": "Playwright Auto-Scraper"
            }
            
            # Save to MongoDB immediately (Legacy Support)
            from services.trace_engine import mongo_db
            if mongo_db is not None:
                import datetime
                try:
                    await mongo_db.wallet_labels.insert_one(
                        {"address": address.lower(), "label": result["label"], "cluster": result["cluster"], "source": result["source"], "timestamp": datetime.datetime.now(datetime.timezone.utc)}
                    )
                    logger.info(f"Playwright Scraper resolved {address}: {result['label']}")
                except Exception as e:
                    if "duplicate" in str(e).lower() or "e11000" in str(e).lower():
                        pass # We already have it
                    elif "not authorized" in str(e).lower():
                        logger.warning("MongoDB skipped: Database user lacks 'insert' permissions for wallet_labels.")
                    else:
                        logger.error(f"Mongo insert failed in scraper: {e}")
            
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

    async def deep_scrape_etherscan(self, address: str, chain: str = "ETHEREUM", max_pages: int = 5) -> dict:
        """Deep scrape of EVM explorers for granular parsing of Txs, Internal, ERC-20, EIP-7702, and Assets."""
        if not self.context: return {"error": "Scraper not initialized"}
        
        result = {
            "address": address.lower(),
            "chain": chain,
            "assets": [],
            "analytics": {},
            "transactions": [],
            "internal_transactions": [],
            "erc20_transfers": [],
            "eip7702_authorizations": [],
            "events": [],
            "cards": []
        }
        
        url = adapter.get_wallet_url(chain, address)
        page = await self.context.new_page()
        try:
            logger.info(f"[DEEP SCRAPE] Loading {url}")
            await page.goto(url, wait_until="domcontentloaded", timeout=25000)
            await page.wait_for_timeout(4000) # Wait for Cloudflare/React
            
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

            # 2. Analytics Tab summary (if we were to click it, but we can grab overview stats)
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
