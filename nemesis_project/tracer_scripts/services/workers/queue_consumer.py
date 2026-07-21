"""
NEMESIS v3.1 Enterprise
Cloudflare Queue Consumer
Replaces Celery/RabbitMQ for long-running AI and Blockchain Trace jobs.
"""

import json
import logging
from typing import List, Dict, Any
from tracer_scripts.services.ai.router import fabric_router
from tracer_scripts.services.workers.edge_trace_engine import EdgeTraceEngine

logger = logging.getLogger("NEMESIS.Workers.QueueConsumer")

async def queue_consumer(batch, env):
    """
    Cloudflare native queue consumer.
    Triggered when batches of messages are pushed to the NEMESIS_JOB queue.
    """
    logger.info(f"Processing Queue Batch: {len(batch.messages)} messages.")
    
    for msg in batch.messages:
        try:
            payload = msg.body
            job_type = payload.get("type")
            
            if job_type == "ai_query":
                # Execute heavy AI reasoning in the background!
                prompt = payload.get("prompt")
                session_id = payload.get("session_id")
                
                # Route through AI Fabric
                result = await fabric_router.execute_prompt(prompt)
                
                # Push result back to the Durable Object to stream to connected Analysts
                do_id = env.SESSION_ENGINE.idFromName(session_id)
                stub = env.SESSION_ENGINE.get(do_id)
                
                await stub.fetch("http://internal/push", method="POST", body=json.dumps({
                    "action": "broadcast",
                    "payload": {"type": "ai_response", "data": result}
                }))
                
                msg.ack() # Mark as successfully processed
                
            elif job_type == "blockchain_trace":
                # Infinite Hop Fan-Out Engine
                session_id = payload.get("session_id")
                address = payload.get("address")
                chain = payload.get("chain", "AUTO")
                current_depth = payload.get("current_depth", 1)
                max_depth = payload.get("max_depth", 3)
                
                engine = EdgeTraceEngine(env)
                await engine.process_hop(session_id, address, chain, current_depth, max_depth)
                msg.ack()
                
            else:
                logger.warning(f"Unknown job type: {job_type}")
                msg.retry() # Put back on queue
                
        except Exception as e:
            logger.error(f"Failed to process queue message: {str(e)}")
            msg.retry() # Dead-letter queue mechanism kicks in after max retries
