# nemesis/storage/neo4j_graph.py

from typing import Dict, Any, Optional
from neo4j import AsyncGraphDatabase, AsyncDriver
from nemesis.core.config import settings
from nemesis.storage.interfaces import GraphStore
from nemesis.observability.telemetry import logger, tracer

class Neo4jStore(GraphStore):
    def __init__(self):
        self.driver: Optional[AsyncDriver] = None

    async def connect(self):
        if settings.neo4j_uri and "ROTATE" not in settings.neo4j_password:
            try:
                self.driver = AsyncGraphDatabase.driver(
                    settings.neo4j_uri, 
                    auth=(settings.neo4j_user, settings.neo4j_password)
                )
                await self.driver.verify_connectivity()
                logger.info("Neo4j connection established.")
            except Exception as e:
                logger.error(f"Neo4j connection failed: {e}")
                self.driver = None
        else:
            logger.warning("Neo4j URL/credentials not configured. Graph storage will fallback to memory/Mongo.")

    async def close(self):
        if self.driver:
            await self.driver.close()
            logger.info("Neo4j connection closed.")

    @tracer.start_as_current_span("neo4j.add_node")
    async def add_node(self, node_id: str, attributes: Dict[str, Any]):
        if not self.driver: return
        query = """
        MERGE (n:Entity {id: $node_id})
        SET n += $attributes
        """
        try:
            async with self.driver.session() as session:
                await session.run(query, node_id=node_id, attributes=attributes)
        except Exception as e:
            logger.error(f"Failed to add node to Neo4j: {e}")

    @tracer.start_as_current_span("neo4j.add_edge")
    async def add_edge(self, from_id: str, to_id: str, edge_type: str, attributes: Dict[str, Any]):
        if not self.driver: return
        query = f"""
        MATCH (a:Entity {{id: $from_id}})
        MATCH (b:Entity {{id: $to_id}})
        MERGE (a)-[r:{edge_type}]->(b)
        SET r += $attributes
        """
        try:
            async with self.driver.session() as session:
                await session.run(query, from_id=from_id, to_id=to_id, attributes=attributes)
        except Exception as e:
            logger.error(f"Failed to add edge to Neo4j: {e}")

    @tracer.start_as_current_span("neo4j.get_node")
    async def get_node(self, node_id: str) -> Optional[Dict[str, Any]]:
        if not self.driver: return None
        query = "MATCH (n:Entity {id: $node_id}) RETURN n"
        try:
            async with self.driver.session() as session:
                result = await session.run(query, node_id=node_id)
                record = await result.single()
                return dict(record["n"]) if record else None
        except Exception as e:
            logger.error(f"Failed to get node from Neo4j: {e}")
            return None
