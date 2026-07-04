import sys
import os
import asyncio
import json

# Add parent directory to path to import main
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import fetch_real_txs
from services.trace_engine import auto_compute_loss_amount

async def test_multi_chain():
    test_cases = {
        "BTC (Pig Butchering)": "bc1qpa8n0a5ckt7wkdw3cn8eklsz3z0kn89knme5a9",
        "XRP (Ledger Scam)": "ra58paZqDhh2e6LtA4VPQEgAztUz3Z3urq",
    }
    
    print("--- Testing `fetch_real_txs` ---")
    for name, addr in test_cases.items():
        print(f"\nTesting {name} - {addr}")
        try:
            txs = await fetch_real_txs(addr)
            print(f"  Found {len(txs)} transactions.")
            if txs:
                print("  Sample TX:", json.dumps(txs[0], indent=2))
        except Exception as e:
            print(f"  [ERROR] {e}")

    print("\n--- Testing `auto_compute_loss_amount` ---")
    for name, addr in test_cases.items():
        print(f"\nTesting {name} - {addr}")
        try:
            amt, cur, extracted = await auto_compute_loss_amount([addr], "AUTO")
            print(f"  Computed Amount: {amt} {cur}")
            print(f"  Extracted Seeds: {extracted}")
        except Exception as e:
            print(f"  [ERROR] {e}")

if __name__ == "__main__":
    asyncio.run(test_multi_chain())
