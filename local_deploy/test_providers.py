import requests
import json
import os

print("--- Testing Ankr Advanced API ---")
ankr_key = "d0ebdc10f7a98d2c08105ddcef64d9353e5b92e1d59e545debed8af8bce60fbc"
ankr_url = f"https://rpc.ankr.com/multichain/{ankr_key}"
try:
    ankr_payload = {
        "jsonrpc": "2.0",
        "method": "ankr_getTransactionsByAddress",
        "params": {
            "blockchain": "bsc",
            "address": "0x3b5D17e2236f4D773DA87EE10B71D80C5e5b5772"
        },
        "id": 1
    }
    ankr_res = requests.post(ankr_url, json=ankr_payload)
    print("Ankr Status:", ankr_res.status_code)
    try:
        data = ankr_res.json()
        txs = data.get("result", {}).get("transactions", [])
        print("Ankr Transactions Found:", len(txs))
        if txs:
            print("Sample Tx:", txs[0].get("hash"))
    except:
        print("Ankr Response Error:", ankr_res.text[:200])
except Exception as e:
    print("Ankr Request Failed:", e)

print("\n--- Testing Tatum API ---")
tatum_key = "t-689cf2666ee03b5b553977b2-ffee8013de0747bda4e360b7"
tatum_url = "https://api.tatum.io/v3/bsc/account/transaction/0x3b5D17e2236f4D773DA87EE10B71D80C5e5b5772"
try:
    tatum_res = requests.get(tatum_url, headers={"x-api-key": tatum_key})
    print("Tatum Status:", tatum_res.status_code)
    try:
        data = tatum_res.json()
        print("Tatum Transactions Found:", len(data))
        if data and isinstance(data, list):
            print("Sample Tx:", data[0].get("hash") or data[0].get("transactionHash"))
    except:
        print("Tatum Response Error:", tatum_res.text[:200])
except Exception as e:
    print("Tatum Request Failed:", e)
