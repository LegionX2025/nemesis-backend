import asyncio
import logging
from datetime import datetime
from services.collectors.bitquery_plugins import TransferCollector, DexCollector, BridgeCollector

logger = logging.getLogger("IntelligencePipeline")

# ==============================================================================
# STATE & BATCH BROADCASTER ARCHITECTURE (INTEGRATED)
# ==============================================================================

class SOCState:
    def __init__(self):
        self.visited = set()
        self.queue = asyncio.Queue()
        self.broadcast_queue = asyncio.Queue() # HIGH-PERFORMANCE BUFFER
        self.state_lock = asyncio.Lock()
        self.target_reached = False
        self.seeds = []

async def ws_broadcaster(state: SOCState, ws_list: set):
    """
    ⚡ HIGH PERFORMANCE BATCH BROADCASATER ⚡
    Pulls edges from the memory queue and blasts them to the frontend in arrays of 50.
    """
    buffer = []
    while not state.target_reached or not state.broadcast_queue.empty():
        try:
            edge = await asyncio.wait_for(state.broadcast_queue.get(), timeout=0.25)
            buffer.append(edge)
            state.broadcast_queue.task_done()
        except asyncio.TimeoutError:
            pass # Timeout hit, time to flush buffer

        # Flush condition: 50 items OR queue is empty but we have pending data
        if buffer and (len(buffer) >= 50 or state.broadcast_queue.empty()):
            payload = {"type": "LEDGER_BATCH", "data": buffer}
            for ws in list(ws_list):
                try: 
                    await ws.send_json(payload)
                except Exception: 
                    ws_list.discard(ws)
            buffer.clear()
            
        # Graceful halt if all viewers disconnect
        if not ws_list:
            state.target_reached = True

# ==============================================================================
# MULTI-COLLECTOR BITQUERY PLUGIN WORKERS
# ==============================================================================

async def fetch_omni_events(addr: str, depth: int) -> list:
    """
    Executes multiple Bitquery collectors in parallel.
    Replaces the linear sequential fetching.
    """
    # Initialize collectors
    collectors = [
        TransferCollector(),
        DexCollector(),
        BridgeCollector()
        # Add more plugins here (NFTCollector, StakingCollector, etc.)
    ]
    
    # Run in parallel using asyncio.gather
    tasks = [c.fetch(addr, depth) for c in collectors]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    edges = []
    for res in results:
        if isinstance(res, Exception):
            logger.error(f"Collector Error: {res}")
            continue
        edges.extend(res)
        
    # Fast heuristic scoring to prevent pipeline stream buffering delays
    if edges:
        for edge in edges:
            from_str = str(edge.get("sender_entity", "")).upper()
            to_str = str(edge.get("receiver_entity", "")).upper()
            
            threat_score = 10 # Default low risk
            if "MIXER" in from_str or "MIXER" in to_str:
                threat_score = 95
            elif "SUSPECT" in from_str or "SUSPECT" in to_str:
                threat_score = 85
            elif "BRIDGE" in from_str or "BRIDGE" in to_str:
                threat_score = 40
            elif "EXCHANGE" in from_str or "EXCHANGE" in to_str:
                threat_score = 20
                
            edge["Threat_Score"] = threat_score
            edge["AML_Score"] = threat_score
            edge["MITRE_Vectors"] = ["T1562.001"] if threat_score > 80 else []
            
    return edges

async def engine_worker(state: SOCState, worker_id: int):
    while not state.target_reached:
        try: 
            item = await asyncio.wait_for(state.queue.get(), timeout=2.0)
        except asyncio.TimeoutError: 
            continue
        
        addr, depth = item
        
        async with state.state_lock:
            if addr in state.visited or depth > 5: # Max depth 5
                state.queue.task_done()
                continue
            state.visited.add(addr)
            
        logger.info(f"[WORKER-{worker_id:02d}] Fetching Bitquery Plugins for {addr[:8]}... (Depth {depth})")
        
        # 1. Fetch Data Concurrently via Plugin System
        edges = await fetch_omni_events(addr, depth)
        
        # 2. Process & Route
        for edge in edges:
            if state.target_reached: break
            
            # Put next hop into task queue
            if not edge.get("is_terminal", False) and edge.get("to") not in state.visited:
                state.queue.put_nowait((edge["to"], depth + 1))
                
            # CRITICAL: Dump to broadcast queue immediately.
            state.broadcast_queue.put_nowait(edge)
            
        state.queue.task_done()

async def run_intelligence_pipeline(seeds: list, ws_list: set):
    """
    Main Orchestrator Entrypoint.
    Replaces `run_trace_engine` with the new Bitquery Plugin architecture.
    """
    logger.info(f"[PIPELINE] Initializing High-Velocity Intelligence Pipeline.")
    state = SOCState()
    state.seeds = seeds
    
    # 1. Seed Queue
    for seed in state.seeds:
        state.queue.put_nowait((seed, 0))
        
    # 2. Spawn Workers (Concurrency = 25)
    workers = [asyncio.create_task(engine_worker(state, i)) for i in range(25)]
    
    # 3. Spawn Batch Broadcaster
    broadcaster = asyncio.create_task(ws_broadcaster(state, ws_list))
    
    # 4. Wait for exhaustion
    await state.queue.join()
    await state.broadcast_queue.join() 
    
    logger.info("[PIPELINE] Matrix Exhausted. Halting workers.")
    state.target_reached = True
    for w in workers: w.cancel()
    broadcaster.cancel()

    for ws in list(ws_list):
        try: await ws.send_json({"type": "COMPLETE"})
        except: pass
