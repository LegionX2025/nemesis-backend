import os
import logging
import asyncio
import datetime

logger = logging.getLogger("OmniChainEngine.Database")

class UniversalDatabaseConnector:
    """
    Handles auto-saving and auto-clustering persistence across multiple 
    cloud databases (MongoDB, Neo4j, Cloudflare).
    """
    def __init__(self):
        self.mongo_client = None
        self.mongo_db = None
        self.neo4j_driver = None
        self.cloudflare_configured = False
        
        self.init_mongodb()
        self.init_neo4j()
        self.init_cloudflare()

    def init_mongodb(self):
        try:
            mongo_uri = os.environ.get("MONGODB_URI")
            if mongo_uri:
                import motor.motor_asyncio
                self.mongo_client = motor.motor_asyncio.AsyncIOMotorClient(mongo_uri)
                self.mongo_db = self.mongo_client.nemesis_intel
                logger.info("MongoDB connected successfully.")
        except Exception as e:
            logger.warning(f"MongoDB initialization skipped/failed: {e}")

    def init_neo4j(self):
        try:
            neo4j_uri = os.environ.get("NEO4J_URI")
            neo4j_user = os.environ.get("NEO4J_USER", "neo4j")
            neo4j_pass = os.environ.get("NEO4J_PASSWORD")
            if neo4j_uri and neo4j_pass:
                from neo4j import AsyncGraphDatabase
                self.neo4j_driver = AsyncGraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_pass))
                logger.info("Neo4j Graph Database connected successfully.")
        except Exception as e:
            logger.warning(f"Neo4j initialization skipped/failed: {e}")
            
    def init_cloudflare(self):
        try:
            cf_account_id = os.environ.get("CLOUDFLARE_ACCOUNT_ID")
            cf_token = os.environ.get("CLOUDFLARE_API_TOKEN")
            if cf_account_id and cf_token:
                self.cloudflare_configured = True
                logger.info("Cloudflare DB (D1/KV) configuration detected.")
        except Exception as e:
            logger.warning(f"Cloudflare configuration skipped/failed: {e}")

    async def save_entity(self, address: str, chain: str, label: str, cluster: str, tags: list = None, metadata: dict = None):
        """
        Auto-resolves and auto-saves wallet address entity intelligence into all available databases.
        """
        timestamp = datetime.datetime.now(datetime.timezone.utc)
        record = {
            "address": address.lower(),
            "chain": (chain or "UNKNOWN").upper(),
            "label": label,
            "cluster": cluster,
            "tags": tags or [],
            "metadata": metadata or {},
            "timestamp": timestamp,
            "source": "Nemesis Swarm Scraper"
        }
        
        tasks = []
        if self.mongo_db is not None:
            tasks.append(self._save_to_mongo(record))
            
        if self.neo4j_driver is not None:
            tasks.append(self._save_to_neo4j(record))
            
        if self.cloudflare_configured:
            tasks.append(self._save_to_cloudflare(record))
            
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
            
    async def _save_to_mongo(self, record):
        try:
            await self.mongo_db.wallet_labels.update_one(
                {"address": record["address"]},
                {"$set": record},
                upsert=True
            )
        except Exception as e:
            logger.error(f"Mongo save failed: {e}")

    async def _save_to_neo4j(self, record):
        try:
            query = """
            MERGE (w:Wallet {address: $address})
            SET w.chain = $chain, w.label = $label, w.cluster = $cluster, w.updatedAt = $timestamp
            WITH w
            UNWIND $tags as tagName
            MERGE (t:Tag {name: tagName})
            MERGE (w)-[:HAS_TAG]->(t)
            """
            async with self.neo4j_driver.session() as session:
                await session.run(query, **record)
        except Exception as e:
            logger.error(f"Neo4j save failed: {e}")

    async def _save_to_cloudflare(self, record):
        # Placeholder for Cloudflare D1 HTTP API call
        pass

db_connector = UniversalDatabaseConnector()
