import os
import json
import asyncio
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from neo4j import AsyncGraphDatabase
from dotenv import load_dotenv

# Load env variables from root cases/.env
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger("AutoImporter")

KB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "NEMESIS_KNOWLEDGE_BASE_LIBRARY")

async def main():
    mongo_url = os.getenv("DATABASE_MONGO_URL")
    neo4j_uri = os.getenv("NEO4J_URI")
    neo4j_user = os.getenv("NEO4J_USERNAME", "neo4j")
    neo4j_pass = os.getenv("NEO4J_PASSWORD", "")

    logger.info("Initializing NEMESIS Database Schema & KB Auto-Import...")

    # 1. Connect to MongoDB Atlas
    mongo_client = None
    db = None
    if mongo_url:
        try:
            mongo_client = AsyncIOMotorClient(mongo_url, serverSelectionTimeoutMS=5000)
            db = mongo_client.get_default_database()
            # Test ping
            await mongo_client.admin.command('ping')
            logger.info("Connected to MongoDB Atlas successfully.")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            return
    else:
        logger.error("No DATABASE_MONGO_URL found in .env")
        return

    # 2. Connect to Neo4j Aura
    neo4j_driver = None
    if neo4j_uri:
        try:
            neo4j_driver = AsyncGraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_pass))
            await neo4j_driver.verify_connectivity()
            logger.info("Connected to Neo4j Aura successfully.")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            return
    else:
        logger.error("No NEO4J_URI found in .env")
        return

    # 3. Import JSON Ontologies (GBEO, GBIO)
    gbeo_file = os.path.join(KB_PATH, "gbeo_v4_ontology.json")
    if os.path.exists(gbeo_file):
        with open(gbeo_file, 'r', encoding='utf-8') as f:
            gbeo_data = json.load(f)
            
            # Store raw in Mongo
            await db.knowledge_base.update_one(
                {"document": "gbeo_v4_ontology"},
                {"$set": {"content": gbeo_data}},
                upsert=True
            )
            logger.info("Imported GBEO v4 into MongoDB.")
            
            # Populate Neo4j Schema
            async with neo4j_driver.session() as session:
                tags = gbeo_data.get("entity_tags", [])
                for tag in tags:
                    await session.run("MERGE (t:OntologyTag {name: $tag})", tag=tag)
                
                networks = gbeo_data.get("networks", {})
                for family, chains in networks.items():
                    await session.run("MERGE (f:ChainFamily {name: $family})", family=family)
                    for chain in chains:
                        await session.run("""
                            MERGE (c:Chain {name: $chain})
                            MERGE (f:ChainFamily {name: $family})
                            MERGE (c)-[:BELONGS_TO_FAMILY]->(f)
                        """, chain=chain, family=family)
            logger.info("Imported GBEO v4 relationships into Neo4j.")

    # 4. Import Text Knowledge Base Files
    if os.path.exists(KB_PATH):
        txt_files = [f for f in os.listdir(KB_PATH) if f.endswith('.txt')]
        for txt_file in txt_files:
            filepath = os.path.join(KB_PATH, txt_file)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # Insert to Mongo for RAG / LangGraph Context
                await db.knowledge_base.update_one(
                    {"document": txt_file},
                    {"$set": {"content": content, "type": "manual_intelligence"}},
                    upsert=True
                )
                
                # Link generic KB node in Neo4j
                async with neo4j_driver.session() as session:
                    await session.run("""
                        MERGE (kb:KnowledgeDocument {title: $title})
                    """, title=txt_file)
                    
        logger.info(f"Imported {len(txt_files)} text documents into MongoDB & Neo4j.")

    # Cleanup
    mongo_client.close()
    await neo4j_driver.close()
    logger.info("NEMESIS Auto-Import Complete!")

if __name__ == "__main__":
    asyncio.run(main())
