import requests
import json
import time

API_URL = "http://127.0.0.1:8088/api/start_trace"

TEST_CASES = [
    {"chain": "TRON", "address": "TNcykrU6R99SrR5BnxaqtDZe1V7o2sf664", "note": "TRX Thief Wallet"},
    {"chain": "ETHEREUM", "address": "0x13d2d1f8e62f1f57eab648076583d7ce9f2af867", "note": "ETH $400k"},
    {"chain": "ETHEREUM", "address": "0x7CA30EEE61DD4E2356B2aE59718C23C3C470D3bB", "note": "August 19 starting point ETH"},
    {"chain": "ETHEREUM", "address": "0xf006878B4232C3281C545ae205Eda784DA6EAEAA", "note": "ETH $31k"},
    {"chain": "STELLAR", "address": "GCMPTBICKA5R4HN2DMRSNPMFWGYN5YO73R4B3DUD3SG7OZGCI4LRA3BP", "note": "Stellar to Changehero"},
    {"chain": "RIPPLE", "address": "r9xM4fYBKM9EJcvECEgzcmwMjG5QQeJP8z", "note": "XRP Wallet"},
    {"chain": "BITCOIN", "address": "bc1qphlqxrjgnj6aa0lnmv4kdgxyefk363sxwpp4tp", "note": "BTC Flagged 262k"},
    {"chain": "ETHEREUM", "address": "0x041a583db93c1bfc883583d08fbc2bb001edd25a", "note": "ETH Flagged zfsex.org"}
]

def run_tests():
    print("==================================================")
    print("    NEMESIS OMEGA - BATCH TEST EXECUTION")
    print("==================================================")
    
    results = []
    
    for case in TEST_CASES:
        print(f"\n[+] Testing {case['note']} ({case['chain']}) - {case['address']}")
        payload = {
            "seeds": case['address'],
            "target_amount": "",
            "target_currency": "USD",
            "chain_override": case['chain'],
            "start_date": "",
            "end_date": "",
            "max_depth": 5,
            "max_hops": 10
        }
        
        try:
            resp = requests.post(API_URL, json=payload, timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                trace_id = data.get("trace_id", "UNKNOWN")
                print(f"    -> SUCCESS: Trace Initiated! Trace ID: {trace_id}")
                results.append({"case": case, "status": "SUCCESS", "trace_id": trace_id, "raw": data})
            else:
                print(f"    -> FAILED: HTTP {resp.status_code} - {resp.text}")
                results.append({"case": case, "status": "FAILED", "error": resp.text})
        except Exception as e:
            print(f"    -> ERROR: {str(e)}")
            results.append({"case": case, "status": "ERROR", "error": str(e)})
            
        time.sleep(2) # brief pause between traces
        
    print("\n==================================================")
    print("    TEST BATCH COMPLETED")
    print("==================================================")
    
    with open("batch_test_results.json", "w") as f:
        json.dump(results, f, indent=4)
        
    print("Results saved to batch_test_results.json")

if __name__ == "__main__":
    run_tests()
