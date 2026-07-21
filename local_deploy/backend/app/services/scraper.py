import asyncio
import logging
from playwright.async_api import async_playwright

logger = logging.getLogger(__name__)

async def scrape_etherscan_intel(address: str):
    """
    Scrapes Etherscan for an address to determine entity tags and malicious flags.
    Returns a dictionary of intel data.
    """
    data = {
        "is_malicious": False,
        "osint_data": "No public OSINT tags found.",
        "darknet_data": "Low exposure",
        "entity_name": "Unknown Entity",
        "tags": []
    }
    
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            # Use a typical user agent to avoid basic blocks
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = await context.new_page()
            
            url = f"https://etherscan.io/address/{address}"
            
            # Navigate to the page
            response = await page.goto(url, wait_until="domcontentloaded", timeout=15000)
            
            if response and response.status == 200:
                # 1. Check for malicious alerts (Etherscan uses .alert-danger for warnings)
                try:
                    alert_elements = await page.locator('.alert-danger').all_inner_texts()
                    for alert in alert_elements:
                        alert_lower = alert.lower()
                        if "phish" in alert_lower or "hack" in alert_lower or "scam" in alert_lower or "exploit" in alert_lower:
                            data["is_malicious"] = True
                            data["osint_data"] = "Known Malicious Entity (Flagged by Etherscan)"
                            data["darknet_data"] = "High exposure / Flagged on block explorers"
                            break
                except Exception as e:
                    logger.debug(f"Error checking alerts: {e}")

                # 2. Extract public name tags / labels
                # Etherscan often puts labels in spans with classes like .badge or specific title attributes
                tags = []
                try:
                    # Attempt to find the specific "Public Name Tag" badge
                    name_tags = await page.locator('span[title="Public Name Tag (viewable by anyone)"]').all_inner_texts()
                    if name_tags:
                        tags.extend([t.strip() for t in name_tags if t.strip()])
                    
                    # Also look at regular badges that might be exchange labels
                    badges = await page.locator('a > span.badge').all_inner_texts()
                    if badges:
                        tags.extend([b.strip() for b in badges if b.strip()])
                except Exception as e:
                    logger.debug(f"Error extracting tags: {e}")
                
                # Remove duplicates and empty strings
                tags = list(set(t for t in tags if t))
                
                if tags:
                    data["tags"] = tags
                    data["entity_name"] = tags[0] # Use the most prominent tag as the entity name
                    if not data["is_malicious"]:
                        data["osint_data"] = f"Identified entity tags: {', '.join(tags)}"
            else:
                logger.warning(f"Failed to fetch {url}, status code: {response.status if response else 'None'}")
                
            await browser.close()
    except Exception as e:
        logger.error(f"Playwright scraping error for {address}: {e}")
        
    return data

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        res = asyncio.run(scrape_etherscan_intel(sys.argv[1]))
        import json
        print(json.dumps(res, indent=2))
