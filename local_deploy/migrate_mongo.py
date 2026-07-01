import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient

async def migrate():
    print("=========================================")
    print("NEMESIS MongoDB Migration Tool")
    print("=========================================")
    
    local_uri = input("Enter your local MongoDB URI [default: mongodb://localhost:27017]: ").strip()
    if not local_uri:
        local_uri = "mongodb://localhost:27017"
        
    atlas_uri = input("Enter your MongoDB Atlas Connection String: ").strip()
    if not atlas_uri:
        print("Error: MongoDB Atlas URI is required!")
        return

    try:
        print("\nConnecting to databases...")
        local_client = AsyncIOMotorClient(local_uri, serverSelectionTimeoutMS=5000)
        atlas_client = AsyncIOMotorClient(atlas_uri, serverSelectionTimeoutMS=5000)
        
        # Verify connections
        await local_client.server_info()
        await atlas_client.server_info()
        
        # Use nemesis_traces database (or default if defined in atlas_uri)
        try:
            local_db = local_client.get_default_database()
        except:
            local_db = local_client["nemesis_traces"]
            
        try:
            atlas_db = atlas_client.get_default_database()
        except:
            atlas_db = atlas_client["nemesis_traces"]

        collections = await local_db.list_collection_names()
        print(f"\nFound {len(collections)} collections to migrate: {collections}")
        
        for coll_name in collections:
            print(f"Migrating collection: {coll_name}...")
            local_coll = local_db[coll_name]
            atlas_coll = atlas_db[coll_name]
            
            cursor = local_coll.find({})
            docs = await cursor.to_list(length=None)
            
            if docs:
                # Clear existing data in Atlas for a clean migration (optional, uncomment if needed)
                # await atlas_coll.delete_many({})
                
                try:
                    # Insert in chunks to avoid max BSON size errors
                    chunk_size = 1000
                    for i in range(0, len(docs), chunk_size):
                        chunk = docs[i:i + chunk_size]
                        # Handle duplicate key errors gracefully by iterating or using insert_many with ordered=False
                        await atlas_coll.insert_many(chunk, ordered=False)
                    print(f"  -> Migrated {len(docs)} documents.")
                except Exception as e:
                    # Ignore DuplicateKeyError if documents already exist
                    if "E11000" in str(e) or "duplicate key" in str(e):
                        print(f"  -> Merged {len(docs)} documents (skipping duplicates).")
                    else:
                        print(f"  -> Error migrating {coll_name}: {e}")
            else:
                print(f"  -> Collection empty, skipping.")

        print("\n=========================================")
        print("Migration Completed Successfully!")
        print("Please update your .env file with the new MongoDB Atlas URL:")
        print(f"DATABASE_MONGO_URL={atlas_uri}")
        print("=========================================")

    except Exception as e:
        print(f"\n[FATAL ERROR] {e}")

if __name__ == "__main__":
    asyncio.run(migrate())
