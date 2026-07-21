import requests
import os
import json
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

def get_btc_txs(address):
    url = f"https://mempool.space/api/address/{address}/txs"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return []

def get_eth_txs(address):
    api_key = os.getenv("ETHERSCAN_API_KEY", "")
    url = f"https://api.etherscan.io/api?module=account&action=txlist&address={address}&startblock=0&endblock=99999999&page=1&offset=1000&sort=desc&apikey={api_key}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if data.get("status") == "1":
            return data.get("result", [])
    return []

def get_eth_internal_txs(address):
    api_key = os.getenv("ETHERSCAN_API_KEY", "")
    url = f"https://api.etherscan.io/api?module=account&action=txlistinternal&address={address}&startblock=0&endblock=99999999&page=1&offset=1000&sort=desc&apikey={api_key}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if data.get("status") == "1":
            return data.get("result", [])
    return []

def analyze():
    btc_address = "bc1qjhfhx9w024gvmwc0pzps9ad0tgd7utaw8kp65n"
    eth_address = "0xF6b7e5fdcC807C4D929423526810791f72d3cd5F"
    target_date_str = "04/01/2024" # M/D/Y or D/M/Y
    
    # Let's just find the TXs that match the amounts approximately
    target_btc_amount = 0.0950667
    target_eth_amount = 11.4346
    
    btc_txs = get_btc_txs(btc_address)
    print(f"Fetched {len(btc_txs)} BTC txs")
    for tx in btc_txs:
        # Check inputs and outputs
        time_str = datetime.fromtimestamp(tx.get("status", {}).get("block_time", 0)).strftime('%Y-%m-%d %H:%M:%S')
        for vout in tx.get("vout", []):
            amt = vout.get("value", 0) / 1e8
            if abs(amt - target_btc_amount) < 0.001:
                print(f"Match BTC Out: TXID {tx['txid']} Date {time_str} Amt {amt} to {vout.get('scriptpubkey_address')}")
        for vin in tx.get("vin", []):
            amt = vin.get("prevout", {}).get("value", 0) / 1e8
            if abs(amt - target_btc_amount) < 0.001:
                print(f"Match BTC In: TXID {tx['txid']} Date {time_str} Amt {amt} from {vin.get('prevout', {}).get('scriptpubkey_address')}")

    eth_txs = get_eth_txs(eth_address)
    print(f"Fetched {len(eth_txs)} ETH txs")
    for tx in eth_txs:
        amt = int(tx.get("value", 0)) / 1e18
        time_str = datetime.fromtimestamp(int(tx.get("timeStamp", 0))).strftime('%Y-%m-%d %H:%M:%S')
        if abs(amt - target_eth_amount) < 0.1:
            print(f"Match ETH TX: Hash {tx['hash']} Date {time_str} Amt {amt} From {tx['from']} To {tx['to']}")

if __name__ == "__main__":
    analyze()
