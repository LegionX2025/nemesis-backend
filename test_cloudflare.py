import urllib.request
import json
import time

def print_header(title):
    print(f"\n{'='*50}\n {title}\n{'='*50}")

def test_endpoint(name, url, method="GET", payload=None):
    print(f"Testing {name} -> {url}...")
    try:
        req = urllib.request.Request(url, method=method)
        if payload:
            req.add_header("Content-Type", "application/json")
            data = json.dumps(payload).encode('utf-8')
            req.data = data
            
        start = time.time()
        with urllib.request.urlopen(req, timeout=10) as response:
            latency = (time.time() - start) * 1000
            body = response.read().decode('utf-8')
            print(f"  [SUCCESS] Status: {response.getcode()} ({latency:.2f}ms)")
            try:
                print(f"  [RESPONSE]: {json.loads(body)}")
            except:
                print(f"  [RESPONSE]: {body[:200]}...")
            return True
    except urllib.error.URLError as e:
        print(f"  [ERROR] Connection failed: {e}")
        if hasattr(e, 'read'):
            try:
                print(f"  [BODY] {e.read().decode('utf-8')}")
            except:
                pass
        return False

def main():
    print_header("NEMESIS CLOUDFLARE/RENDER ARCHITECTURE TEST")
    
    # 1. Test Render Backend Directly
    backend_url = "https://nemesis-backend.onrender.com"
    print_header("1. TESTING RENDER BACKEND (PYTHON / FASTAPI)")
    test_endpoint("Backend Health", f"{backend_url}/admin/health")
    test_endpoint("Backend Intelligence", f"{backend_url}/api/intelligence/summary")
    
    # 2. Test Cloudflare Worker Proxy
    # Note: Replace this with your actual deployed worker URL if different
    cf_worker_url = "https://nemesis-edge.legionxgaming2021.workers.dev" 
    print_header("2. TESTING CLOUDFLARE EDGE WORKER (PROXY TO RENDER)")
    test_endpoint("Proxy Health", f"{cf_worker_url}/admin/health")
    
    # 3. Test Cloudflare Pages Frontend
    cf_pages_url = "https://nemesis-id-frontend.pages.dev"
    print_header("3. TESTING CLOUDFLARE PAGES (STATIC FRONTEND)")
    test_endpoint("Frontend Load", f"{cf_pages_url}/index.html")

    print("\n[NOTE] If tests fail due to 'Not Found' or DNS errors, ensure you have deployed using `python auto_deploy.py` in the root folder so the services are live on these URLs.")

if __name__ == "__main__":
    main()
