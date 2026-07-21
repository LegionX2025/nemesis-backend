import os
import asyncio
import httpx
from datetime import datetime, timezone
from celery import Celery
import socketio
import logging
from dotenv import load_dotenv
from pymongo import MongoClient

# Ensure we import from the same path as main.py
try:
    from app.main import (
        SOCState, detect_chain, get_asset_ticker, Config,
        BlockchainNetwork, GBIONode, EvidenceRecord, TransferAction, GBIOEngine,
        ROTATOR
    )
except ImportError:
    from main import (
        SOCState, detect_chain, get_asset_ticker, Config,
        BlockchainNetwork, GBIONode, EvidenceRecord, TransferAction, GBIOEngine,
        ROTATOR
    )

load_dotenv()
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
DATABASE_MONGO_URL = os.getenv("DATABASE_MONGO_URL")

mongo_client = None
mongo_db = None
if DATABASE_MONGO_URL:
    try:
        mongo_client = MongoClient(DATABASE_MONGO_URL)
        mongo_db = mongo_client.get_database()
        logger.info("[*] Connected to MongoDB Atlas successfully in Celery Worker")
    except Exception as e:
        logger.error(f"[!] MongoDB Atlas connection failed: {e}")

celery_app = Celery(
    'nemesis_tasks',
    broker=REDIS_URL,
    backend=REDIS_URL
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1
)

logger = logging.getLogger("CELERY_WORKER")

# External Emitter for Socket.IO via Redis Message Bus
sio_mgr = socketio.RedisManager(REDIS_URL, write_only=True)

# -------------------------------------------------------------------------
# ASYNC TRACE LOGIC (Adapted from main.py)
# -------------------------------------------------------------------------

class SIOMockClient:
    def __init__(self, trace_id, mgr):
        self.trace_id = trace_id
        self.sio_mgr = mgr
    async def send_json(self, node):
        if "type" in node and node["type"] == "DBSCAN_UPDATE":
            self.sio_mgr.emit('DBSCAN_UPDATE', node["data"], room=self.trace_id)
        else:
            self.sio_mgr.emit('LEDGER_BATCH', [node], room=self.trace_id)

async def run_trace_engine_async(seeds, target_amount, network, trace_id):
    from app.services.trace_engine import TraceEngine
    logger.info(f"[TRACE] Celery executing trace {trace_id} for seeds: {seeds}")
    sio_mgr.emit('PROGRESS', {"message": "Initializing OmniChain Investigation..."}, room=trace_id)
    
    engine = TraceEngine(trace_id=trace_id)
    engine.setup(seeds=seeds, target_amount=target_amount, default_chain=network)
    
    # Mock WebSocket to broadcast updates over Socket.IO via Redis
    engine.clients.add(SIOMockClient(trace_id, sio_mgr))
    
    sio_mgr.emit('PROGRESS', {"message": "Launching Playwright Parsers & RPC Nodes..."}, room=trace_id)
    
    await engine.run()
    
    sio_mgr.emit('PROGRESS', {"message": "Cluster Analysis & Graph Construction Complete."}, room=trace_id)
    
    # Dump to MongoDB
    if mongo_db is not None:
        sio_mgr.emit('PROGRESS', {"message": "Saving trace payload to MongoDB..."}, room=trace_id)
        try:
            trace_payload = {
                "trace_id": trace_id,
                "seeds": seeds,
                "target_amount": target_amount,
                "edges": engine.ledger,
                "timestamp": datetime.now(timezone.utc)
            }
            mongo_db.traces.insert_one(trace_payload)
        except Exception as e:
            logger.error(f"[!] Failed to save trace to MongoDB: {e}")

    sio_mgr.emit('PROGRESS', {"message": "Final Report Generation Complete."}, room=trace_id)
    sio_mgr.emit('COMPLETE', data={"status": "done"}, room=trace_id)

@celery_app.task(name="execute_trace")
def execute_trace_task(seeds, target_amount, network, trace_id):
    """
    Synchronous Celery task wrapper that runs the asyncio event loop.
    """
    asyncio.run(run_trace_engine_async(seeds, target_amount, network, trace_id))
