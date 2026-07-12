import os
import requests
from bs4 import BeautifulSoup
import time

KNOWLEDGE_BASE_DIR = r"C:\Users\LEGIONX\Downloads\cases\nemesis_project\NEMESIS_KNOWLEDGE_BASE_LIBRARY\bitquery_docs"
BASE_URL = "https://docs.bitquery.io/docs/"
SITEMAP_URL = "https://docs.bitquery.io/sitemap.xml"

def setup_directory():
    os.makedirs(KNOWLEDGE_BASE_DIR, exist_ok=True)
    print(f"[*] Initialized Knowledge Base at {KNOWLEDGE_BASE_DIR}")

def extract_content(html):
    soup = BeautifulSoup(html, 'html.parser')
    main_content = soup.find('main')
    if not main_content:
        main_content = soup.find('article')
    if not main_content:
        return ""
    
    # Strip scripts and styles
    for element in main_content(["script", "style", "nav", "footer"]):
        element.extract()
        
    return main_content.get_text(separator='\n\n', strip=True)

def fetch_page(url):
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.text
    except Exception as e:
        print(f"[!] Failed to fetch {url}: {e}")
    return None

def main():
    setup_directory()
    print(f"[*] Fetching Bitquery Documentation Sitemap...")
    
    xml_data = fetch_page(SITEMAP_URL)
    if not xml_data:
        print("[!] Could not fetch sitemap. Defaulting to core v2 endpoints.")
        urls = [
            "https://docs.bitquery.io/docs/category/examples/",
            "https://docs.bitquery.io/docs/graphql/query/",
            "https://docs.bitquery.io/docs/graphql/dataset/"
        ]
    else:
        soup = BeautifulSoup(xml_data, 'xml')
        urls = [loc.text for loc in soup.find_all('loc') if "/docs/examples/" in loc.text or "/docs/graphql/" in loc.text]

    print(f"[*] Found {len(urls)} relevant documentation pages. Indexing max 50...")
    
    count = 0
    for url in urls[:50]:
        filename = url.strip('/').split('/')[-1]
        if not filename or filename == "docs": filename = "index"
        filepath = os.path.join(KNOWLEDGE_BASE_DIR, f"{filename}.md")
        
        if os.path.exists(filepath):
            continue
            
        print(f"[*] Scraping {url}...")
        html = fetch_page(url)
        if html:
            content = extract_content(html)
            if content:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(f"# Source: {url}\n\n{content}")
                count += 1
        time.sleep(1) # Rate limit protection

    print(f"[+] Successfully indexed {count} new pages into NEMESIS_KNOWLEDGE_BASE_LIBRARY.")

if __name__ == "__main__":
    main()
