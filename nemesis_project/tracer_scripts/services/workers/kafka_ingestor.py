"""
NEMESIS v3.1 Enterprise
Kafka Stream Ingestor
Bridges Bitquery Real-time Kafka Topics (Trades/Transfers) into the Cloudflare Serverless Queue.
"""

import json
import logging
from typing import Dict, Any

logger = logging.getLogger("NEMESIS.Workers.KafkaIngestor")

class KafkaStreamIngestor:
    """
    Acts as a bridge between the Bitquery Kafka infrastructure (docs.bitquery.io/docs/streams/kafka-streaming-concepts/)
    and the NEMESIS Cloudflare Job Queue.
    
    Instead of NEMESIS constantly polling Bitquery, Bitquery pushes transactions to Kafka,
    which this ingestor reads and routes directly into the Serverless Edge.
    """
    
    def __init__(self, env):
        self.env = env
        
    async def process_kafka_batch(self, batch_messages: list):
        """
        Simulates receiving a batch of messages from a Bitquery Kafka consumer.
        In a real Cloudflare deployment, this could be triggered by a Cloudflare Worker
        bound to a Kafka stream via HTTP webhooks, or a separate microservice.
        """
        queue_payloads = []
        
        for msg in batch_messages:
            try:
                # Parse Bitquery GraphQL/Kafka JSON structure
                data = json.loads(msg) if isinstance(msg, str) else msg
                
                # Check for DEX Trades
                if "dex_trades" in data:
                    for trade in data["dex_trades"]:
                        maker = trade.get("maker")
                        taker = trade.get("taker")
                        token_address = trade.get("token")
                        
                        if maker:
                            queue_payloads.append({
                                "type": "blockchain_trace",
                                "session_id": "GLOBAL_MONITORING",
                                "address": maker,
                                "chain": data.get("network", "AUTO"),
                                "current_depth": 1,
                                "max_depth": 2, # Fast triage depth
                                "context": f"DEX Trade Detected: {token_address}"
                            })
                            
                # Check for Standard Transfers
                elif "transfers" in data:
                    for transfer in data["transfers"]:
                        sender = transfer.get("sender")
                        amount = transfer.get("amount")
                        
                        # Only trigger traces for large volume transfers (Whale tracking)
                        if sender and amount and float(amount) > 50000:
                            queue_payloads.append({
                                "type": "blockchain_trace",
                                "session_id": "WHALE_MONITORING",
                                "address": sender,
                                "chain": data.get("network", "AUTO"),
                                "current_depth": 1,
                                "max_depth": 3,
                                "context": f"Whale Transfer: ${amount}"
                            })
            except Exception as e:
                logger.error(f"Failed to parse Kafka message: {e}")
                
        # Bulk Dispatch into Cloudflare Queue
        if queue_payloads:
            logger.info(f"Dispatching {len(queue_payloads)} tasks to Cloudflare NEMESIS_JOB queue from Kafka stream.")
            for payload in queue_payloads:
                await self.env.JOB_QUEUE.send(payload)
