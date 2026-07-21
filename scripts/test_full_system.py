import requests
import time
import json
import os
from dotenv import load_dotenv
load_dotenv()

BASE_URL = "http://127.0.0.1:8000"

def print_header(title):
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")

def print_result(name, passed, details=""):
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"[{status}] {name}")
    if details:
        print(f"    -> {details}")

def wait_for_server():
    print_header("SERVER LIFECYCLE INITIALIZATION")
    print("[*] Waiting for backend server to become available...")
    for _ in range(30):
        try:
            r = requests.get(f"{BASE_URL}/admin/health", timeout=2)
            if r.status_code == 200:
                print("[*] Server is UP!")
                return True
        except:
            pass
        time.sleep(2)
    return False

def test_frontend_routes():
    print_header("1. FRONTEND ROUTE VALIDATION")
    routes = [
        ("/", "Main Dashboard"),
        ("/tracer", "Tracer App"),
        ("/nemesis_id", "Nemesis ID App"),
        ("/darknet_search", "Darknet OSINT App"),
        ("/admin", "Admin Panel")
    ]
    
    for route, name in routes:
        try:
            r = requests.get(f"{BASE_URL}{route}", timeout=5)
            print_result(name, r.status_code == 200, f"Status: {r.status_code}")
        except Exception as e:
            print_result(name, False, str(e))

def test_admin_db_health():
    print_header("2. ADMIN & DATABASE HEALTH")
    
    # Health check
    try:
        r = requests.get(f"{BASE_URL}/admin/health", timeout=5)
        print_result("System Health", r.status_code == 200, r.text)
    except Exception as e:
        print_result("System Health", False, str(e))
        
    # DB Stats
    try:
        # First, attempt to login to get a bearer token
        login_data = {
            "username": os.getenv("ADMIN_USERNAME", "admin"),
            "password": os.getenv("ADMIN_PASSWORD", "nemesis_admin_2026")
        }
        auth_req = requests.post(f"{BASE_URL}/api/login", data=login_data, timeout=5)
        
        headers = {}
        if auth_req.status_code == 200:
            token = auth_req.json().get("access_token")
            headers = {"Authorization": f"Bearer {token}"}
            
        r = requests.get(f"{BASE_URL}/api/admin/db_stats", headers=headers, timeout=5)
        print_result("Database Statistics", r.status_code == 200, f"Status: {r.status_code}")
    except Exception as e:
        print_result("Database Statistics", False, str(e))

def test_nemesis_tracer():
    print_header("3. NEMESIS TRACER ENGINE")
    
    payload = {
        "seeds": "bc1qpa8n0a5ckt7wkdw3cn8eklsz3z0kn89knme5a9",
        "target_amount": "",
        "target_currency": "USD",
        "start_date": "",
        "end_date": "",
        "chain_override": "AUTO",
        "max_depth": 1,
        "max_hops": 5
    }
    try:
        r = requests.post(f"{BASE_URL}/api/start_trace", json=payload, timeout=10)
        passed = r.status_code == 200 and "trace_id" in r.json()
        print_result("Initialize Trace (/api/start_trace)", passed, f"Trace ID: {r.json().get('trace_id', 'None')}" if passed else r.text)
    except Exception as e:
        print_result("Initialize Trace (/api/start_trace)", False, str(e))

    try:
        req = {"entities": ["bc1qpa8n0a5ckt7wkdw3cn8eklsz3z0kn89knme5a9"]}
        r = requests.post(f"{BASE_URL}/api/resolve_entity", json=req, timeout=10)
        print_result("Resolve Entity Label (/api/resolve_entity)", r.status_code == 200, r.text[:100] + "...")
    except Exception as e:
        print_result("Resolve Entity Label (/api/resolve_entity)", False, str(e))

def test_nemesis_id():
    print_header("4. NEMESIS ID PROFILING")
    
    wallet = "bc1qpa8n0a5ckt7wkdw3cn8eklsz3z0kn89knme5a9"
    endpoints = [
        (f"/api/nemesis_id/profile/{wallet}", "Entity Profile"),
        (f"/api/nemesis_id/aml/{wallet}", "AML Compliance Score"),
        (f"/api/nemesis_id/tx_history/{wallet}", "Transaction History Parsing"),
        (f"/api/nemesis_id/intel/{wallet}", "Godmode ML & Darknet Intel")
    ]
    
    for route, name in endpoints:
        try:
            r = requests.get(f"{BASE_URL}{route}", timeout=15)
            print_result(name, r.status_code == 200, f"Status: {r.status_code}")
        except Exception as e:
            print_result(name, False, str(e))

def test_darknet_osint():
    print_header("5. DARKNET OSINT SCRAPER")
    try:
        r = requests.get(f"{BASE_URL}/api/darknet/search?q=alphabay", timeout=20)
        print_result("Execute Darknet Search", r.status_code == 200, f"Status: {r.status_code}")
    except Exception as e:
        print_result("Execute Darknet Search", False, str(e))

def main():
    if not wait_for_server():
        print("[!] Backend server is not running on port 8000. Please start main.py first.")
        print("[!] Run: python main.py")
        return
        
    test_frontend_routes()
    test_admin_db_health()
    test_nemesis_tracer()
    test_nemesis_id()
    test_darknet_osint()
    
    print("\n" + "="*60)
    print(" ✅ AUTOMATED TESTING SUITE COMPLETED")
    print("="*60)

if __name__ == "__main__":
    main()
