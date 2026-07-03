import os
import sys
import ijson
import pymongo
from pymongo import MongoClient
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

MONGO_URL = os.environ.get("DATABASE_MONGO_URL")
if not MONGO_URL:
    print("[!] DATABASE_MONGO_URL is not set in .env")
    sys.exit(1)

print(f"[*] Connecting to MongoDB Atlas: {MONGO_URL[:40]}...")
client = MongoClient(MONGO_URL)
db = client.get_default_database() or client['blockchain']

def import_json_chunked(file_path, collection_name, chunk_size=5000):
    if not os.path.exists(file_path):
        print(f"[!] File not found: {file_path}")
        return

    collection = db[collection_name]
    print(f"[*] Starting import for {file_path} into '{collection_name}' collection")
    
    start_time = time.time()
    batch = []
    total_inserted = 0
    
    try:
        with open(file_path, 'rb') as f:
            # Detect if it's an array of objects
            # ijson.items yields individual objects from the top-level array
            objects = ijson.items(f, 'item')
            
            for obj in objects:
                batch.append(obj)
                
                if len(batch) >= chunk_size:
                    collection.insert_many(batch, ordered=False)
                    total_inserted += len(batch)
                    print(f"[+] Inserted {total_inserted} records so far...")
                    batch = []
                    
            # Insert remaining
            if batch:
                collection.insert_many(batch, ordered=False)
                total_inserted += len(batch)
                
    except Exception as e:
        print(f"[!] Error during parsing {file_path}: {e}")
        print("[*] Trying fallback line-by-line parsing (JSONL format)...")
        # Fallback if it's JSONL
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                import json
                for line in f:
                    if line.strip():
                        batch.append(json.loads(line))
                    if len(batch) >= chunk_size:
                        collection.insert_many(batch, ordered=False)
                        total_inserted += len(batch)
                        print(f"[+] Inserted {total_inserted} records so far...")
                        batch = []
                if batch:
                    collection.insert_many(batch, ordered=False)
                    total_inserted += len(batch)
        except Exception as e2:
             print(f"[!] Fallback failed: {e2}")
        
    end_time = time.time()
    print(f"[*] Finished importing {total_inserted} records in {end_time - start_time:.2f} seconds.\n")

if __name__ == "__main__":
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    
    files_to_import = {
        "blockchain.entity.json": "entities",
        "blockchain.nodes.json": "nodes",
        "blockchain.edges.json": "edges",
        "blockchain.bridges.json": "bridges",
        "blockchain.vasp.json": "vasp",
        "blockchain.global_directory.json": "global_directory",
        "blockchain.rpcs.json": "rpcs"
    }
    
    for filename, col_name in files_to_import.items():
        file_path = os.path.join(data_dir, filename)
        if os.path.exists(file_path):
             import_json_chunked(file_path, col_name)
