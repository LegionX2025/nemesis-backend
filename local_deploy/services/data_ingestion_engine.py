import os
import sys
import json
import logging
import asyncio
from pymongo import MongoClient, UpdateOne
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("DataIngestion")

# MongoDB connection
MONGO_URI = "mongodb+srv://nemesis:nemesis2026@nemesisdb.vir5vg2.mongodb.net/?appName=nemesisdb"
client = MongoClient(MONGO_URI)
db = client.get_database("nemesis_intel")
collection_entities = db.get_collection("global_entities")
collection_arkham = db.get_collection("arkham_intel")
collection_vasp = db.get_collection("vasp_directory")

# GraphDB Connection (Neo4j)
try:
    from services.graph_db import neo4j_db
except ImportError:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from services.graph_db import neo4j_db


DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

async def ingest_jsonl(file_path, collection, batch_size=1000, parse_func=None):
    if not os.path.exists(file_path):
        logger.warning(f"File not found: {file_path}")
        return

    logger.info(f"Starting ingestion for {file_path} into {collection.name}")
    operations = []
    count = 0
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue
            try:
                doc = json.loads(line)
                if parse_func:
                    doc = parse_func(doc)
                
                if doc:
                    # Upsert based on an identifier. Let's assume 'address' or 'id'
                    doc_id = doc.get("address", doc.get("id", doc.get("_id")))
                    if doc_id:
                        operations.append(UpdateOne({"_id": doc_id}, {"$set": doc}, upsert=True))
                    else:
                        operations.append(UpdateOne({"_raw": line.strip()[:50]}, {"$set": doc}, upsert=True))
                    
                if len(operations) >= batch_size:
                    collection.bulk_write(operations, ordered=False)
                    count += len(operations)
                    logger.info(f"Inserted {count} records into {collection.name}")
                    operations = []
            except Exception as e:
                logger.error(f"Error parsing line: {e}")
                
    if operations:
        collection.bulk_write(operations, ordered=False)
        count += len(operations)
        logger.info(f"Inserted final batch. Total {count} records into {collection.name}")

async def ingest_json_array(file_path, collection, batch_size=1000):
    """Fallback for standard JSON arrays that fit in memory, or use ijson for large files."""
    if not os.path.exists(file_path):
        logger.warning(f"File not found: {file_path}")
        return

    logger.info(f"Starting ingestion for {file_path} into {collection.name}")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if not isinstance(data, list):
                if isinstance(data, dict):
                    # Sometimes the array is inside a key
                    for key, val in data.items():
                        if isinstance(val, list):
                            data = val
                            break
                if not isinstance(data, list):
                    data = [data]
            
            operations = []
            count = 0
            for doc in data:
                doc_id = doc.get("address", doc.get("id", doc.get("_id")))
                if doc_id:
                    operations.append(UpdateOne({"_id": doc_id}, {"$set": doc}, upsert=True))
                else:
                    # Just insert if no ID can be inferred
                    operations.append(UpdateOne({"_raw_doc": str(doc)[:50]}, {"$set": doc}, upsert=True))
                
                if len(operations) >= batch_size:
                    collection.bulk_write(operations, ordered=False)
                    count += len(operations)
                    logger.info(f"Inserted {count} records into {collection.name}")
                    operations = []
            
            if operations:
                collection.bulk_write(operations, ordered=False)
                count += len(operations)
                logger.info(f"Inserted final batch. Total {count} records into {collection.name}")
    except MemoryError:
        logger.error(f"File {file_path} is too large to parse into memory. Convert to JSONL or use stream parsing.")
    except Exception as e:
        logger.error(f"Error ingesting {file_path}: {e}")

async def build_neo4j_graph(limit=1000):
    """
    Sample function to sync MongoDB entities into Neo4j
    In a real massive DB, we'd run this asynchronously or sync on the fly.
    """
    logger.info("Syncing a sample of MongoDB entities to Neo4j...")
    await neo4j_db.connect()
    
    docs = collection_entities.find().limit(limit)
    for doc in docs:
        address = doc.get("address")
        if not address:
            continue
        
        chain = doc.get("chain", "ETH")
        tags = doc.get("tags", [])
        entity_type = doc.get("entity", "Unknown")
        cluster = doc.get("cluster", "Unclustered")
        
        await neo4j_db.auto_save_entity(
            address=address,
            chain=chain,
            entity_type=entity_type,
            cluster=cluster,
            dom_tags=tags,
            scores={"Confidence_Score": 85},
            osint_evidence=[]
        )
    logger.info("Neo4j sync complete.")
    await neo4j_db.close()

async def main():
    logger.info("--- Data Ingestion Engine Started ---")
    
    # 1. Ingest JSONL (Large streaming files)
    arkham_file = os.path.join(DATA_DIR, "arkham_cex_live.jsonl")
    await ingest_jsonl(arkham_file, collection_arkham, batch_size=5000)
    
    # 2. Ingest JSON Arrays
    vasp_file = os.path.join(DATA_DIR, "blockchain.vasp.json")
    await ingest_json_array(vasp_file, collection_vasp)
    
    global_dir_file = os.path.join(DATA_DIR, "blockchain.global_directory.json")
    await ingest_json_array(global_dir_file, collection_entities)
    
    bridges_file = os.path.join(DATA_DIR, "blockchain.bridges.json")
    await ingest_json_array(bridges_file, collection_entities)
    
    # Optional: populate graph
    await build_neo4j_graph(limit=500)
    
    logger.info("--- Data Ingestion Completed ---")

if __name__ == "__main__":
    try:
        client.admin.command('ping')
        logger.info("Pinged your deployment. You successfully connected to MongoDB!")
    except Exception as e:
        logger.error(f"MongoDB connection failed: {e}")
        exit(1)
        
    asyncio.run(main())
