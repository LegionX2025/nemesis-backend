import os
import sys
import json
import logging
import asyncio
import aiohttp
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("NemesisDataIngestor")

load_dotenv()

MONGO_URI = os.getenv("DATABASE_MONGO_URL", os.getenv("VITE_DATABASE_MONGO_URL", "mongodb://localhost:27017"))
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASS = os.getenv("NEO4J_PASSWORD", "password")

CF_ACCOUNT_ID = os.getenv("CLOUDFLARE_ACCOUNT_ID")
CF_API_TOKEN = os.getenv("CLOUDFLARE_API_TOKEN")
CF_D1_ID = os.getenv("CLOUDFLARE_D1_DATABASE_ID")

BATCH_SIZE = 1000

# Try to initialize DB clients
try:
    from pymongo import MongoClient
    mongo_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    mongo_client.server_info()
    mongo_db = mongo_client["blockchain_intel"]
    mongo_col = mongo_db["entities"]
    mongo_col.create_index([("address", 1)], unique=True, sparse=True)
    mongo_col.create_index([("name", "text")])
    MONGO_ENABLED = True
    logger.info("MongoDB connection established.")
except Exception as e:
    MONGO_ENABLED = False
    logger.warning(f"MongoDB disabled: {e}")

try:
    from neo4j import AsyncGraphDatabase
    neo4j_driver = AsyncGraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))
    NEO4J_ENABLED = True
    logger.info("Neo4j connection established.")
except Exception as e:
    NEO4J_ENABLED = False
    logger.warning(f"Neo4j disabled: {e}")

CF_D1_ENABLED = bool(CF_ACCOUNT_ID and CF_API_TOKEN and CF_D1_ID)
if CF_D1_ENABLED:
    logger.info("Cloudflare D1 ingestion enabled.")

async def insert_cloudflare_d1(session, batch):
    """Inserts records into Cloudflare D1 via HTTP API."""
    if not CF_D1_ENABLED: return
    url = f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/d1/database/{CF_D1_ID}/query"
    headers = {"Authorization": f"Bearer {CF_API_TOKEN}", "Content-Type": "application/json"}
    
    # We create a batch of SQL insert statements. 
    # Warning: massive batching can hit limits. We use a single parameterized query with multiple rows if possible, or multiple queries.
    queries = []
    for item in batch:
        address = item.get("address") or item.get("addresses", [""])[0] if item.get("addresses") else "unknown"
        name = item.get("name", "Unknown")
        type_val = item.get("type", "unknown")
        # Ensure strings
        address, name, type_val = str(address), str(name), str(type_val)
        queries.append({
            "sql": "INSERT INTO entities (address, name, type) VALUES (?, ?, ?) ON CONFLICT(address) DO NOTHING",
            "params": [address, name, type_val]
        })
    
    try:
        async with session.post(url, headers=headers, json=queries) as resp:
            if resp.status != 200:
                logger.error(f"D1 Insert Failed: {await resp.text()}")
    except Exception as e:
        logger.error(f"D1 Exception: {e}")

async def insert_neo4j(batch):
    """Inserts nodes into Neo4j."""
    if not NEO4J_ENABLED: return
    query = """
    UNWIND $batch AS row
    MERGE (e:Entity {id: COALESCE(row.address, row.name, "unknown")})
    SET e.name = row.name, e.type = row.type
    """
    try:
        async with neo4j_driver.session() as session:
            await session.run(query, batch=batch)
    except Exception as e:
        logger.error(f"Neo4j Insert Failed: {e}")

def insert_mongo(batch):
    if not MONGO_ENABLED: return
    try:
        # Avoid _id collision issues by removing them if they exist in the batch
        for b in batch: b.pop('_id', None)
        mongo_col.insert_many(batch, ordered=False)
    except Exception as e:
        # Ignore duplicate key errors
        pass

async def process_batch(session, batch):
    # MongoDB is synchronous in pymongo, run in thread
    if MONGO_ENABLED:
        await asyncio.to_thread(insert_mongo, batch)
    
    tasks = []
    if NEO4J_ENABLED:
        tasks.append(insert_neo4j(batch))
    if CF_D1_ENABLED:
        tasks.append(insert_cloudflare_d1(session, batch))
        
    if tasks:
        await asyncio.gather(*tasks)

async def process_jsonl(filepath, session):
    logger.info(f"Processing JSONL file: {filepath}")
    batch = []
    count = 0
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip(): continue
            try:
                record = json.loads(line)
                batch.append(record)
                if len(batch) >= BATCH_SIZE:
                    await process_batch(session, batch)
                    count += len(batch)
                    batch = []
                    logger.info(f"Ingested {count} records from {os.path.basename(filepath)}...")
            except Exception as e:
                pass
        if batch:
            await process_batch(session, batch)
            count += len(batch)
    logger.info(f"Finished {filepath}. Total: {count}")

async def process_json(filepath, session):
    logger.info(f"Processing massive JSON array file: {filepath}")
    try:
        import ijson
    except ImportError:
        logger.error("ijson is required to stream large JSON files. Install via 'pip install ijson'")
        return

    batch = []
    count = 0
    with open(filepath, 'r', encoding='utf-8') as f:
        objects = ijson.items(f, 'item')
        for record in objects:
            batch.append(record)
            if len(batch) >= BATCH_SIZE:
                await process_batch(session, batch)
                count += len(batch)
                batch = []
                logger.info(f"Ingested {count} records from {os.path.basename(filepath)}...")
        if batch:
            await process_batch(session, batch)
            count += len(batch)
    logger.info(f"Finished {filepath}. Total: {count}")

async def main():
    data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
    if not os.path.exists(data_dir):
        logger.error(f"Data directory not found: {data_dir}")
        return

    async with aiohttp.ClientSession() as session:
        for filename in os.listdir(data_dir):
            filepath = os.path.join(data_dir, filename)
            if filename.endswith(".jsonl"):
                await process_jsonl(filepath, session)
            elif filename.endswith(".json"):
                if "schema" in filename: continue
                await process_json(filepath, session)
                
    if NEO4J_ENABLED:
        await neo4j_driver.close()

if __name__ == "__main__":
    asyncio.run(main())
