import os
import requests
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from urllib.parse import urlparse

# Directories to target to avoid indexing thousands of irrelevant pages
TARGET_PATHS = ["/workers/", "/pages/", "/api/"]
SITEMAP_URL = "https://developers.cloudflare.com/sitemap-0.xml"

# Output directory for the ML Engine
OUTPUT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "NEMESIS_KNOWLEDGE_BASE_LIBRARY", "cloudflare_docs"))

def init_directory():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        print(f"[+] Created directory: {OUTPUT_DIR}")

def fetch_sitemap_urls():
    print(f"[*] Fetching sitemap from {SITEMAP_URL}...")
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"}
    try:
        response = requests.get(SITEMAP_URL, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Parse XML
        root = ET.fromstring(response.content)
        urls = []
        # XML namespace handling for sitemaps
        namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        
        for url in root.findall('ns:url', namespace):
            loc = url.find('ns:loc', namespace)
            if loc is not None:
                url_str = loc.text
                # Filter by target paths
                parsed_url = urlparse(url_str)
                if any(parsed_url.path.startswith(tp) for tp in TARGET_PATHS):
                    urls.append(url_str)
                    
        print(f"[+] Found {len(urls)} target URLs in the sitemap.")
        return urls
    except Exception as e:
        print(f"[!] Failed to fetch sitemap: {e}")
        return []

def scrape_and_save(url):
    print(f"[*] Scraping: {url}")
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"}
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Target the main content area (Cloudflare docs usually use <main> or an article tag)
        main_content = soup.find('main') or soup.find('article')
        
        if not main_content:
            print(f"    [-] No main content found for {url}. Skipping.")
            return False
            
        # Clean out navs, sidebars, and footers from the main content just in case
        for element in main_content.find_all(['nav', 'footer', 'aside', 'script', 'style']):
            element.decompose()
            
        # Extract title
        title_tag = soup.find('title')
        title = title_tag.text if title_tag else "cloudflare_doc"
        
        # Clean title for filename
        safe_title = "".join([c if c.isalnum() else "_" for c in title]).strip("_")
        
        text_content = f"# {title}\n\n"
        text_content += f"Source URL: {url}\n\n"
        
        # Extract markdown-like text
        for element in main_content.find_all(['h1', 'h2', 'h3', 'p', 'pre', 'li']):
            text = element.get_text(strip=True)
            if not text:
                continue
                
            if element.name == 'h1':
                text_content += f"# {text}\n\n"
            elif element.name == 'h2':
                text_content += f"## {text}\n\n"
            elif element.name == 'h3':
                text_content += f"### {text}\n\n"
            elif element.name == 'pre':
                text_content += f"```\n{text}\n```\n\n"
            elif element.name == 'li':
                text_content += f"- {text}\n"
            else:
                text_content += f"{text}\n\n"
                
        filename = f"{safe_title}.md"
        filepath = os.path.join(OUTPUT_DIR, filename)
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(text_content)
            
        return True
        
    except Exception as e:
        print(f"    [!] Error scraping {url}: {e}")
        return False

def main():
    print("============================================================")
    print(" 🌩️ NEMESIS KNOWLEDGE BASE: CLOUDFLARE DOCS AUTO-INDEXER")
    print("============================================================")
    
    init_directory()
    urls = fetch_sitemap_urls()
    
    if not urls:
        print("[!] No URLs to process. Exiting.")
        return
        
    # Limit to first 50 to prevent rate-limiting during initial ingestion
    MAX_LIMIT = 50
    print(f"[*] Limiting execution to {MAX_LIMIT} pages to prevent IP blocks.")
    
    success_count = 0
    for url in urls[:MAX_LIMIT]:
        if scrape_and_save(url):
            success_count += 1
            
    print("============================================================")
    print(f" ✅ AUTO-INDEX COMPLETE. Successfully extracted {success_count} documents.")
    print(f" 📂 Documents stored in: {OUTPUT_DIR}")
    print("============================================================")

if __name__ == "__main__":
    main()
