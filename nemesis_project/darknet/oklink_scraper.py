import os
import sys
import json
import re
import subprocess
import time
from collections import deque

try:
    import playwright_stealth
except ImportError:
    print("[SYSTEM] Installing playwright-stealth...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "playwright-stealth", "playwright", "kafka-python"])
    subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])
    print("[SYSTEM] Installed successfully. Please re-run the script.")
    sys.exit(0)

try:
    from kafka import KafkaProducer
    KAFKA_AVAILABLE = True
except ImportError:
    KAFKA_AVAILABLE = False

from playwright.sync_api import sync_playwright

# Initialize Kafka Producer if available
producer = None
if KAFKA_AVAILABLE:
    try:
        producer = KafkaProducer(
            bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"),
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            retries=3
        )
        print("[*] Connected to Kafka Cluster")
    except Exception as e:
        print(f"[!] Kafka connection failed: {e}. Running without Kafka stream.")
        producer = None

def apply_stealth(page):
    try:
        import playwright_stealth
        try:
            from playwright_stealth import stealth_sync
            stealth_sync(page)
            return
        except Exception:
            pass

        if hasattr(playwright_stealth, 'stealth_sync') and callable(playwright_stealth.stealth_sync):
            playwright_stealth.stealth_sync(page)
        elif hasattr(playwright_stealth, 'stealth') and callable(playwright_stealth.stealth):
            playwright_stealth.stealth(page)
        else:
            try:
                from playwright_stealth.stealth import stealth_sync
                stealth_sync(page)
            except Exception:
                pass
    except ImportError:
        pass

def scrape_oklink_entity(chain, start_address, max_depth=1, max_cluster_size=50):
    """
    Crawls OKLink to extract entity tags and auto-clusters addresses by mapping the transaction graph.
    Emits (source, target, chain, tag) events to Kafka for the Nemesis Neo4j ingestion.
    """
    visited = set()
    queue = deque([(start_address, 0)]) # (address, depth)
    
    clustered_edges = []
    root_tags = []
    
    print(f"[*] Starting Auto-Clustering Crawler on {chain.upper()}: {start_address} (Max Depth: {max_depth})")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--headless=new"])
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        apply_stealth(page)
        
        while queue and len(visited) < max_cluster_size:
            address, depth = queue.popleft()
            if address in visited:
                continue
                
            visited.add(address)
            url = f"https://www.oklink.com/{chain}/address/{address}"
            
            tags = []
            intercepted_txs = []
            
            def handle_response(response):
                if "address-tags/support" in response.url or "/api/explorer/v" in response.url:
                    try:
                        data = response.json()
                        tags.append(data)
                    except: pass
                # Intercept transaction list APIs for auto-clustering
                if "address-transaction" in response.url or "address-summary" in response.url:
                    try:
                        tx_data = response.json()
                        intercepted_txs.append(tx_data)
                    except: pass
            
            # Rebind event listener for each page
            page.remove_listener("response", handle_response)
            page.on("response", handle_response)
            
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=45000)
                page.wait_for_timeout(3000) 
            except Exception as e:
                print(f"[!] Warning during navigation for {address}: {e}")
                
            # Extract tags from DOM
            try:
                dom_tags = page.evaluate('''() => {
                    return Array.from(document.querySelectorAll('.tagsList-MN1-u .text-ellipsis, div[class*="tag-md"] .text-ellipsis'))
                        .map(el => el.textContent.trim().replace(/^#\\s*/, ''));
                }''')
                tags.extend(dom_tags)
            except: pass
            
            # Clean Tags
            final_tags = []
            for tag in tags:
                if isinstance(tag, str):
                    clean_text = tag.lstrip('#').strip()
                    if clean_text and len(clean_text) > 2 and clean_text not in ["Overview", "Transactions", "Token"]:
                        final_tags.append(clean_text)
                elif isinstance(tag, dict):
                    api_dump = json.dumps(tag)
                    api_tags = re.findall(r'"tag_name":\s*"([^"]+)"', api_dump)
                    final_tags.extend(api_tags)
                    
            final_tags = list(set(final_tags))
            
            # Extract transactions/edges for clustering
            # 1. From intercepted API
            linked_addresses = set()
            if intercepted_txs:
                tx_dump = json.dumps(intercepted_txs)
                # Find all things that look like addresses (e.g. 0x...)
                # Heuristic: looking for "from" and "to" fields in JSON
                from_matches = re.findall(r'"from"\s*:\s*"([^"]+)"', tx_dump)
                to_matches = re.findall(r'"to"\s*:\s*"([^"]+)"', tx_dump)
                linked_addresses.update(from_matches)
                linked_addresses.update(to_matches)
                
            # 2. From DOM hrefs
            try:
                dom_links = page.evaluate('''() => {
                    return Array.from(document.querySelectorAll('a[href*="/address/"]'))
                        .map(a => a.href.split('/').pop());
                }''')
                linked_addresses.update(dom_links)
            except: pass
            
            # Filter and queue neighbors
            linked_addresses = {a for a in linked_addresses if len(a) > 20 and a != address}
            
            for neighbor in list(linked_addresses)[:20]: # cap branching factor
                clustered_edges.append((address, neighbor))
                
                # Emit to Kafka
                if producer:
                    event = {
                        "event_type": "WALLET_CLUSTER_EDGE",
                        "source": address,
                        "target": neighbor,
                        "chain": chain,
                        "tags": final_tags if address == start_address else []
                    }
                    producer.send("nemesis.crawler.wallet_discovered", event)
                
                if depth < max_depth:
                    queue.append((neighbor, depth + 1))
                    
            print(f"[*] Crawled {address} (Depth {depth}) - Found {len(final_tags)} tags, {len(linked_addresses)} edges")
            
            if address == start_address:
                root_tags = final_tags
            
        browser.close()
        
        if producer:
            producer.flush()
            
        return {
            "chain": chain,
            "root_address": start_address,
            "total_clustered_nodes": len(visited),
            "total_edges": len(clustered_edges),
            "root_tags": root_tags
        }

# Maintain backward compatibility with existing tracer
def scrape_oklink_tags(chain, address):
    res = scrape_oklink_entity(chain, address, max_depth=0)
    tags = res.get("root_tags", [])
    if not tags:
        tags = ["OKLink-Crawled"]
    return {
        "chain": chain,
        "address": address,
        "attributionTags": tags
    }

if __name__ == "__main__":
    # Test Scenario: Crawl Tornado Cash Router 1-hop neighborhood
    test_chain = "eth"
    test_address = "0xd90e2f925da726b50c4ed8d0fb90ad053324f31b"
    try:
        result = scrape_oklink_entity(test_chain, test_address, max_depth=1)
        print(f"\n🚀 CRAWLER FINISHED:")
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"[!] Critical Error: {e}")
