import os
import json
import psycopg2
from difflib import SequenceMatcher
from datetime import datetime

class EntityResolutionEngine:
    def __init__(self):
        self.pg_uri = os.getenv("POSTGRES_URI")
        self.mongo_uri = os.getenv("DATABASE_MONGO_URL", "mongodb+srv://MKpBkrUw:Z63zGHQaiYG6rhrb@us-east-1.ufsuw.mongodb.net/blockchain")
        self.entities = []
        
        # Init MongoDB
        try:
            from pymongo import MongoClient
            self.mongo_client = MongoClient(self.mongo_uri)
            self.mongo_db = self.mongo_client["darknet_data"]
            self.mongo_collection = self.mongo_db["resolved_entities"]
            print("✅ [ERE] Connected to MongoDB (darknet_data)")
        except Exception as e:
            print(f"[-] MongoDB Init Error: {e}")
            self.mongo_collection = None
        
    def init_db(self):
        if not self.pg_uri: return
        try:
            conn = psycopg2.connect(self.pg_uri)
            cur = conn.cursor()
            cur.execute("""
                CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
                CREATE TABLE IF NOT EXISTS intel_entities (
                    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                    canonical_name TEXT NOT NULL,
                    entity_type VARCHAR(255),
                    risk_score INTEGER DEFAULT 0,
                    attributes JSONB DEFAULT '{}',
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS intel_aliases (
                    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                    entity_id UUID REFERENCES intel_entities(id) ON DELETE CASCADE,
                    alias TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS intel_relationships (
                    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                    source_id UUID REFERENCES intel_entities(id) ON DELETE CASCADE,
                    target_id UUID REFERENCES intel_entities(id) ON DELETE CASCADE,
                    relationship_type VARCHAR(255),
                    confidence FLOAT,
                    evidence JSONB
                );
            """)
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[-] ERE DB Init Error: {e}")

    def fuzzy_match(self, s1, s2):
        if not s1 or not s2: return 0
        s1 = str(s1).lower().strip()
        s2 = str(s2).lower().strip()
        for suffix in [' inc', ' llc', ' ltd', ' corporation', ' holdings', ' group']:
            s1 = s1.replace(suffix, '')
            s2 = s2.replace(suffix, '')
        return SequenceMatcher(None, s1, s2).ratio() * 100

    def resolve_and_merge(self, new_entity):
        """
        Merge new_entity into self.entities.
        Returns the merged entity dict.
        """
        best_match = None
        best_score = 0
        
        for existing in self.entities:
            if new_entity['name'].lower() in [a.lower() for a in existing.get('aliases', [])] or new_entity['name'].lower() == existing['name'].lower():
                best_score = 100
                best_match = existing
                break
                
            new_attrs = new_entity.get('attributes', {})
            ext_attrs = existing.get('attributes', {})
            
            for k in ['domain', 'email', 'crypto_wallet', 'phone']:
                if k in new_attrs and k in ext_attrs and new_attrs[k] == ext_attrs[k]:
                    best_score = 95
                    best_match = existing
                    break
                    
            score = self.fuzzy_match(new_entity['name'], existing['name'])
            if score > best_score:
                best_score = score
                best_match = existing

        if best_score >= 85 and best_match:
            print(f"🔗 [ERE] Merging '{new_entity['name']}' -> '{best_match['name']}' (Confidence: {best_score:.1f}%)")
            best_match['aliases'] = list(set(best_match.get('aliases', []) + new_entity.get('aliases', []) + [new_entity['name']]))
            
            # Merge lists inside attributes
            for k, v in new_entity.get('attributes', {}).items():
                if isinstance(v, list):
                    best_match['attributes'][k] = list(set(best_match['attributes'].get(k, []) + v))
                else:
                    best_match['attributes'][k] = v
                    
            if 'sources' not in best_match: best_match['sources'] = []
            best_match['sources'].append(new_entity.get('source', 'unknown'))
            return best_match
        else:
            print(f"✨ [ERE] New Entity Isolated: '{new_entity['name']}'")
            new_entity['aliases'] = new_entity.get('aliases', [])
            if 'sources' not in new_entity: new_entity['sources'] = [new_entity.get('source', 'unknown')]
            self.entities.append(new_entity)
            return new_entity

    def ingest_playwright_text(self, source_name, source_url, text_content):
        """
        In a full deployment, this would use a local NLP model (like SpaCy)
        to extract structured entities from raw scraped text.
        For now, we just attach the document text to the base entity's attributes.
        """
        # This will be processed by Gemini Vision in nemesis_comp.py
        pass
