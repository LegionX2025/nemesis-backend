import sys
import os
import asyncio
import json

# Add backend/app to path to import main and services
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'app')))

from main import fetch_real_txs
from services.trace_engine import auto_compute_loss_amount

async def test_all_cases():
    test_cases = {
        "BTC - Pig Butchering": "bc1qpa8n0a5ckt7wkdw3cn8eklsz3z0kn89knme5a9",
        "BTC - Fake Trading": "bc1qcrdrmxx49pfzrmltx6my4cp62n6t4e58jeu0y7",
        "BTC - Flagged": "bc1qphlqxrjgnj6aa0lnmv4kdgxyefk363sxwpp4tp",
        "XRP - Ledger Scam": "ra58paZqDhh2e6LtA4VPQEgAztUz3Z3urq",
        "XRP - Secondary": "r9xM4fYBKM9EJcvECEgzcmwMjG5QQeJP8z",
        "ETH - Token Scam 1": "0x159a861a3f0838adb1e6895886c7a0be7158be89",
        "ETH - Etherscanverify": "0x2042404183ecd9610da5b251bb5f6e93eb9d3e08",
        "ETH - Token Scam 2A": "0x60E760222474A10f378cD53A5Bcd2CBd5a70eD1F",
        "ETH - Token Scam 2B": "0x0ed649357AbdAaA0222fE452B50D61D3E4a263a8",
        "ETH - Token Scam 3": "0x6f00b583914fb35d314b36d2d914c145210be24e",
        "ETH - Token Scam 4": "0x53556d7f1553Fa43D446D5363426447c40EDeAb3",
        "ETH - Token Scam 5": "0x13d2d1f8e62f1f57eab648076583d7ce9f2af867",
        "ETH - Token Scam 6": "0x7CA30EEE61DD4E2356B2aE59718C23C3C470D3bB",
        "ETH - Token Scam 7": "0xf006878B4232C3281C545ae205Eda784DA6EAEAA",
        "ETH - Flagged": "0x041a583db93c1bfc883583d08fbc2bb001edd25a",
        "SOL - Unverified NFT Burn 1": "uThZSCB2R8UQXHuPKPQLrRC5n7VTdSqUrJDQuoJsNum",
        "SOL - Unverified NFT Burn 2": "6vMuna31vRDs9u9RAEF8UeCSs9CNu6j4LkXpe4Ko1gBQ",
        "SOL - Unverified NFT Burn 3": "G2YxRa6wt1qePMwfJzdXZG62ej4qaTC7YURzuh2Lwd3t",
        "SOL - Unverified NFT Burn 4": "J7RBLx4gr5QisTidhJEzMj4awHz2ajwWKVREwN2J2TKR",
        "TRX - Exodus Wallet Scam": "TNcykrU6R99SrR5BnxaqtDZe1V7o2sf664",
        "Stellar - Incident": "GCMPTBICKA5R4HN2DMRSNPMFWGYN5YO73R4B3DUD3SG7OZGCI4LRA3BP"
    }
    
    print("=========================================")
    print("   NEMESIS ID & TRACER - DATA VALIDATION ")
    print("=========================================\n")

    print("--- 1. Testing `fetch_real_txs` (Nemesis ID Data) ---")
    for name, addr in test_cases.items():
        print(f"\n[+] Testing {name} | {addr}")
        try:
            txs = await fetch_real_txs(addr)
            print(f"  -> Found {len(txs)} transactions.")
            if txs:
                print(f"  -> Latest TX: {txs[0].get('amount')} {txs[0].get('symbol')} ({txs[0].get('timestamp')})")
        except Exception as e:
            print(f"  [ERROR] {e}")

    print("\n=========================================\n")
    
    print("--- 2. Testing `auto_compute_loss_amount` (Tracer Initialization) ---")
    for name, addr in test_cases.items():
        print(f"\n[+] Testing {name} | {addr}")
        try:
            amt, cur, extracted = await auto_compute_loss_amount([addr], "AUTO")
            print(f"  -> Computed Highest Loss: {amt} {cur}")
            print(f"  -> Extracted Next Hop / Receiver: {extracted}")
        except Exception as e:
            print(f"  [ERROR] {e}")

if __name__ == "__main__":
    asyncio.run(test_all_cases())
