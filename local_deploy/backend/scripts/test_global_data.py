import requests
import time
import sys
import os
from dotenv import load_dotenv
load_dotenv()
BASE_URL = "http://localhost:8000"

def print_header(title):
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")

def print_result(name, passed, detail=""):
    icon = "✅ PASS" if passed else "❌ FAIL"
    print(f"[{icon}] {name}")
    if detail:
        print(f"    -> {detail}")

def test_global_data_layer():
    print_header("GLOBAL DATA ENGINE TESTS")
    
    # 1. Login to get token
    login_data = {
        "username": os.getenv("ADMIN_USERNAME", "admin"),
        "password": os.getenv("ADMIN_PASSWORD", "nemesis_admin_2026")
    }
    try:
        auth_req = requests.post(f"{BASE_URL}/api/login", data=login_data, timeout=5)
        if auth_req.status_code != 200:
            print_result("Admin Authentication", False, f"Failed to get token: {auth_req.status_code} - {auth_req.text}")
            return
        token = auth_req.json().get("access_token")
        headers = {"Authorization": f"Bearer {token}"}
        print_result("Admin Authentication", True, "Token acquired")
    except Exception as e:
        print_result("Admin Authentication", False, str(e))
        return

    # 2. Test Import
    dummy_trace = {
        "trace_id": "TEST_TRACE_9999",
        "addresses": ["bc1q_test_wallet_1234", "0x_test_wallet_5678"],
        "metadata": {"source": "Test Script"}
    }
    try:
        r = requests.post(f"{BASE_URL}/api/db/import", json=dummy_trace, headers=headers, timeout=10)
        if r.status_code == 200:
            print_result("Global Import", True, f"Results: {r.json().get('results')}")
        else:
            print_result("Global Import", False, f"Status: {r.status_code} - {r.text}")
    except Exception as e:
        print_result("Global Import", False, str(e))

    # 3. Test Search
    try:
        r = requests.get(f"{BASE_URL}/api/db/search?q=bc1q_test_wallet_1234", headers=headers, timeout=10)
        if r.status_code == 200:
            res = r.json().get('results', {})
            mongo_hits = len(res.get('mongo', []))
            neo4j_hits = len(res.get('neo4j', []))
            pg_hits = len(res.get('pg', []))
            print_result("Global Search", True, f"Found in Mongo: {mongo_hits}, Neo4j: {neo4j_hits}, Postgres: {pg_hits}")
        else:
            print_result("Global Search", False, f"Status: {r.status_code} - {r.text}")
    except Exception as e:
        print_result("Global Search", False, str(e))

    # 4. Test Export
    try:
        r = requests.get(f"{BASE_URL}/api/db/export", headers=headers, timeout=10)
        if r.status_code == 200:
            print_result("Global Export", True, f"Status: {r.json().get('results')}")
        else:
            print_result("Global Export", False, f"Status: {r.status_code} - {r.text}")
    except Exception as e:
        print_result("Global Export", False, str(e))

if __name__ == "__main__":
    try:
        # Wait for server to boot if needed
        requests.get(BASE_URL, timeout=5)
    except:
        print("[!] Backend server is not running. Start with 'python main.py' first.")
        sys.exit(1)
        
    test_global_data_layer()
