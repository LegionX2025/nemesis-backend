import sys
from playwright.sync_api import sync_playwright

def snapshot():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        print("Navigating to https://nemesis-id-frontend.pages.dev ...")
        page.goto("https://nemesis-id-frontend.pages.dev", wait_until="networkidle")
        page.wait_for_selector("text=NEMESIS ID", timeout=10000)
        
        # Take screenshot
        screenshot_path = r"C:\Users\LEGIONX\.gemini\antigravity\brain\d0b9964f-2e93-4f96-a938-23eb5510d2f5\frontend_snapshot.png"
        page.screenshot(path=screenshot_path, full_page=True)
        print(f"Screenshot saved to {screenshot_path}")
        browser.close()

if __name__ == "__main__":
    snapshot()
