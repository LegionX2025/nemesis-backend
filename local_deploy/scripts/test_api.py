import requests
import time
import sys

BASE_URL = "http://127.0.0.1:8088"
TEST_ADDRESS = "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"

ENDPOINTS = [
    f"/api/nemesis_id/profile/{TEST_ADDRESS}",
    f"/api/nemesis_id/tx_history/{TEST_ADDRESS}",
    f"/api/nemesis_id/aml/{TEST_ADDRESS}",
    f"/api/nemesis_id/intel/{TEST_ADDRESS}",
    f"/api/osint/{TEST_ADDRESS}",
    f"/api/nemesis_id/georisk/{TEST_ADDRESS}",
    f"/api/nemesis_id/ai_insights/{TEST_ADDRESS}",
    f"/api/wallet_profile/{TEST_ADDRESS}"
]

def wait_for_server(timeout=30):
    start = time.time()
    while time.time() - start < timeout:
        try:
            res = requests.get(BASE_URL + "/")
            if res.status_code == 200:
                print("[*] Server is up!")
                return True
        except requests.ConnectionError:
            pass
        time.sleep(1)
    return False

def run_tests():
    print(f"Waiting for server at {BASE_URL}...")
    if not wait_for_server():
        print("[!] Server failed to start or did not respond in time.")
        sys.exit(1)

    print("\n--- RUNNING E2E API TESTS ---")
    passed = 0
    failed = 0

    for ep in ENDPOINTS:
        url = BASE_URL + ep
        try:
            res = requests.get(url, timeout=10)
            if res.status_code == 200:
                try:
                    data = res.json()
                    print(f"[SUCCESS] {ep} -> 200 OK (Valid JSON)")
                    passed += 1
                except ValueError:
                    print(f"[FAIL] {ep} -> 200 OK but Invalid JSON")
                    failed += 1
            else:
                print(f"[FAIL] {ep} -> HTTP {res.status_code}")
                failed += 1
        except Exception as e:
            print(f"[ERROR] {ep} -> {str(e)}")
            failed += 1

    print("\n--- SUMMARY ---")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    
    if failed > 0:
        sys.exit(1)

if __name__ == "__main__":
    run_tests()
