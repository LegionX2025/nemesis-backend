import os
import json
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import ijson # using ijson for streaming large JSON files without loading entirely into memory
from dotenv import load_dotenv
import time

load_dotenv()

MONGO_URI = os.getenv("DATABASE_MONGO_URL")
if not MONGO_URI:
    print("Error: DATABASE_MONGO_URL not found in .env")
    exit(1)

# Using database nemesisdb as specified in the connection string
DB_NAME = "nemesisdb"

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
CHUNK_SIZE = 5000

async def migrate_file(db, filename, collection_name):
    file_path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(file_path):
        print(f"Skipping {filename}: File not found.")
        return

    print(f"Starting migration for {filename} -> collection: {collection_name}")
    collection = db[collection_name]
    
    # We use ijson to stream the file if it's a JSON array
    try:
        with open(file_path, "rb") as f:
            objects = ijson.items(f, 'item')
            batch = []
            total_inserted = 0
            
            for obj in objects:
                batch.append(obj)
                if len(batch) >= CHUNK_SIZE:
                    try:
                        await collection.insert_many(batch, ordered=False)
                    except Exception as e:
                        pass # Ignore duplicate key errors if resuming
                    total_inserted += len(batch)
                    print(f"[{collection_name}] Inserted {total_inserted} records...")
                    batch = []
                    
            if batch:
                try:
                    await collection.insert_many(batch, ordered=False)
                except Exception as e:
                    pass
                total_inserted += len(batch)
                
            print(f"✅ Completed {filename}. Total inserted: {total_inserted}")
    except Exception as e:
        print(f"Error processing {filename} as array: {e}")
        # Fallback to reading line-by-line if it's JSONL
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                batch = []
                total_inserted = 0
                for line in f:
                    line = line.strip()
                    if not line: continue
                    try:
                        batch.append(json.loads(line))
                    except: continue
                    
                    if len(batch) >= CHUNK_SIZE:
                        try:
                            await collection.insert_many(batch, ordered=False)
                        except: pass
                        total_inserted += len(batch)
                        print(f"[{collection_name}] Inserted {total_inserted} records...")
                        batch = []
                if batch:
                    try:
                        await collection.insert_many(batch, ordered=False)
                    except: pass
                    total_inserted += len(batch)
                print(f"✅ Completed {filename}. Total inserted: {total_inserted}")
        except Exception as e2:
             print(f"Failed fallback for {filename}: {e2}")

async def main():
    print(f"Connecting to MongoDB Atlas...")
    client = AsyncIOMotorClient(MONGO_URI)
    db = client[DB_NAME]
    
    files_to_migrate = [
        ("blockchain.entity.json", "entities"),
        ("blockchain.vasp.json", "vasps"),
        ("blockchain.nodes.json", "nodes"),
        ("blockchain.rpcs.json", "rpcs"),
        ("blockchain.global_directory.json", "global_directory"),
        ("blockchain.bridges.json", "bridges")
    ]
    
    start_time = time.time()
    
    # We can run these sequentially to avoid overloading the memory/network
    for filename, collection in files_to_migrate:
        await migrate_file(db, filename, collection)
        
    print(f"\n🎉 Migration Complete in {time.time() - start_time:.2f} seconds!")

if __name__ == "__main__":
    asyncio.run(main())
