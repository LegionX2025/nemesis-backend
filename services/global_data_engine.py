import os
import json
import asyncio
import logging
from typing import Dict, Any, List

# MongoDB
from motor.motor_asyncio import AsyncIOMotorClient

# Neo4j
from neo4j import AsyncGraphDatabase

logger = logging.getLogger("GlobalDataEngine")

class GlobalDataEngine:
    def __init__(self):
        # Database Clients
        self.mongo_client = None
        self.mongo_db = None
        
        self.neo4j_driver = None

    async def connect_all(self):
        logger.info("Initializing Global Data Connections...")
        
        # 1. MongoDB Connection
        mongo_url = os.getenv("MONGO_URI") or os.getenv("DATABASE_MONGO_URL")
        if mongo_url:
            try:
                self.mongo_client = AsyncIOMotorClient(mongo_url, serverSelectionTimeoutMS=5000)
                self.mongo_db = self.mongo_client.get_default_database()
                logger.info("[OK] GlobalDataEngine: Connected to MongoDB.")
            except Exception:
                try:
                    self.mongo_db = self.mongo_client["nemesis_traces"]
                    logger.info("[OK] GlobalDataEngine: Connected to MongoDB (nemesis_traces).")
                except Exception as e:
                    logger.error(f"[FAIL] MongoDB Connection: {e}")
        
        # 2. Neo4j Connection
        neo4j_uri = os.getenv("NEO4J_URI")
        neo4j_user = os.getenv("NEO4J_USERNAME", "neo4j")
        neo4j_pass = os.getenv("NEO4J_PASSWORD", "")
        if neo4j_uri:
            try:
                self.neo4j_driver = AsyncGraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_pass))
                await self.neo4j_driver.verify_connectivity()
                logger.info("[OK] GlobalDataEngine: Connected to Neo4j.")
            except Exception as e:
                logger.error(f"[FAIL] Neo4j Connection: {e}")
                self.neo4j_driver = None

    async def global_import(self, trace_data: Dict[str, Any]):
        """Ingests data into all available databases."""
        results = {"mongo": False, "neo4j": False}
        trace_id = trace_data.get("trace_id", "unknown")
        
        # MongoDB: Store the raw document
        if self.mongo_db is not None:
            try:
                await self.mongo_db.traces_data.update_one(
                    {"trace_id": trace_id},
                    {"$set": trace_data},
                    upsert=True
                )
                results["mongo"] = True
            except Exception as e:
                logger.error(f"MongoDB Import Error: {e}")
                
        # Neo4j: Build the graph
        if self.neo4j_driver is not None:
            try:
                async with self.neo4j_driver.session() as session:
                    # Example: merge a central Trace node
                    await session.run(
                        "MERGE (t:Trace {trace_id: $trace_id}) SET t.timestamp = timestamp()",
                        trace_id=trace_id
                    )
                    # Merge addresses and link them
                    addresses = trace_data.get("addresses", [])
                    for addr in addresses:
                        await session.run("""
                            MERGE (w:Wallet {address: $address})
                            MERGE (t:Trace {trace_id: $trace_id})
                            MERGE (w)-[:PART_OF]->(t)
                        """, address=addr, trace_id=trace_id)
                results["neo4j"] = True
            except Exception as e:
                logger.error(f"Neo4j Import Error: {e}")
                
        return results

    async def global_query(self, query: str, db_target: str = "all") -> Dict[str, Any]:
        """Runs a direct query string against the specified database target."""
        # This is a dangerous method in production, usually restricted to admin/internal
        results = {}
        
        if db_target in ["all", "neo4j"] and self.neo4j_driver:
            async with self.neo4j_driver.session() as session:
                try:
                    res = await session.run(query)
                    records = await res.data()
                    results["neo4j"] = records
                except Exception as e:
                    results["neo4j_error"] = str(e)
                    
        return results

    async def global_search(self, search_term: str) -> Dict[str, Any]:
        """Federated search across all DBs for wallets, tx hashes, etc."""
        results = {"mongo": [], "neo4j": []}
        
        # Mongo Search
        if self.mongo_db is not None:
            try:
                # Search traces for this term
                cursor = self.mongo_db.traces_data.find(
                    {"$or": [{"trace_id": search_term}, {"addresses": search_term}]}
                ).limit(10)
                docs = await cursor.to_list(length=10)
                results["mongo"] = [{"trace_id": d.get("trace_id")} for d in docs]
            except Exception as e:
                logger.error(f"Mongo search error: {e}")

        # Neo4j Search
        if self.neo4j_driver is not None:
            try:
                async with self.neo4j_driver.session() as session:
                    res = await session.run(
                        "MATCH (n) WHERE n.address = $term OR n.trace_id = $term RETURN n LIMIT 10",
                        term=search_term
                    )
                    records = await res.data()
                    results["neo4j"] = records
            except Exception as e:
                logger.error(f"Neo4j search error: {e}")
                
        return results

    async def global_export(self) -> str:
        """Triggers a snapshot/export of all databases."""
        # For this prototype, we return status strings.
        # A real system would write out JSONL, Cypher dumps, and SQL dumps, then zip them.
        export_status = {}
        export_status["mongo"] = "Export ready" if self.mongo_db is not None else "Offline"
        export_status["neo4j"] = "Export ready" if self.neo4j_driver else "Offline"
        
        return export_status

global_db = GlobalDataEngine()
