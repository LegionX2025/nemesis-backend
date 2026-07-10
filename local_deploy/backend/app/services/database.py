import os
import logging
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from neo4j import GraphDatabase, exceptions
from dotenv import load_dotenv

# Load environment variables before reading them
load_dotenv()

logger = logging.getLogger("NemesisDB")

class DatabaseConfig:
    MONGO_URI = os.getenv("DATABASE_MONGO_URL")
    NEO4J_URI = os.getenv("NEO4J_URI")
    NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
    NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

class NemesisDB:
    def __init__(self):
        self.mongo_client = None
        self.neo4j_driver = None
        self.db = None
        self._connect()

    def _connect(self):
        # Connect to MongoDB Atlas
        try:
            if DatabaseConfig.MONGO_URI:
                self.mongo_client = MongoClient(DatabaseConfig.MONGO_URI, serverSelectionTimeoutMS=5000)
                # Verify connection
                self.mongo_client.admin.command('ping')
                try:
                    self.db = self.mongo_client.get_database() # Uses default db from URI
                except Exception:
                    self.db = self.mongo_client.get_database('nemesis_db') # Fallback
                logger.info("Successfully connected to MongoDB Atlas.")
            else:
                logger.warning("DATABASE_MONGO_URL not set.")
        except ConnectionFailure as e:
            logger.error(f"Failed to connect to MongoDB Atlas: {e}")

        # Connect to Neo4j Aura
        try:
            if DatabaseConfig.NEO4J_URI and DatabaseConfig.NEO4J_USERNAME and DatabaseConfig.NEO4J_PASSWORD:
                self.neo4j_driver = GraphDatabase.driver(
                    DatabaseConfig.NEO4J_URI, 
                    auth=(DatabaseConfig.NEO4J_USERNAME, DatabaseConfig.NEO4J_PASSWORD)
                )
                self.neo4j_driver.verify_connectivity()
                logger.info("Successfully connected to Neo4j Aura.")
            else:
                logger.warning("Neo4j credentials not fully set in environment.")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j Aura: {e}")

    def get_mongo_collection(self, collection_name: str):
        if self.db is not None:
            return self.db[collection_name]
        raise ConnectionError("MongoDB is not connected.")

    def run_neo4j_query(self, query: str, parameters=None):
        """Runs a Cypher query on the Neo4j database."""
        if not self.neo4j_driver:
            raise ConnectionError("Neo4j is not connected.")
        
        with self.neo4j_driver.session() as session:
            result = session.run(query, parameters or {})
            return [record.data() for record in result]

    def close(self):
        if self.mongo_client:
            self.mongo_client.close()
        if self.neo4j_driver:
            self.neo4j_driver.close()

# Singleton Instance
db_instance = NemesisDB()
