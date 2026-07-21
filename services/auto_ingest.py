import os
import time
import json
import datetime
import threading
import random

class AutoIngestPipeline:
    def __init__(self):
        self.is_running = False
        self.memory_dir = os.path.join(os.getcwd(), "datasets")
        os.makedirs(self.memory_dir, exist_ok=True)
        self.dataset_path = os.path.join(self.memory_dir, "raw_telemetry.jsonl")
        
    def fetch_mock_osint(self):
        # Mocking OSINT/Blockchain telemetry fetch for the ingestion engine
        threat_actors = ["Lazarus", "LockBit", "Conti_Remnant", "ScatteredSpider"]
        return {
            "source": "Global Threat Intel Feed",
            "actor": random.choice(threat_actors),
            "wallet": f"0x{random.randbytes(20).hex()}",
            "activity": "Obfuscation Mix",
            "confidence": round(random.uniform(0.6, 0.99), 2)
        }

    def _ingest_loop(self):
        while self.is_running:
            print("[AUTO-INGEST] Fetching global intelligence...")
            data = self.fetch_mock_osint()
            
            record = {
                "timestamp": datetime.datetime.now().isoformat(),
                "event": data
            }
            
            with open(self.dataset_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record) + "\n")
            
            # Here we would normally pipe to core.nemesis_llm.nemesis_ai_engine.auto_teach(data)
            # but we run this asynchronously to avoid blocking
            
            time.sleep(10) # Ingest every 10 seconds

    def start(self):
        if not self.is_running:
            self.is_running = True
            t = threading.Thread(target=self._ingest_loop, daemon=True)
            t.start()
            print("[AUTO-INGEST] Pipeline started.")

    def stop(self):
        self.is_running = False
        print("[AUTO-INGEST] Pipeline stopped.")

    def get_status(self):
        try:
            with open(self.dataset_path, "r", encoding="utf-8") as f:
                count = sum(1 for line in f)
        except Exception:
            count = 0
            
        return {
            "status": "RUNNING" if self.is_running else "STOPPED",
            "total_records_ingested": count
        }

ingest_engine = AutoIngestPipeline()
