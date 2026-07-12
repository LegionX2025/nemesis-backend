import asyncio
from playwright.async_api import async_playwright

async def scrape_corporate_intel(wallet_address: str, chain: str = "ETHEREUM") -> dict:
    if chain.upper() != "ETHEREUM":
        return {"status": "error", "message": "Corporate Intelligence scraping currently supported only for EVM/Ethereum."}
        
    url = f"https://etherscan.io/token/{wallet_address}"
    intel_data = {
        "status": "success",
        "name": "Unknown Token",
        "contract": wallet_address,
        "total_supply": "Unknown",
        "issuer": "Unknown",
        "official_site": "",
        "links": []
    }
    
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            # Navigate to token page
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            
            # Token Name
            try:
                name_el = await page.query_selector("h1 .text-break")
                if name_el:
                    intel_data["name"] = (await name_el.inner_text()).strip()
            except: pass
            
            # Issuer
            try:
                issuer_el = await page.query_selector("span.hash-tag.text-truncate")
                if issuer_el:
                    intel_data["issuer"] = (await issuer_el.inner_text()).strip()
            except: pass
            
            # Total Supply
            try:
                supply_text = await page.evaluate('''() => {
                    const elements = Array.from(document.querySelectorAll('div, span, p'));
                    for (let el of elements) {
                        if (el.innerText && el.innerText.includes('Total Supply:') && el.innerText.length < 100) {
                            return el.innerText.replace('Total Supply:', '').trim();
                        }
                    }
                    return 'Unknown';
                }''')
                intel_data["total_supply"] = supply_text
            except: pass
            
            # Links
            try:
                dropdown_selector = "ul.dropdown-menu.show"
                # Need to click the more button to show the dropdown if it's hidden
                more_btn = await page.query_selector("#dropdownMore2")
                if more_btn:
                    await more_btn.click()
                    await page.wait_for_selector(dropdown_selector, timeout=5000)
                    
                items = await page.eval_on_selector_all(f"{dropdown_selector} li a", '''elements => {
                    return elements.map(el => ({
                        label: el.innerText.trim(),
                        url: el.href
                    })).filter(item => item.label !== "");
                }''')
                intel_data["links"] = items
                
                # Extract official site from links if possible
                for item in items:
                    if "Website" in item["label"] or "Site" in item["label"] or item["url"].startswith("http"):
                        if "etherscan" not in item["url"].lower() and "coinmarketcap" not in item["url"].lower() and "coingecko" not in item["url"].lower():
                            intel_data["official_site"] = item["url"]
                            break
            except: pass
            
            await browser.close()
            
    except Exception as e:
        intel_data["status"] = "error"
        intel_data["message"] = str(e)
        
    if "Total Supply:" in intel_data["total_supply"]:
         intel_data["total_supply"] = intel_data["total_supply"].replace("Total Supply:\n", "").strip()
         
    return intel_data

if __name__ == "__main__":
    import json
    async def test():
        res = await scrape_corporate_intel("0xa0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48")
        print(json.dumps(res, indent=2))
    asyncio.run(test())
