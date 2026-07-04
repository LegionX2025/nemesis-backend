import os
import json
import logging
from datetime import datetime
from services.database import db_instance

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("KBImporter")

KB_DIR = "NEMESIS_KNOWLEDGE_BASE_LIBRARY"

def import_knowledge_base():
    if not os.path.exists(KB_DIR):
        logger.error(f"Directory {KB_DIR} not found.")
        return

    # Create MongoDB collection
    try:
        kb_collection = db_instance.get_mongo_collection("knowledge_base")
    except Exception as e:
        logger.error(f"Cannot get MongoDB collection: {e}")
        return

    docs_inserted = 0
    for root, dirs, files in os.walk(KB_DIR):
        for file in files:
            file_path = os.path.join(root, file)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                doc = {
                    "filename": file,
                    "filepath": file_path,
                    "type": "json" if file.endswith(".json") else "text",
                    "content": content,
                    "imported_at": datetime.utcnow()
                }

                # Try parsing JSON if applicable
                if file.endswith(".json"):
                    try:
                        doc["parsed_json"] = json.loads(content)
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to parse JSON for {file}")

                # Upsert into MongoDB
                kb_collection.update_one(
                    {"filename": file},
                    {"$set": doc},
                    upsert=True
                )
                docs_inserted += 1
                logger.info(f"Imported {file} into Knowledge Base.")

                # If it's the Ontology JSON, we could also pre-populate Neo4j entity types here
                # (Skipping deep Neo4j ontology generation for brevity, relying on MongoDB for full text)
                
            except Exception as e:
                logger.error(f"Error processing {file}: {e}")

    logger.info(f"Successfully imported {docs_inserted} documents into NEMESIS Knowledge Base.")

if __name__ == "__main__":
    logger.info("Starting Knowledge Base Import Process...")
    import_knowledge_base()
    logger.info("Process Complete.")
