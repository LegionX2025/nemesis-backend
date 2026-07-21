import os
import sys
import json
from playwright.sync_api import sync_playwright

def scrape_oklink_tags(chain, address):
    url = f"https://www.oklink.com/{chain}/address/{address}"
    print(f"[*] Targeting: {url}")
    
    tags = []
    
    with sync_playwright() as p:
        # Using a Chromium headless browser
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # Intercept API responses to find the structured JSON data if possible
        def handle_response(response):
            # OKLink API usually returns tags in specific endpoints
            if "api/explorer/v1/" in response.url and response.status == 200:
                try:
                    data = response.json()
                    # Check if the response contains tags array
                    if data.get("data") and isinstance(data["data"], list) and len(data["data"]) > 0:
                         if "tags" in data["data"][0] or "label" in data["data"][0]:
                              print(f"[*] Caught API response: {response.url[:60]}...")
                except:
                    pass
        
        page.on("response", handle_response)
        
        try:
            # Navigate to the OKLink address page
            page.goto(url, wait_until="networkidle", timeout=20000)
            
            # Wait for the tags container to be hydrated in the DOM
            try:
                # Based on the user's selector: .tagsList-MN1-u .text-ellipsis
                page.wait_for_selector('div[class*="tagsList"], div[class*="tag-md"]', timeout=8000)
            except Exception as e:
                print("[!] Timeout waiting for tags list. The address might not have tags or the selector changed.")
            
            # Scrape using the universal strategy provided
            # 1. Chain Name
            try:
                scraped_chain = page.locator('div[class*="chainName"]').inner_text().strip()
            except:
                scraped_chain = chain
                
            # 2. Extract Tags using fallback selectors for robust scraping
            tag_locators = page.locator('.text-ellipsis, div[class*="tag-md"] .text-ellipsis')
            
            for i in range(tag_locators.count()):
                text = tag_locators.nth(i).inner_text().strip()
                # Clean the prefix '#' if present
                clean_text = text.lstrip('#').strip()
                # Filter out standard UI elements that might match .text-ellipsis
                if clean_text and len(clean_text) > 2 and clean_text not in ["Overview", "Transactions", "Token"]:
                    tags.append(clean_text)
                    
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
            
            return result
            
        except Exception as e:
             print(f"[!] Error during scraping: {e}")
             return None
        finally:
             browser.close()

if __name__ == "__main__":
    # Test Scenario: Tornado Cash Router on Ethereum
    test_chain = "eth"
    test_address = "0xd90e2f925da726b50c4ed8d0fb90ad053324f31b"
    scrape_oklink_tags(test_chain, test_address)
