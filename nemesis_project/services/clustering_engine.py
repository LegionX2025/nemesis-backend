import os
import json
import asyncio
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timezone
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans, DBSCAN
from sklearn.preprocessing import StandardScaler

# Import Universal Database Connector
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from services.database_connector import db_connector
from scripts.data_ingestion_pipeline import DataIngestionPipeline

logger = logging.getLogger("NemesisClusteringEngine")

class NemesisClusterer:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(stop_words='english', max_features=1000)
        self.scaler = StandardScaler()
        
    async def fetch_dataset_from_mongo(self, limit=10000):
        """Fetches active identity nodes from MongoDB for clustering."""
        if db_connector.mongo_db is None:
            return []
            
        col = db_connector.mongo_db["identity_graph"]
        cursor = col.find({}).limit(limit)
        docs = await cursor.to_list(length=limit)
        return docs

    def compute_attribution_clusters(self, docs, n_clusters=None):
        """
        Uses NLP (TF-IDF) on tags, evidence, and identities to find Attribution Similarity.
        Groups wallets that share OSINT signatures, even across chains.
        """
        if not docs:
            return []
            
        corpus = []
        for d in docs:
            # Build a string document for this entity
            text_parts = [d.get("entity_name", "")]
            text_parts.append(d.get("entity_type", ""))
            
            identities = d.get("identities", {})
            for k, v in identities.items():
                if isinstance(v, list):
                    text_parts.extend(v)
            
            raw_evidence = d.get("raw_evidence", [])
            for ev in raw_evidence:
                if isinstance(ev, dict) and "label" in ev:
                    text_parts.append(ev["label"])
                    
            corpus.append(" ".join(text_parts))
            
        # Vectorize
        X = self.vectorizer.fit_transform(corpus)
        
        # Determine optimal K dynamically if not provided (simplified heuristic)
        k = n_clusters if n_clusters else min(len(docs) // 10 + 1, 50)
        k = max(2, min(k, len(docs))) # bounds
        
        if len(docs) < 2:
            k = 1
            
        kmeans = KMeans(n_clusters=k, random_state=42, n_init="auto")
        labels = kmeans.fit_predict(X)
        
        results = []
        for i, d in enumerate(docs):
            res = {
                "wallet_address": d.get("wallet_address", "unknown"),
                "entity_name": d.get("entity_name", "unknown"),
                "cluster_id": int(labels[i]),
                "similarity_type": "Attribution (NLP)"
            }
            results.append(res)
            
        return results

    def compute_peel_chain_clusters(self, docs):
        """
        Uses DBSCAN on numerical/behavioral metrics to find Peel-Chain / Sybil behavior.
        Mock implementation assuming we have transaction counts and confidence scores.
        """
        if not docs:
            return []
            
        features = []
        for d in docs:
            # In a real scenario, we'd query transaction frequencies from trace_engine
            # For now, we use confidence_score and evidence_count as proxy metrics for structure
            conf = d.get("confidence_score", 50)
            timeline = d.get("timeline", [])
            ev_count = sum([t.get("evidence_count", 0) for t in timeline])
            features.append([conf, ev_count])
            
        X = np.array(features)
        X_scaled = self.scaler.fit_transform(X)
        
        # DBSCAN handles non-linear clusters (peel chains often look like dense lines in feature space)
        dbscan = DBSCAN(eps=0.5, min_samples=3)
        labels = dbscan.fit_predict(X_scaled)
        
        results = []
        for i, d in enumerate(docs):
            res = {
                "wallet_address": d.get("wallet_address", "unknown"),
                "entity_name": d.get("entity_name", "unknown"),
                "cluster_id": int(labels[i]),
                "similarity_type": "Peel-Chain Behavior (DBSCAN)"
            }
            results.append(res)
            
        return results
        
    async def run_full_clustering_suite(self):
        """Runs both clustering algorithms and returns formatted results for the dashboard."""
        docs = await self.fetch_dataset_from_mongo(limit=2000) # Batched for memory
        
        if not docs:
            return {"error": "No data found in identity graph."}
            
        attr_clusters = self.compute_attribution_clusters(docs)
        peel_clusters = self.compute_peel_chain_clusters(docs)
        
        # Group by cluster ID for the frontend
        attr_grouped = pd.DataFrame(attr_clusters).groupby("cluster_id").apply(lambda x: x.to_dict(orient="records")).to_dict()
        peel_grouped = pd.DataFrame(peel_clusters).groupby("cluster_id").apply(lambda x: x.to_dict(orient="records")).to_dict()
        
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "attribution_clusters": attr_grouped,
            "peel_chain_clusters": peel_grouped,
            "total_entities_analyzed": len(docs)
        }

    async def ingest_from_file(self, filepath: str):
        """Triggers the DataIngestionPipeline on a newly uploaded file."""
        data_dir = os.path.dirname(filepath)
        filename = os.path.basename(filepath)
        
        pipeline = DataIngestionPipeline(data_dir)
        if filename.endswith(".jsonl"):
            await pipeline.process_jsonl_file(filename)
        elif filename.endswith(".json"):
            await pipeline.process_coinbase_schema(filename)
        else:
            raise ValueError("Unsupported file format for ingestion.")
            
        return pipeline.total_processed

clustering_engine = NemesisClusterer()
