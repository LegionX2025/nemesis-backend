import logging
from typing import List, Dict, Any
from services.database import db_instance
from services.db_schemas import GraphSchemas

logger = logging.getLogger("NemesisGraph")

class GraphEngine:
    def __init__(self):
        self.db = db_instance

    def ingest_transaction(self, from_address: str, to_address: str, tx_hash: str, amount: float, asset: str, timestamp: int):
        """Creates nodes and relationships for a blockchain transaction in Neo4j."""
        try:
            # Create/Merge sender
            self.db.run_neo4j_query(GraphSchemas.MERGE_WALLET, {"address": from_address, "chain": "UNKNOWN"})
            # Create/Merge receiver
            self.db.run_neo4j_query(GraphSchemas.MERGE_WALLET, {"address": to_address, "chain": "UNKNOWN"})
            
            # Create transaction edge
            params = {
                "from_address": from_address,
                "to_address": to_address,
                "tx_hash": tx_hash,
                "amount": amount,
                "asset": asset,
                "timestamp": timestamp
            }
            self.db.run_neo4j_query(GraphSchemas.LINK_WALLET_TRANSACTION, params)
            logger.debug(f"Ingested TX {tx_hash} into Knowledge Graph.")
        except Exception as e:
            logger.error(f"Failed to ingest transaction into graph: {e}")

    def label_wallet(self, address: str, entity_name: str, entity_type: str, confidence: float):
        """Links a wallet to a real-world entity (e.g. Exchange, Sanctioned individual)."""
        try:
            self.db.run_neo4j_query(GraphSchemas.MERGE_ENTITY, {"name": entity_name, "type": entity_type})
            self.db.run_neo4j_query(GraphSchemas.LINK_WALLET_TO_ENTITY, {
                "address": address,
                "name": entity_name,
                "confidence": confidence
            })
            logger.info(f"Labeled {address} as {entity_name} ({entity_type}).")
        except Exception as e:
            logger.error(f"Failed to label wallet in graph: {e}")

    def find_shortest_path(self, start_addr: str, end_addr: str):
        """Lang-Graph integration point: Pathfinding between two entities."""
        try:
            result = self.db.run_neo4j_query(GraphSchemas.FIND_SHORTEST_PATH, {
                "start_addr": start_addr,
                "end_addr": end_addr
            })
            return result
        except Exception as e:
            logger.error(f"Failed to find shortest path: {e}")
            return None

graph_engine = GraphEngine()
