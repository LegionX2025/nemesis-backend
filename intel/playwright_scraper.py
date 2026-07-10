import asyncio
import logging
import re
from playwright.async_api import async_playwright

logger = logging.getLogger("NEMESIS.v32.WalletScraper")

class PlaywrightWalletScraper:
    def __init__(self, headless: bool = True):
        self.headless = headless

    async def scrape_entity_labels(self, target_url: str) -> list:
        """
        Navigates to the target block explorer or entity page and resolves 
        truncated wallet addresses and their associated labels.
        """
        results = []
        logger.info(f"Launching Playwright to scrape: {target_url}")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            context = await browser.new_context()
            page = await context.new_page()
            
            try:
                await page.goto(target_url, wait_until="networkidle")
                
                # The label locator is explicitly .text-ellipsis often hidden in a tooltip
                label_locators = page.locator('.text-ellipsis')
                count = await label_locators.count()
                
                for i in range(count):
                    try:
                        # Attempt to hover to force tooltip/address generation if dynamic
                        await label_locators.nth(i).hover(timeout=1000)
                        
                        raw_label = await label_locators.nth(i).inner_text()
                        # Clean up the label (e.g. remove # prefix)
                        clean_label = re.sub(r'^#\s*', '', raw_label).strip()
                        
                        if not clean_label:
                            continue
                            
                        # Locate address via robust partial matching as prescribed
                        # and filter specifically for EVM 0x hashes
                        address_locator = page.locator('[class*="address-"], [class*="text--"]').filter(has_text=re.compile(r'^0x'))
                        
                        # Wait for the address element to ensure async loads complete
                        if await address_locator.count() > 0:
                            raw_address = await address_locator.first.text_content()
                            clean_address = raw_address.strip()
                            
                            results.append({
                                "entity": clean_label,
                                "address": clean_address
                            })
                            logger.info(f"Resolved Entity: {clean_label} -> Address: {clean_address}")
                    
                    except Exception as e:
                        logger.debug(f"Failed to resolve item {i}: {e}")
                        continue
                        
            except Exception as e:
                logger.error(f"Failed to scrape {target_url}: {str(e)}")
            finally:
                await browser.close()
                
        return results

# For testing
if __name__ == "__main__":
    async def test():
        scraper = PlaywrightWalletScraper(headless=True)
        # Pass a mock or actual URL here
        # res = await scraper.scrape_entity_labels("https://etherscan.io/...")
        # print(res)
    
    # asyncio.run(test())
