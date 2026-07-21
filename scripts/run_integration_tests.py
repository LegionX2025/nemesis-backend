import json
import os
import requests
import time

BASE_URL = "http://127.0.0.1:8000"
TEST_FILE = os.path.join(os.path.dirname(__file__), "test_cases.json")

def wait_for_server():
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

def run_tests():
    if not os.path.exists(TEST_FILE):
        print(f"[!] Test file not found: {TEST_FILE}")
        return

    with open(TEST_FILE, "r") as f:
        cases = json.load(f)

    if not wait_for_server():
        print("[!] Backend server is not running on port 8000. Please start main.py first.")
        print("[!] Run: python main.py")
        return

    print("\n" + "="*50)
    print("🚀 NEMESIS OMNICHAIN INTEGRATION TESTS")
    print("="*50)

    total_scenarios = len(cases)
    total_wallets = sum(len(c["wallets"]) for c in cases)
    
    print(f"[*] Loaded {total_scenarios} scenarios containing {total_wallets} total wallets.\n")

    for idx, case in enumerate(cases, 1):
        scenario_name = case["scenario"]
        wallets = case["wallets"]
        chain_override = case.get("chain_override", "AUTO")
        
        print(f"[{idx}/{total_scenarios}] Testing Scenario: {scenario_name}")
        print(f"    -> Wallets: {len(wallets)}")
        print(f"    -> Chain: {chain_override}")
        
        seeds_str = ",".join(wallets)
        
        payload = {
            "seeds": seeds_str,
            "target_amount": "",
            "target_currency": "USD",
            "start_date": "",
            "end_date": "",
            "chain_override": chain_override,
            "max_depth": 3,
            "max_hops": 100
        }
        
        try:
            res = requests.post(f"{BASE_URL}/api/start_trace", json=payload, timeout=10)
            if res.status_code == 200:
                data = res.json()
                trace_id = data.get("trace_id")
                if trace_id:
                    print(f"    ✅ Trace successfully initialized! Trace ID: {trace_id}")
                else:
                    print(f"    ❌ Trace init failed. Response: {data}")
            else:
                print(f"    ❌ HTTP Error: {res.status_code} - {res.text}")
        except Exception as e:
            print(f"    ❌ Request failed: {e}")
            
        print("-" * 50)
        time.sleep(1) # Slight delay between large batches to not overload the engine

    print("\n✅ Integration Testing Complete. Check the backend logs for processing status.")

if __name__ == "__main__":
    run_tests()
