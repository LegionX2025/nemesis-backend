import asyncio
import os
import sys

# Add backend/app to Python path to find services module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'app')))

from services.recursive_tracer import RecursiveTracer

# ---------------------------------------------------------
# Test Cases (Based on User's Incidents)
# ---------------------------------------------------------
CASES = [
    {
        "name": "Pig Butchering (BTC)",
        "network": "BITCOIN",
        "suspect_wallet": "bc1qpa8n0a5ckt7wkdw3cn8eklsz3z0kn89knme5a9",
        "loss": "1.6M"
    },
    {
        "name": "Fake Recovery (XRP)",
        "network": "RIPPLE",
        "suspect_wallet": "ra58paZqDhh2e6LtA4VPQEgAztUz3Z3urq",
        "loss": "432K"
    },
    {
        "name": "Fake Trading (BTC)",
        "network": "BITCOIN",
        "suspect_wallet": "bc1qcrdrmxx49pfzrmltx6my4cp62n6t4e58jeu0y7",
        "loss": "0.7M"
    },
    {
        "name": "Unverified NFT Burn (SOL)",
        "network": "SOLANA",
        "suspect_wallet": "uThZSCB2R8UQXHuPKPQLrRC5n7VTdSqUrJDQuoJsNum",
        "loss": "Unknown"
    },
    {
        "name": "Exodus Wallet Scam (TRX)",
        "network": "TRON",
        "suspect_wallet": "TNcykrU6R99SrR5BnxaqtDZe1V7o2sf664",
        "loss": "306k"
    },
    {
        "name": "Stellar Anchor Scheme (XLM)",
        "network": "STELLAR",
        "suspect_wallet": "GCMPTBICKA5R4HN2DMRSNPMFWGYN5YO73R4B3DUD3SG7OZGCI4LRA3BP",
        "loss": "Unknown"
    }
]

async def run_tests():
    print("=========================================")
    print("   RECURSIVE OMNI-CHAIN ENGINE TEST      ")
    print("=========================================\n")
    
    tracer = RecursiveTracer()
    
    for case in CASES:
        print(f"[+] Injecting Case: {case['name']} | Chain: {case['network']}")
        print(f"    Suspect Seed: {case['suspect_wallet']}")
        
        try:
            # Inject into the recursive algorithm (Depth 2 to avoid too much API spam for testing)
            path = await tracer.trace_from_entity(case['suspect_wallet'], depth=0, max_depth=2)
            
            print(f"    -> Found {len(path)} total correlated state transitions.")
            
            # Print a quick summary of the path
            if path:
                # Find the deepest node reached (terminal node)
                deepest = path[-1]
                terminal_address = deepest['to']
                
                # Look up the entity in the database to get labels
                ent = tracer.entities_col.find_one({"_id": terminal_address})
                labels = ent.get("labels", []) if ent else []
                entity_name = ", ".join(labels) if labels else "Unknown/Unlabeled Entity"
                

                
                print(f"    -> Terminal Node Reached: {terminal_address}")
                print(f"    -> Entity: {entity_name}")
                print(f"    -> Amount Landed: {deepest.get('amount', '0.0')} {deepest.get('asset', 'UNKNOWN')}")
            else:
                print("    -> No further transitions found within 2 hops.")
                
            print("-" * 50)
            
        except Exception as e:
            print(f"    [!] Error during recursion: {e}")
            print("-" * 50)

if __name__ == "__main__":
    asyncio.run(run_tests())
