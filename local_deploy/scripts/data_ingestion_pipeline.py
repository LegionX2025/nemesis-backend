import os
import sys
import json
import asyncio
import logging
import traceback
from datetime import datetime, timezone

# Add parent directory to path to import services
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from services.database_connector import db_connector

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("NemesisDataIngestor")

class DataIngestionPipeline:
    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        self.total_processed = 0
        self.chunk_size = 1000  # For batching if needed
        
    async def run_all(self):
        """Discovers and runs ingestion on all recognized data files."""
        logger.info(f"Starting Bulk Data Ingestion Pipeline from {self.data_dir}")
        
        # 1. Process JSONL streams (Memory efficient)
        await self.process_jsonl_file("arkham_cex_live.jsonl")
        
        # 2. Process specific JSON structures
        await self.process_coinbase_schema("coinbase.json")
        await self.process_coinbase_schema("coinbase2.json")
        await self.process_coinbase_schema("coinbase3.json")
        
        logger.info(f"Ingestion Complete. Total Entities Processed: {self.total_processed}")

    async def _save_normalized_node(self, name, type_val, addresses, tags, twitter, website):
        """Constructs the Hyper-node identity format and saves it."""
        identities = {
            "TWITTER": [twitter.split("/")[-1]] if twitter else [],
            "GITHUB": [],
            "DOMAIN": [website] if website else [],
            "ENS": []
        }
        
        # Extract identities from tags if present
        for t in tags:
            tag_label = t.get("label", "").lower()
            if ".eth" in tag_label:
                # Basic ENS extraction
                import re
                ens_matches = re.findall(r"([a-z0-9-]+\.eth)", tag_label)
                identities["ENS"].extend(ens_matches)
                
        # For OSINT graphs, we need a root identifier. If no address, we use the name as a mock wallet/entity ID
        root_address = addresses[0] if addresses else f"entity_{name.lower().replace(' ', '_')}"
        
        node = {
            "wallet_address": root_address,
            "identities": identities,
            "confidence_score": 90 if twitter or website else 50, # High confidence if verified external OSINT exists
            "timeline": [{
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "event": "Bulk Data Ingestion",
                "evidence_count": len(tags)
            }],
            "raw_evidence": tags,
            "entity_name": name,
            "entity_type": type_val
        }
        
        await db_connector.save_identity_graph(node)
        self.total_processed += 1
        
        if self.total_processed % 500 == 0:
            logger.info(f"Ingested {self.total_processed} entities so far...")

    async def process_jsonl_file(self, filename: str):
        filepath = os.path.join(self.data_dir, filename)
        if not os.path.exists(filepath):
            logger.warning(f"File not found: {filepath}")
            return
            
        logger.info(f"Processing JSONL stream: {filename}")
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                batch_tasks = []
                for line in f:
                    if not line.strip(): continue
                    try:
                        record = json.loads(line)
                        # Normalize Arkham/Generic JSONL Schema
                        name = record.get("name", "Unknown Entity")
                        type_val = record.get("type", "unknown")
                        addresses = record.get("addresses", [])
                        
                        task = self._save_normalized_node(name, type_val, addresses, [{"label": "Arkham Data"}], None, None)
                        batch_tasks.append(task)
                        
                        if len(batch_tasks) >= self.chunk_size:
                            await asyncio.gather(*batch_tasks)
                            batch_tasks = []
                    except Exception as parse_e:
                        continue
                        
                if batch_tasks:
                    await asyncio.gather(*batch_tasks)
        except Exception as e:
            logger.error(f"Error processing {filename}: {e}")

    async def process_coinbase_schema(self, filename: str):
        filepath = os.path.join(self.data_dir, filename)
        if not os.path.exists(filepath):
            logger.warning(f"File not found: {filepath}")
            return
            
        logger.info(f"Processing JSON file: {filename}")
        try:
            # Memory warning: loading whole JSON. If this crashes on 1GB+ files, we need `ijson`
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            entities = data.get("entities", [])
            batch_tasks = []
            
            for ent in entities:
                name = ent.get("name", "")
                type_val = ent.get("type", "")
                addresses = ent.get("addresses") or []
                tags = ent.get("populatedTags", [])
                twitter = ent.get("twitter", "")
                website = ent.get("website", "")
                
                task = self._save_normalized_node(name, type_val, addresses, tags, twitter, website)
                batch_tasks.append(task)
                
                if len(batch_tasks) >= self.chunk_size:
                    await asyncio.gather(*batch_tasks)
                    batch_tasks = []
                    
            if batch_tasks:
                await asyncio.gather(*batch_tasks)
                
        except MemoryError:
            logger.critical(f"OOM Error reading {filename}. Use a streaming JSON parser (like ijson) for this massive file.")
        except Exception as e:
            logger.error(f"Error processing {filename}: {e}")

if __name__ == "__main__":
    data_directory = os.path.join(os.path.dirname(__file__), '..', 'data')
    pipeline = DataIngestionPipeline(data_directory)
    asyncio.run(pipeline.run_all())
