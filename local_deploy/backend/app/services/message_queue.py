import os
import json
import logging
from kafka import KafkaProducer, KafkaConsumer
import asyncio

logger = logging.getLogger("KafkaService")

class KafkaMessageQueue:
    def __init__(self):
        self.bootstrap_servers = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
        self.client_id = os.environ.get("KAFKA_CLIENT_ID", "nemesis-tracer")
        self.producer = None
        
    def connect_producer(self):
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                client_id=self.client_id,
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )
            logger.info(f"[*] Connected to Kafka Producer at {self.bootstrap_servers}")
        except Exception as e:
            logger.error(f"[!] Failed to connect to Kafka Producer: {e}")

    async def produce_message(self, topic: str, message: dict):
        if not self.producer:
            self.connect_producer()
            
        if self.producer:
            try:
                # Wrap synchronous producer in asyncio
                future = self.producer.send(topic, value=message)
                # Ensure it's pushed asynchronously
                await asyncio.to_thread(future.get, timeout=5)
                logger.debug(f"[+] Message sent to Kafka topic: {topic}")
            except Exception as e:
                logger.error(f"[!] Kafka Produce Error: {e}")

    def consume_messages(self, topic: str, callback):
        group_id = os.environ.get("KAFKA_CONSUMER_GROUP", "nemesis-group")
        try:
            consumer = KafkaConsumer(
                topic,
                bootstrap_servers=self.bootstrap_servers,
                group_id=group_id,
                value_deserializer=lambda x: json.loads(x.decode('utf-8')),
                auto_offset_reset='earliest'
            )
            logger.info(f"[*] Started Kafka Consumer for topic {topic}")
            for msg in consumer:
                callback(msg.value)
        except Exception as e:
            logger.error(f"[!] Kafka Consumer Error: {e}")

# Singleton instance
kafka_mq = KafkaMessageQueue()
