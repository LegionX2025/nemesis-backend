import sqlite3
import json
import logging
from datetime import datetime
import os

logger = logging.getLogger("OmniChainEngine.IntelligenceLake")

class IntelligenceLake:
    def __init__(self, db_path="intelligence_lake.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS entity_profiles (
                    address TEXT PRIMARY KEY,
                    profile_data TEXT,
                    last_updated TIMESTAMP
                )
            ''')
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Failed to initialize Intelligence Lake: {e}")

    def upsert_profile(self, address: str, profile_data: dict):
        """
        Upserts an IntelligenceProfile (JSON-LD format) into the database.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            address_lower = address.lower()
            
            # Upsert logic
            cursor.execute('''
                INSERT INTO entity_profiles (address, profile_data, last_updated)
                VALUES (?, ?, ?)
                ON CONFLICT(address) DO UPDATE SET
                    profile_data=excluded.profile_data,
                    last_updated=excluded.last_updated
            ''', (address_lower, json.dumps(profile_data), datetime.utcnow()))
            
            conn.commit()
            conn.close()
            logger.info(f"Intelligence profile upserted for {address_lower}")
        except Exception as e:
            logger.error(f"Failed to upsert profile for {address}: {e}")

    def get_profile(self, address: str) -> dict:
        """
        Retrieves an IntelligenceProfile by address. Returns None if not found.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            address_lower = address.lower()
            
            cursor.execute('SELECT profile_data FROM entity_profiles WHERE address = ?', (address_lower,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                logger.info(f"Intelligence Lake cache HIT for {address_lower}")
                return json.loads(row[0])
            return None
        except Exception as e:
            logger.error(f"Failed to get profile for {address}: {e}")
            return None

# Singleton instance
intelligence_lake = IntelligenceLake()
