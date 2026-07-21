import os
import sys
import json
import asyncio
from playwright.async_api import async_playwright

async def scrape_oklink_tags(chain, address):
    url = f"https://www.oklink.com/{chain}/address/{address}"
    print(f"[*] Targeting: {url}")
    
    tags = []
    
    async with async_playwright() as p:
        # Using a Chromium headless browser
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Intercept API responses to find the structured JSON data if possible
        async def handle_response(response):
            # OKLink API usually returns tags in specific endpoints
            if "api/explorer/v1/" in response.url and response.status == 200:
                try:
                    data = await response.json()
                    # Check if the response contains tags array
                    if data.get("data") and isinstance(data["data"], list) and len(data["data"]) > 0:
                         if "tags" in data["data"][0] or "label" in data["data"][0]:
                              print(f"[*] Caught API response: {response.url[:60]}...")
                except:
                    pass
        
        page.on("response", handle_response)
        
        try:
            # Navigate to the OKLink address page
            await page.goto(url, wait_until="networkidle", timeout=20000)
            
            # Wait for the tags container to be hydrated in the DOM
            try:
                # Based on the user's selector: .tagsList-MN1-u .text-ellipsis
                await page.wait_for_selector('div[class*="tagsList"], div[class*="tag-md"]', timeout=8000)
            except Exception as e:
                print("[!] Timeout waiting for tags list. The address might not have tags or the selector changed.")
            
            # Scrape using the universal strategy provided
            # 1. Chain Name
            try:
                scraped_chain_locator = page.locator('div[class*="chainName"]')
                scraped_chain = await scraped_chain_locator.inner_text()
                scraped_chain = scraped_chain.strip()
            except:
                scraped_chain = chain
                
            # 2. Extract Tags using fallback selectors for robust scraping
            tag_locators = page.locator('.text-ellipsis, div[class*="tag-md"] .text-ellipsis')
            
            count = await tag_locators.count()
            for i in range(count):
                text = await tag_locators.nth(i).inner_text()
                text = text.strip()
                # Clean the prefix '#' if present
                clean_text = text.lstrip('#').strip()
                # Filter out standard UI elements that might match .text-ellipsis
                if clean_text and len(clean_text) > 2 and clean_text not in ["Overview", "Transactions", "Token"]:
                    tags.append(clean_text)
                    
            # 3. Extract Exchange / Entity Information
            # Based on diagnostics: Tag Name DIV, inside span.tagText-Cc7j-
            # Using text-based and hierarchical locators to avoid unstable generated classes.
            try:
                exchange_locators = page.locator('span[class*="tagText"] div')
                ex_count = await exchange_locators.count()
                for i in range(ex_count):
                    ex_text = await exchange_locators.nth(i).inner_text()
                    ex_text = ex_text.strip()
                    # Look for characteristic strings like "Exchange:" or known CEX names if needed
                    if "Exchange:" in ex_text or "Entity:" in ex_text or ". User" in ex_text:
                        # Optional: format the text to just "OKX" or "Exchange: OKX"
                        tags.append(ex_text)
            except Exception as e:
                print(f"[!] Error extracting exchange tags: {e}")
                    
            # Deduplicate tags
            tags = list(set(tags))
            
            result = {
                "chain": scraped_chain,
                "address": address,
                "attributionTags": tags
            }
            
            print("\n" + "="*40)
            print("🚀 OKLINK AUTO-LABEL RESULTS")
            print("="*40)
            print(json.dumps(result, indent=2))
            
            # Write to log file
            log_path = os.path.join(os.path.dirname(__file__), 'output_log.txt')
            with open(log_path, 'w', encoding='utf-8') as f:
                f.write("🚀 OKLINK AUTO-LABEL RESULTS\n")
                f.write(json.dumps(result, indent=2) + "\n")
            print(f"[*] Wrote log to {log_path}")
            
            return result
            
        except Exception as e:
             print(f"[!] Error during scraping: {e}")
             return None
        finally:
             await browser.close()

if __name__ == "__main__":
    # Test Scenario: Tornado Cash Router on Ethereum
    test_chain = "eth"
    test_address = "0xd90e2f925da726b50c4ed8d0fb90ad053324f31b"
    asyncio.run(scrape_oklink_tags(test_chain, test_address))
