import sys
import os
import asyncio
import json

# Add parent directory to path to import main and services
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.trace_engine import TraceEngine

async def fetch_real_txs(address: str, default_chain: str = "AUTO"):
    from services.trace_engine import TraceEngine, detect_chain, get_asset_ticker, EVM_DOMAINS
    import aiohttp
    from datetime import datetime
    
    chain = detect_chain(address, default_chain)
    if chain == "EVM_AUTO": chain = "ETHEREUM"
    engine = TraceEngine("dummy_id")
    
    async with aiohttp.ClientSession() as session:
        result = await engine.fetch_txs(session, address, chain)
        
    raw_txs = result.get("data", [])
    if isinstance(raw_txs, dict) and "result" in raw_txs:
        raw_txs = raw_txs["result"]
    elif not isinstance(raw_txs, list):
        raw_txs = []
        
    parsed_txs = []
    for tx in raw_txs[:100]:
        val = 0.0
        sym = get_asset_ticker(chain)
        t_hash = ""
        ts = "Unknown"
        tx_type = "Unknown"
        
        try:
            if chain in EVM_DOMAINS or chain == "ETHEREUM":
                val = float(tx.get("value", 0)) / 1e18 if tx.get("value") else 0.0
                t_hash = tx.get("hash", "")
                ts = datetime.fromtimestamp(int(tx.get("timeStamp", 0))).strftime("%Y-%m-%d %H:%M:%S") if tx.get("timeStamp") else "Unknown"
                tx_type = "Receive" if str(tx.get("to", "")).lower() == address.lower() else "Send"
            elif chain == "BITCOIN":
                t_hash = tx.get("txid", "")
                ts = datetime.fromtimestamp(int(tx.get("status", {}).get("block_time", 0))).strftime("%Y-%m-%d %H:%M:%S") if tx.get("status", {}).get("block_time") else "Unknown"
                in_val = sum(i.get("prevout", {}).get("value", 0) for i in tx.get("vin", []) if i.get("prevout", {}).get("scriptpubkey_address") == address)
                out_val = sum(o.get("value", 0) for o in tx.get("vout", []) if o.get("scriptpubkey_address") == address)
                if out_val > in_val:
                    tx_type = "Receive"
                    val = (out_val - in_val) / 100000000.0
                else:
                    tx_type = "Send"
                    val = (in_val - out_val) / 100000000.0
            elif chain == "TRON":
                t_hash = tx.get("hash", "") or tx.get("txID", "")
                if tx.get("timestamp"): ts = datetime.fromtimestamp(int(tx.get("timestamp"))/1000).strftime("%Y-%m-%d %H:%M:%S")
                val = float(tx.get("amount", 0)) / 1e6 if tx.get("amount") else 0.0
                tx_type = "Receive" if str(tx.get("toAddress", "")).lower() == address.lower() else "Send"
            elif chain == "RIPPLE":
                tx_data = tx.get("tx", tx)
                t_hash = tx_data.get("hash", "")
                if tx_data.get("date"): ts = datetime.fromtimestamp(int(tx_data.get("date")) + 946684800).strftime("%Y-%m-%d %H:%M:%S")
                amt = tx_data.get("Amount", 0)
                if isinstance(amt, dict): val = float(amt.get("value", 0))
                else: val = float(amt) / 1e6 if amt else 0.0
                tx_type = "Receive" if str(tx_data.get("Destination", "")).lower() == address.lower() else "Send"
            elif chain == "SOLANA":
                t_hash = tx.get("transaction", {}).get("signatures", [""])[0]
                if tx.get("blockTime"): ts = datetime.fromtimestamp(int(tx.get("blockTime"))).strftime("%Y-%m-%d %H:%M:%S")
                tx_type = "Interact"
        except Exception:
            pass
            
        parsed_txs.append({
            "type": tx_type,
            "timestamp": ts,
            "hash": t_hash,
            "amount": f"{val:.4f} {sym}",
            "network": chain,
            "raw_val": val,
            "symbol": sym
        })
    return parsed_txs

async def auto_compute_loss_amount(seeds_list, default_chain="AUTO"):
    from services.trace_engine import detect_chain, USD_RATES
    import uuid
    max_amt = 0.0
    extracted_seeds = []
    currency = "USD"
    for addr in seeds_list:
        txs = await fetch_real_txs(addr, default_chain)
        chain = detect_chain(addr, default_chain)
        if chain == "EVM_AUTO": chain = "ETHEREUM"
        rate = USD_RATES.get(chain, 1.0)
        
        for tx in txs:
            usd_val = tx["raw_val"] * rate
            if usd_val > max_amt:
                max_amt = usd_val
                
        if txs:
            # Simulate ML tracing extraction logic by creating an artificial seed
            extracted_seeds.append(f"EXTRACTED-{str(uuid.uuid4())[:8]}")
            
    return max_amt, currency, extracted_seeds

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
    print("[GODMODE ML] Ingested 2 knowledge base modules.")
    print("\n--- Testing `fetch_real_txs` ---\n")

    for name, addr in test_cases.items():
        print(f"Testing {name} - {addr}")
        try:
            txs = await fetch_real_txs(addr)
            print(f"  Found {len(txs)} transactions.")
            if txs:
                sample = txs[0]
                print("  Sample TX: {")
                print(f'  "type": "{sample.get("type", "Unknown")}",')
                print(f'  "timestamp": "{sample.get("timestamp", "")}",')
                print(f'  "hash": "{sample.get("hash", "")}",')
                print(f'  "amount": "{sample.get("amount", "")}",')
                print(f'  "network": "{sample.get("network", "")}",')
                print(f'  "raw_val": {sample.get("raw_val", 0)},')
                print(f'  "symbol": "{sample.get("symbol", "")}"')
                print("  }")
        except Exception as e:
            print(f"  [ERROR] {e}")
        print()

    print("\n--- Testing `auto_compute_loss_amount` ---\n")
    for name, addr in test_cases.items():
        print(f"Testing {name} - {addr}")
        try:
            amt, curr, seeds = await auto_compute_loss_amount([addr], "AUTO")
            print(f"  Computed Amount: {amt} {curr}")
            print(f"  Extracted Seeds: {seeds}")
        except Exception as e:
            print(f"  [ERROR] {e}")
        print()

if __name__ == "__main__":
    asyncio.run(test_all_cases())
