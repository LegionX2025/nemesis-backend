from pymongo import MongoClient
from core.config import Config
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        try:
            self.client = MongoClient(Config.MONGO_URL, serverSelectionTimeoutMS=5000)
            self.db = self.client['blockchain_intelligence']
            self.nodes = self.db['nodes']
            self.edges = self.db['edges']
            self.traces = self.db['traces']
            logger.info("MongoDB Connection Successful")
        except Exception as e:
            logger.error(f"MongoDB Connection Failed: {e}")
            self.db = None
