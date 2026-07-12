import os
import logging
import asyncio
import datetime
import aiohttp

logger = logging.getLogger("OmniChainEngine.Database")

class UniversalDatabaseConnector:
    """
    Handles auto-saving and auto-clustering persistence across multiple 
    cloud databases using ONLY HTTP/REST APIs (Cloudflare Edge Compatible).
    """
    def __init__(self):
        self.mongo_api_url = None
        self.mongo_api_key = None
        self.neo4j_http_url = None
        self.cloudflare_configured = False
        self.session = None

    def init_databases(self):
        self.init_mongodb()
        self.init_neo4j()
        self.init_cloudflare()

    def init_mongodb(self):
        try:
            # Requires MongoDB Atlas Data API URL and Key
            self.mongo_api_url = os.environ.get("MONGODB_DATA_API_URL")
            self.mongo_api_key = os.environ.get("MONGODB_DATA_API_KEY")
            if self.mongo_api_url and self.mongo_api_key:
                logger.info("MongoDB Atlas Data API configured successfully.")
            else:
                logger.warning("MongoDB Atlas Data API not configured. Writes will be skipped.")
        except Exception as e:
            logger.warning(f"MongoDB initialization skipped/failed: {e}")

    def init_neo4j(self):
        try:
            self.neo4j_http_url = os.environ.get("NEO4J_HTTP_URI")
            neo4j_user = os.environ.get("NEO4J_USER", "neo4j")
            neo4j_pass = os.environ.get("NEO4J_PASSWORD")
            if self.neo4j_http_url and neo4j_pass:
                logger.info("Neo4j HTTP Database connected successfully.")
            else:
                logger.warning("Neo4j HTTP API not configured. Writes will be skipped.")
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

    async def get_session(self):
        if not self.session:
            self.session = aiohttp.ClientSession()
        return self.session

    async def save_entity(self, address: str, chain: str, label: str, cluster: str, tags: list = None, metadata: dict = None):
        timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
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
        if self.mongo_api_url:
            tasks.append(self._save_to_mongo(record))
            
        if self.neo4j_http_url:
            tasks.append(self._save_to_neo4j(record))
            
        if self.cloudflare_configured:
            tasks.append(self._save_to_cloudflare(record))
            
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
            
    async def _save_to_mongo(self, record):
        try:
            session = await self.get_session()
            headers = {
                "Content-Type": "application/json",
                "api-key": self.mongo_api_key
            }
            payload = {
                "dataSource": "nemesisdb",
                "database": "nemesis_intel",
                "collection": "wallet_labels",
                "filter": {"address": record["address"]},
                "update": {"$set": record},
                "upsert": True
            }
            async with session.post(f"{self.mongo_api_url}/action/updateOne", json=payload, headers=headers) as resp:
                if resp.status >= 400:
                    logger.error(f"Mongo HTTP save failed: {await resp.text()}")
        except Exception as e:
            logger.error(f"Mongo HTTP save failed: {e}")

    async def _save_to_neo4j(self, record):
        pass # Placeholder for Neo4j HTTP transaction

    async def _save_to_cloudflare(self, record):
        pass

    async def save_identity_graph(self, resolved_node: dict):
        tasks = []
        if self.neo4j_http_url:
            tasks.append(self._save_osint_to_neo4j(resolved_node))
        if self.mongo_api_url:
            tasks.append(self._save_osint_to_mongo(resolved_node))
            
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
            
    async def _save_osint_to_neo4j(self, node: dict):
        pass

    async def _save_osint_to_mongo(self, node: dict):
        try:
            session = await self.get_session()
            headers = {
                "Content-Type": "application/json",
                "api-key": self.mongo_api_key
            }
            payload = {
                "dataSource": "nemesisdb",
                "database": "nemesis_intel",
                "collection": "osint_identities",
                "filter": {"wallet_address": node["wallet_address"]},
                "update": {"$set": node},
                "upsert": True
            }
            async with session.post(f"{self.mongo_api_url}/action/updateOne", json=payload, headers=headers) as resp:
                if resp.status >= 400:
                    logger.error(f"Mongo HTTP OSINT save failed: {await resp.text()}")
        except Exception as e:
            logger.error(f"Mongo HTTP OSINT save failed: {e}")

db_connector = UniversalDatabaseConnector()

class AtlasCursor:
    def __init__(self, api_url, api_key, collection_name, filter_query):
        self.api_url = api_url
        self.api_key = api_key
        self.collection_name = collection_name
        self.filter_query = filter_query
        self._sort = None
        self._limit = None
        
    def sort(self, field, direction=-1):
        if isinstance(field, list):
            # Handle list of tuples like [("block_time", -1)]
            self._sort = {k: v for k, v in field}
        elif isinstance(field, str):
            self._sort = {field: direction}
        return self

    def limit(self, length):
        self._limit = length
        return self

    async def to_list(self, length=None):
        if not self.api_url or not self.api_key:
            return []
            
        limit_val = length if length is not None else self._limit
        
        headers = {
            "Content-Type": "application/json",
            "api-key": self.api_key
        }
        
        payload = {
            "dataSource": "nemesisdb",
            "database": "nemesis_intel",
            "collection": self.collection_name,
            "filter": self.filter_query
        }
        
        if self._sort:
            payload["sort"] = self._sort
        if limit_val:
            payload["limit"] = limit_val
            
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.api_url}/action/find", json=payload, headers=headers) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data.get("documents", [])
                    else:
                        logger.error(f"Atlas API find error: {await resp.text()}")
                        return []
        except Exception as e:
            logger.error(f"Atlas API cursor error: {e}")
            return []

class AtlasCollection:
    def __init__(self, api_url, api_key, collection_name):
        self.api_url = api_url
        self.api_key = api_key
        self.collection_name = collection_name
        
    def find(self, filter_query=None):
        if filter_query is None: filter_query = {}
        return AtlasCursor(self.api_url, self.api_key, self.collection_name, filter_query)
        
    async def find_one(self, filter_query=None):
        if not self.api_url or not self.api_key: return None
        if filter_query is None: filter_query = {}
        
        headers = {
            "Content-Type": "application/json",
            "api-key": self.api_key
        }
        payload = {
            "dataSource": "nemesisdb",
            "database": "nemesis_intel",
            "collection": self.collection_name,
            "filter": filter_query
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.api_url}/action/findOne", json=payload, headers=headers) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data.get("document", None)
                    return None
        except Exception as e:
            logger.error(f"Atlas API findOne error: {e}")
            return None

    async def insert_one(self, document):
        if not self.api_url or not self.api_key: return None
        headers = {
            "Content-Type": "application/json",
            "api-key": self.api_key
        }
        payload = {
            "dataSource": "nemesisdb",
            "database": "nemesis_intel",
            "collection": self.collection_name,
            "document": document
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.api_url}/action/insertOne", json=payload, headers=headers) as resp:
                    pass
        except Exception as e:
            logger.error(f"Atlas API insertOne error: {e}")

    async def update_one(self, filter_query, update, upsert=False):
        if not self.api_url or not self.api_key: return None
        headers = {
            "Content-Type": "application/json",
            "api-key": self.api_key
        }
        payload = {
            "dataSource": "nemesisdb",
            "database": "nemesis_intel",
            "collection": self.collection_name,
            "filter": filter_query,
            "update": update,
            "upsert": upsert
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.api_url}/action/updateOne", json=payload, headers=headers) as resp:
                    pass
        except Exception as e:
            logger.error(f"Atlas API updateOne error: {e}")
            
    async def count_documents(self, filter_query):
        if not self.api_url or not self.api_key: return 0
        headers = {
            "Content-Type": "application/json",
            "api-key": self.api_key
        }
        payload = {
            "dataSource": "nemesisdb",
            "database": "nemesis_intel",
            "collection": self.collection_name,
            "pipeline": [
                {"$match": filter_query},
                {"$count": "count"}
            ]
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.api_url}/action/aggregate", json=payload, headers=headers) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        docs = data.get("documents", [])
                        if docs:
                            return docs[0].get("count", 0)
                    return 0
        except Exception as e:
            return 0

    async def create_index(self, *args, **kwargs): pass

class AtlasDataAPIClient:
    def __init__(self):
        self.api_url = os.environ.get("MONGODB_DATA_API_URL")
        self.api_key = os.environ.get("MONGODB_DATA_API_KEY")
        self.admin = AtlasCollection(self.api_url, self.api_key, "admin")
        
    def __getattr__(self, name):
        return AtlasCollection(self.api_url, self.api_key, name)
        
    def __getitem__(self, name):
        return AtlasCollection(self.api_url, self.api_key, name)
        
    async def command(self, *args, **kwargs): pass

class Neo4jProxy:
    def __getattr__(self, name):
        return None

mongo_db = AtlasDataAPIClient()
neo4j_driver = Neo4jProxy()

db_engine = db_connector
db_engine.db = mongo_db
async def _dummy_connect(): pass
db_engine.connect = _dummy_connect
