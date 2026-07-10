import requests
import json
import os

ankr_key = "d0ebdc10f7a98d2c08105ddcef64d9353e5b92e1d59e545debed8af8bce60fbc"
url = f"https://rpc.ankr.com/multichain/{ankr_key}"

payload = {
    "jsonrpc": "2.0",
    "method": "ankr_getTransactionsByAddress",
    "params": {
        "blockchain": "bsc",
        "address": "0x3b5D17e2236f4D773DA87EE10B71D80C5e5b5772"
    },
    "id": 1
}

response = requests.post(url, json=payload)
print(response.json())
