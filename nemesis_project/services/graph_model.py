import os
from neo4j import GraphDatabase, AsyncGraphDatabase
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("NemesisNeo4j")

NEO4J_URI = os.getenv("NEO4J_URI", "neo4j+s://89ea7d8f.databases.neo4j.io")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "89ea7d8f")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "pMyRVGUtCLJCHBph0vR3FBVk5Ct1jkrThq-ApD2cJAA")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "89ea7d8f")

class Neo4jGraphModel:
    def __init__(self):
        self._driver = None
        self._async_driver = None
        
    def connect(self):
        try:
            self._driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
            # Test connection
            self._driver.verify_connectivity()
            logger.info("✅ Connected to Neo4j Aura Graph Database")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")

    async def connect_async(self):
        try:
            self._async_driver = AsyncGraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
            await self._async_driver.verify_connectivity()
            logger.info("✅ Connected to Neo4j Aura (Async)")
        except Exception as e:
            logger.error(f"Failed to async connect to Neo4j: {e}")

    def close(self):
        if self._driver:
            self._driver.close()
            
    async def close_async(self):
        if self._async_driver:
            await self._async_driver.close()

    async def initialize_schema(self):
        """Create constraints and indexes to optimize graph queries."""
        if not self._async_driver:
            await self.connect_async()
            
        queries = [
            "CREATE CONSTRAINT wallet_address IF NOT EXISTS FOR (w:Wallet) REQUIRE w.address IS UNIQUE",
            "CREATE CONSTRAINT entity_name IF NOT EXISTS FOR (e:Entity) REQUIRE e.name IS UNIQUE",
            "CREATE INDEX wallet_chain IF NOT EXISTS FOR (w:Wallet) ON (w.chain)"
        ]
        
        async with self._async_driver.session(database=NEO4J_DATABASE) as session:
            for q in queries:
                try:
                    await session.run(q)
                except Exception as e:
                    logger.warning(f"Schema initialization warning: {e}")

    async def record_wallet_cluster(self, source_address: str, target_address: str, chain: str, interaction_type="TRANSACTED_WITH"):
        """Creates or updates a cluster edge between two wallets."""
        if not self._async_driver:
            await self.connect_async()
            
        query = f"""
        MERGE (a:Wallet {{address: $source}})
        ON CREATE SET a.chain = $chain, a.first_seen = timestamp()
        
        MERGE (b:Wallet {{address: $target}})
        ON CREATE SET b.chain = $chain, b.first_seen = timestamp()
        
        MERGE (a)-[r:{interaction_type}]->(b)
        ON CREATE SET r.count = 1, r.last_seen = timestamp()
        ON MATCH SET r.count = r.count + 1, r.last_seen = timestamp()
        """
        async with self._async_driver.session(database=NEO4J_DATABASE) as session:
            await session.run(query, source=source_address.lower(), target=target_address.lower(), chain=chain)

    async def tag_wallet(self, address: str, tag: str, chain: str):
        """Links a wallet to an Entity label in the graph."""
        if not self._async_driver:
            await self.connect_async()
            
        query = """
        MERGE (w:Wallet {address: $address})
        ON CREATE SET w.chain = $chain, w.first_seen = timestamp()
        
        MERGE (e:Entity {name: $tag})
        
        MERGE (w)-[:HAS_TAG]->(e)
        """
        async with self._async_driver.session(database=NEO4J_DATABASE) as session:
            await session.run(query, address=address.lower(), tag=tag, chain=chain)

# Singleton instance
graph_db = Neo4jGraphModel()
