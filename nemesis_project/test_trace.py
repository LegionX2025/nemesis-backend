import asyncio
import sys
import os
import aiohttp

from services.trace_engine import TraceEngine
from services.database_connector import db_connector

async def test_trace():
    print("Initializing Databases...")
    db_connector.init_databases()
    
    print("Initializing Trace Engine (zeroShadow Case LGN-US-2026-0172)...")
    engine = TraceEngine("zeroShadow_01")
    
    # Victim Wallet
    victim_seed = "0x3b5D17e2236f4D773DA87EE10B71D80C5e5b5772"
    
    # Suspect Aggregator (Received additional funds from other victims)
    suspect_wallet = "0x030c0c65DBb914e423992F35b4Fe956F5E90b045"
    
    target_asset = "USDC"
    target_amount = 1999500.29
    
    engine.setup(
        seeds=[victim_seed, suspect_wallet], 
        target_amount=target_amount, 
        default_chain="BSC", 
        max_depth=10000, 
        max_hops=100000,
        start_date="2025-12-31",
        end_date="2026-02-02"
    )
    
    # Run the full trace engine (which handles workers, visited sets, and file exports)
    print("Starting trace execution...")
    await engine.run()
    
    print(f"Trace completed. Processed {len(engine.ledger)} state-transitions.")
    if hasattr(engine, 'ai_narrative'):
        print(f"AI Narrative: {engine.ai_narrative}")
            
if __name__ == "__main__":
    asyncio.run(test_trace())
