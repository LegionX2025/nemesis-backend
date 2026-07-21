import asyncio
import os
import sys
import logging

logging.basicConfig(level=logging.INFO)

# Add backend/app to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'app')))

from services.recursive_tracer import RecursiveTracer
from services.oklink_scraper import OKLinkScraper
from collections import defaultdict
import sys
sys.setrecursionlimit(1000000)

async def run_custom_trace():
    print("=========================================")
    print("   NEMESIS OMNI-CHAIN CUSTOM TRACE       ")
    print("=========================================\n")
    
    victim_wallet = "0x3b5D17e2236f4D773DA87EE10B71D80C5e5b5772"
    suspect_wallet = "0x030c0c65DBb914e423992F35b4Fe956F5E90b045"
    print(f"[+] Injecting Case: Custom Investigation")
    print(f"    Victim Wallet: {victim_wallet}")
    print(f"    Suspect Seed: {suspect_wallet}")
    print(f"    Target Asset: USDC")
    print(f"    Target Amount: 1999500.29")
    
    tracer = RecursiveTracer()
    
    try:
        # Unlimited BFS until the target amount is isolated
        path = []
        target_amount = 1999500.29
        async for edge in tracer.start_omni_trace_bfs(suspect_wallet, max_depth=1000000):
            path.append(edge)
            if edge["edge_type"] == "TRANSFER" and edge.get("amount"):
                if abs(float(edge["amount"]) - float(target_amount)) / float(target_amount) < 0.05:
                    print(f"    [!] HIGH CONFIDENCE TARGET AMOUNT TRACED: {edge['tx_hash']} -> {edge['to']}")
                    break
        
        print(f"\n    -> Found {len(path)} total correlated state transitions.")
        
        if path:
            print(f"\n    [+] Extracting unique entities for OKLink Automated Resolution...")
            unique_addresses = set()
            for p in path:
                unique_addresses.add((p['from'], p['chain']))
                unique_addresses.add((p['to'], p['chain']))
                
            print(f"    [+] Resolving {len(unique_addresses)} entities via Batch Scraper...")
            scraper = OKLinkScraper()
            resolved_labels = await scraper.batch_scrape_addresses(list(unique_addresses))
            
            print("\n    -> FULL PATH TRACE:")
            for i, p in enumerate(path):
                from_lbl = resolved_labels.get(p['from'].lower(), [])
                to_lbl = resolved_labels.get(p['to'].lower(), [])
                from_str = f"{p['from']} ({','.join(from_lbl)})" if from_lbl else p['from']
                to_str = f"{p['to']} ({','.join(to_lbl)})" if to_lbl else p['to']
                print(f"       [{i+1}] {from_str} -> {to_str} | Hash: {p['tx_hash']} | Amount: {p['amount']} {p['asset']}")

            # Calculate Terminal CEX Losses
            print("\n=========================================")
            print("   TERMINAL CEX / CUSTODIAL LOSS REPORT  ")
            print("=========================================")
            
            cex_landed = defaultdict(float)
            for p in path:
                to_addr = p['to'].lower()
                labels = resolved_labels.get(to_addr, [])
                is_cex = any(kw in lbl.upper() for lbl in labels for kw in ["EXCHANGE", "BINANCE", "KRAKEN", "OKX", "CUSTODIAL", "HOT WALLET", "HUOBI", "KUCOIN", "MEXC"])
                
                if is_cex:
                    cex_name = next((lbl for lbl in labels if any(kw in lbl.upper() for kw in ["EXCHANGE", "BINANCE", "KRAKEN", "OKX", "HUOBI", "KUCOIN", "MEXC"])), "Unknown CEX")
                    amt = float(p.get('amount', 0.0))
                    cex_landed[f"{cex_name} ({to_addr})"] += amt
                    
            if cex_landed:
                for cex, amount in cex_landed.items():
                    print(f"    -> {cex}: {amount:.4f} Assets")
            else:
                print("    -> No assets confirmed landed in CEX/Custodial wallets.")
                
            # Format the output data according to the requested schema
            formatted_path = []
            for p in path:
                from_addr = p['from'].lower()
                to_addr = p['to'].lower()
                from_lbls = resolved_labels.get(from_addr, [])
                to_lbls = resolved_labels.get(to_addr, [])
                
                from_str = f"{p['from']} ({','.join(from_lbls)})" if from_lbls else p['from']
                to_str = f"{p['to']} ({','.join(to_lbls)})" if to_lbls else p['to']
                
                # Determine CEX Status for Timestamp column
                is_cex = any(kw in lbl.upper() for lbl in from_lbls + to_lbls for kw in ["EXCHANGE", "BINANCE", "KRAKEN", "OKX", "CUSTODIAL", "HOT WALLET"])
                cex_time = p['timestamp'].isoformat() if is_cex else p['timestamp'].isoformat()
                
                # Receiver Entity name
                receiver_entity = next((lbl for lbl in to_lbls if "EXCHANGE" in lbl.upper() or "MIXER" in lbl.upper()), "Private Wallet")
                if not to_lbls: receiver_entity = "Unknown"
                
                # Transaction Intelligence
                tx_intel = f"Chain: {p['chain']} | Method: {p['edge_type']}"
                
                # Calculate USD Estimate
                asset = str(p.get('asset', 'UNKNOWN')).upper()
                try: amount_val = float(p.get('amount', 0))
                except: amount_val = 0.0
                
                oracle = {
                    "ETH": 3500.00, "BTC": 65000.00, "SOL": 150.00, 
                    "BNB": 580.00, "TRX": 0.12, "USDC": 1.00, 
                    "USDT": 1.00, "DAI": 1.00, "MATIC": 0.80, 
                    "ARB": 1.10, "OP": 2.50, "HBAR": 0.10, 
                    "XRP": 0.50, "XLM": 0.10
                }
                price = oracle.get(asset, 0.0)
                usd_val = amount_val * price
                amount_str = f"{amount_val:,.4f} {asset} (~${usd_val:,.2f} USD)" if usd_val > 0 else f"{amount_val:,.4f} {asset}"

                formatted_path.append({
                    "Date/Time (UTC)": cex_time,
                    "Type of Tx Correlation": "Direct Transfer" if p['edge_type'] == "TRANSFER" else "Heuristic/Protocol Hop",
                    "TX Hash": p['tx_hash'],
                    "From Wallet(Entity)": from_str,
                    "To Wallet(Entity)": to_str,
                    "To Receiver Entity": receiver_entity,
                    "Amount": amount_str,
                    "Transaction Type": p['edge_type'],
                    "Behavioral Cluster": "Pending OSINT" if not to_lbls else ",".join(to_lbls[:2]),
                    "Clustered address{root}ENTITY": "OKLink_Resolved",
                    "Confidence": p['confidence'],
                    "Tx Attributions": f"Asset: {p['asset']} | Network: {p['chain']}",
                    "Transaction Intelligence": tx_intel
                })
                
            # Export to JSON
            json_file = "custom_trace_report.json"
            import json
            with open(json_file, "w", encoding="utf-8") as f:
                json.dump(formatted_path, f, indent=4)
            print(f"\n    [+] JSON data exported to {json_file}")
            
            # Export to CSV
            import csv
            csv_file = "custom_trace_report.csv"
            with open(csv_file, "w", encoding="utf-8", newline="") as f:
                if formatted_path:
                    writer = csv.DictWriter(f, fieldnames=formatted_path[0].keys())
                    writer.writeheader()
                    for p in formatted_path:
                        writer.writerow(p)
            print(f"    [+] CSV data exported to {csv_file}")
            
            # Generate the HTML Forensic Report
            print("\n    [+] Generating Advanced Lionsgate Forensic HTML Report...")
            import subprocess
            generate_script = os.path.join(os.path.dirname(__file__), "generate_report.py")
            try:
                subprocess.run([sys.executable, generate_script], check=True)
            except Exception as e:
                print(f"    [!] Failed to generate HTML report: {e}")
            
        else:
            print("    -> No further transitions found.")
            
        print("-" * 50)
        
    except Exception as e:
        print(f"    [!] Error during trace: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run_custom_trace())
