import os
import asyncio
from neo4j import GraphDatabase, AsyncGraphDatabase
import logging

logger = logging.getLogger(__name__)

class GraphEngine:
    """
    Neo4j Graph Database Driver for NEMESIS TraceEngine.
    Handles high-performance native graph ingestion for BFS omni-chain tracing.
    """
    def __init__(self):
        self.uri = os.getenv("NEO4J_URI", "bolt://neo4j:7687")
        self.user = os.getenv("NEO4J_USER", "neo4j")
        self.password = os.getenv("NEO4J_PASSWORD", "nemesis2026")
        self.driver = None

    async def connect(self):
        try:
            self.driver = AsyncGraphDatabase.driver(self.uri, auth=(self.user, self.password))
            logger.info(f"Connected to Neo4j Graph DB at {self.uri}")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            self.driver = None

    async def close(self):
        if self.driver:
            await self.driver.close()

    async def merge_node(self, address: str, entity_type: str = "Unknown", balance: float = 0.0):
        if not self.driver: return
        query = """
        MERGE (a:Address {id: $address})
        ON CREATE SET a.type = $type, a.balance = $balance, a.created_at = timestamp()
        ON MATCH SET a.balance = $balance, a.updated_at = timestamp()
        """
        async with self.driver.session() as session:
            await session.run(query, address=address.lower(), type=entity_type, balance=balance)

    async def merge_edge(self, from_addr: str, to_addr: str, tx_hash: str, amount: float, token: str, timestamp: str):
        if not self.driver: return
        query = """
        MATCH (src:Address {id: $from_addr})
        MATCH (dst:Address {id: $to_addr})
        MERGE (src)-[r:TRANSFERRED {hash: $tx_hash}]->(dst)
        ON CREATE SET r.amount = $amount, r.token = $token, r.timestamp = $timestamp
        """
        async with self.driver.session() as session:
            await session.run(
                query, 
                from_addr=from_addr.lower(), 
                to_addr=to_addr.lower(), 
                tx_hash=tx_hash.lower(), 
                amount=amount, 
                token=token, 
                timestamp=timestamp
            )

graph_engine = GraphEngine()
