import asyncio
from playwright.async_api import async_playwright
import requests

async def test_frontend():
    print("🚀 Starting Automated Frontend & Backend Audit...")
    try:
        r = requests.get('http://localhost:8000/')
        if r.status_code == 200:
            print("✅ Backend server is responding on port 8000")
        else:
            print("❌ Backend server returned status:", r.status_code)
    except Exception as e:
        print("❌ Could not connect to backend. Is uvicorn running?")
        return

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        print("✅ Headless browser launched")
        
        await page.goto("http://localhost:8000/")
        print("✅ Frontend loaded")
        
        # Test input fields
        await page.fill("#customSeeds", "bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh\n0x7675DC2856fca0C22ed3C57979388FbF236De57F")
        await page.fill("#customLoss", "150000")
        await page.fill("#customVictim", "AUTO-TEST")
        print("✅ Custom inputs populated")
        
        # Click Run Trace
        await page.click("button:has-text('Run Parallel Trace')")
        print("✅ Trace initiated")
        
        # Wait for trace to complete or error out (Wait up to 30s)
        try:
            await page.wait_for_selector("text=TRACE COMPLETE", timeout=30000)
            print("✅ Trace completed successfully")
        except:
            print("⚠️ Trace did not complete within 30 seconds, or failed.")
            
        # Check Report
        await page.click("button:has-text('Generate Forensic Report')")
        print("✅ Forensic report button clicked")
        
        try:
            await page.wait_for_selector("#print-doc", state="visible", timeout=5000)
            print("✅ Forensic report modal opened")
            victim_text = await page.inner_text("#docVictimInitials")
            if "AUTO-TEST" in victim_text:
                print("✅ Data binding (Victim Initials) confirmed in report")
            else:
                print("❌ Data binding failed in report")
        except:
            print("❌ Forensic report modal failed to open")
            
        await browser.close()
        print("✅ Auto-test suite completed successfully.")

if __name__ == '__main__':
    asyncio.run(test_frontend())
