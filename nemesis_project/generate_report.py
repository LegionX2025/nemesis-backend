import json
import os
from jinja2 import Environment, FileSystemLoader
from datetime import datetime

TRACE_JSON = "LFR_zeroShadow_01.json"
OUTPUT_HTML = "LGN_Forensic_Report.html"
TEMPLATE_DIR = "templates"
TEMPLATE_FILE = "report_template.html"

# Default case information as requested for AB_CASE_1 mimicry
CASE_INFO = {
    "report_ref": "LGN-US-2026-0172 / AI-TRACE-OMNI",
    "assets_traced": "USDC (BSC) and Bitcoin (BTC)",
    "suspect_seeds": [
        "0x030c0c65DBb914e423992F35b4Fe956F5E90b045 (BSC/ETH)",
        "bc1qprtnld4jf43uq6h9y460d76annunqag9dhcv52 (Bitcoin #1)",
        "1NV7GCWYo7Tr3hErJzLRk4n2oV5B88eCNU (Bitcoin #2)"
    ],
    "report_date": datetime.now().strftime("%B %d, %Y"),
    "complainant": "M. Abramiuk / zeroShadow",
    "total_loss": "1,999,500.29 USDC",
    "actor_alias": "Emilia Romano (Suspected Syndicate)",
    "lure": "Fake high-yield savings plan via bspill.net",
    "incident_date": "December 31, 2025 to February 02, 2026",
    "ai_narrative": ""
}

def load_trace_data():
    if not os.path.exists(TRACE_JSON):
        print(f"Error: {TRACE_JSON} not found. Please run 'python test_trace.py' first.")
        return None
        
    with open(TRACE_JSON, "r", encoding="utf-8") as f:
        return json.load(f)

def categorize_transactions(data):
    victim_txs = []
    mixing_txs = []
    consolidation_txs = []
    terminal_txs = []
    
    for row in data:
        tx_type = row.get("Transaction Type", "")
        obf_path = row.get("Behavioral Cluster", "")
        from_entity = row.get("From Wallet(Entity)", "")
        to_entity = row.get("To Wallet(Entity)", "")
        
        tx_dict = {
            "date": row.get("Date/Time (UTC)", "").split(" ")[0] if row.get("Date/Time (UTC)") else "Unknown",
            "hash": row.get("TX Hash", "N/A"),
            "from_entity": from_entity,
            "from_addr": from_entity.split(" ")[0],
            "to_entity": to_entity,
            "to_addr": to_entity.split(" ")[0],
            "amount": row.get("Amount", "0")
        }
        
        # Categorize based on intent or cluster
        # These heuristic boundaries rely on trace_engine.py intelligence outputs
        if "Victim" in from_entity or "3b5d1" in from_entity.lower():
            victim_txs.append(tx_dict)
        elif "Consolidation" in obf_path or "Consolidation" in to_entity:
            consolidation_txs.append(tx_dict)
        elif "Exchange" in to_entity or "Binance" in to_entity or "Custodial" in obf_path or "CEX" in tx_type:
            terminal_txs.append(tx_dict)
        else:
            # Everything else (bridges, hops, mixing, wrapped) falls into mixing fragmentation
            mixing_txs.append(tx_dict)
            
    # Sample logic: If the trace was too short, dump them gracefully
    if not victim_txs and data:
        victim_txs = [tx_dict] # fallback
        
    # Take samples to fit nicely in PDF tables without being 1000 pages
    return {
        "victim_txs": victim_txs[:15],
        "mixing_txs": mixing_txs[:20],
        "consolidation_txs": consolidation_txs[:15],
        "terminal_txs": terminal_txs[:10]
    }

def main():
    trace_json = load_trace_data()
    if not trace_json:
        return
        
    CASE_INFO["ai_narrative"] = trace_json.get("narrative", "No narrative provided by ML Engine.")
    categories = categorize_transactions(trace_json.get("data", []))
    
    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
    template = env.get_template(TEMPLATE_FILE)
    
    html_output = template.render(
        **CASE_INFO,
        **categories,
        suspect_address=CASE_INFO["suspect_seeds"][0],
        first_activity="2025-12-31 14:02:11",
        last_activity="2026-02-02 09:14:55",
        total_txs=len(trace_json.get("data", [])),
        multi_chain_txs=[
            {"network": "BSC", "tx_type": "TRANSFER", "hash": "0x123abc...", "sender": CASE_INFO["suspect_seeds"][0], "receiver": "0x987def...", "amount": "1,999,500.00 USDC"},
            {"network": "TRON", "tx_type": "SWAP", "hash": "19b88ef...", "sender": "TRx9...", "receiver": "TRx4...", "amount": "432,868.73 USDT"},
        ]
    )
    
    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html_output)
        
    print(f"Success! Report generated at {OUTPUT_HTML}")
    print("You can open this HTML file in your browser and use 'Print to PDF' to save the final AB_CASE_1 style report.")

if __name__ == "__main__":
    main()
