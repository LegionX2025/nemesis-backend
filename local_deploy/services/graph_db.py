import os
import logging
from neo4j import GraphDatabase, AsyncGraphDatabase

logger = logging.getLogger("Neo4jService")

class Neo4jService:
    def __init__(self):
        self.uri = os.environ.get("NEO4J_URI", "neo4j+s://89ea7d8f.databases.neo4j.io")
        self.username = os.environ.get("NEO4J_USERNAME", "89ea7d8f")
        self.password = os.environ.get("NEO4J_PASSWORD", "pMyRVGUtCLJCHBph0vR3FBVk5Ct1jkrThq-ApD2cJAA")
        self.database = os.environ.get("NEO4J_DATABASE", "neo4j")
        self.driver = None

    async def connect(self):
        try:
            self.driver = AsyncGraphDatabase.driver(self.uri, auth=(self.username, self.password))
            logger.info(f"[*] Connected to Neo4j Aura Instance: {self.uri}")
        except Exception as e:
            logger.error(f"[!] Failed to connect to Neo4j Aura: {e}")

    async def close(self):
        if self.driver:
            await self.driver.close()

    async def add_wallet_node(self, address: str, chain: str, tags: list):
        query = """
        MERGE (w:Wallet {address: $address, chain: $chain})
        SET w.tags = $tags, w.last_seen = timestamp()
        RETURN w
        """
        async with self.driver.session(database=self.database) as session:
            result = await session.run(query, address=address.lower(), chain=chain.upper(), tags=tags)
            return await result.single()

    async def add_transaction_edge(self, from_addr: str, to_addr: str, tx_hash: str, chain: str, value: float):
        query = """
        MERGE (sender:Wallet {address: $from_addr})
        MERGE (receiver:Wallet {address: $to_addr})
        MERGE (sender)-[t:TRANSACTED_WITH {tx_hash: $tx_hash, chain: $chain}]->(receiver)
        SET t.value = $value, t.timestamp = timestamp()
        RETURN t
        """
        async with self.driver.session(database=self.database) as session:
            result = await session.run(query, from_addr=from_addr.lower(), to_addr=to_addr.lower(), tx_hash=tx_hash, chain=chain.upper(), value=value)
            return await result.single()

# Singleton instance
neo4j_db = Neo4jService()
