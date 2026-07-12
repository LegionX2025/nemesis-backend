#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Nemesis Lab - Secure Enterprise Python Recon Script
---------------------------------------------------
- Wallet labeling & entity directory
- OSINT Recon engine
- Flashbot MEV monitoring
- Coinbase Intel tracer
- Risk scoring & alerts
- MongoDB storage & Graph linking
- Parallel real-time + batch processing
- Self-healing, retry/backoff, Tor SOCKS support
"""

import os
import json
import asyncio
import logging
import aiohttp
import requests
import pymongo
import websockets
import traceback
import sys
from datetime import datetime
from dotenv import load_dotenv

# Import UniversalDatabaseConnector
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from services.database_connector import db_connector
from tenacity import retry, stop_after_attempt, wait_exponential
from concurrent.futures import ThreadPoolExecutor
from web3 import Web3, HTTPProvider

# -----------------------------
# Load Environment
# -----------------------------
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
HUNTER_API_KEY = os.getenv("HUNTER_API_KEY")
TOR_SOCKS = os.getenv("TOR_SOCKS", "127.0.0.1:9050")
INFURA_ETH_URL = os.getenv("INFURA_ETH_URL")

MAX_PARALLEL = int(os.getenv("PARALLEL_FETCH_LIMIT", 12))

# -----------------------------
# Logging
# -----------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("NemesisRecon")

# -----------------------------
# MongoDB Setup
# -----------------------------
mongo_client = pymongo.MongoClient(MONGO_URI)
db = mongo_client.get_database()
wallet_labels_col = db["wallet_labels"]
entity_dir_col = db["entity_directory"]
osint_profiles_col = db["osint_profiles"]
coinbase_col = db["coinbase_wallets"]

# -----------------------------
# Utilities
# -----------------------------
def utc_now_iso():
    return datetime.utcnow().isoformat() + "Z"

def safe_json(resp):
    try:
        return resp.json()
    except:
        return {}

# -----------------------------
# HTTP / Tor Session Setup
# -----------------------------
def get_session():
    session = requests.Session()
    if TOR_SOCKS:
        session.proxies = {
            "http": f"socks5h://{TOR_SOCKS}",
            "https": f"socks5h://{TOR_SOCKS}"
        }
    return session

session = get_session()

# -----------------------------
# Gemini API Wallet Classifier
# -----------------------------
@retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=2, max=30))
def classify_wallet(wallet_address: str, raw_label: str = None):
    """Send wallet to Gemini API and get deterministic JSON output"""
    payload = {
        "wallet_address": wallet_address,
        "raw_label": raw_label or "",
        "known_wallets": []  # Can fetch from DB if needed
    }
    headers = {"Authorization": f"Bearer {GEMINI_API_KEY}"}
    try:
        resp = session.post("https://gemini-api.example.com/classify", json=payload, headers=headers, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except requests.HTTPError as e:
        logger.error(f"Gemini API HTTP Error: {e}")
        raise
    except Exception as e:
        logger.error(f"Gemini API Exception: {e}")
        raise

# -----------------------------
# OSINT Recon Scraper (Playwright scaffold)
# -----------------------------
async def osint_scraper(wallet_address: str):
    """
    Placeholder for Playwright automation:
    - Scrape OKLink / explorers / forums / social media
    - Extract full URLs, names, usernames, emails, phones
    """
    # This is a scaffold: implement Playwright browser automation here
    await asyncio.sleep(0.5)
    return {
        "wallet": wallet_address,
        "urls": [],
        "emails": [],
        "usernames": [],
        "phones": [],
        "names": [],
        "riskScore": 0.0,
        "sourceConfidence": 0.9,
        "firstSeen": utc_now_iso(),
        "lastSeen": utc_now_iso(),
    }

# -----------------------------
# Coinbase Intel Tracer
# -----------------------------
def trace_coinbase_wallet(wallet_address: str):
    """Fetch Coinbase wallet user info, transactions, link to flagged wallets"""
    try:
        doc = coinbase_col.find_one({"wallet": wallet_address})
        if not doc:
            return {}
        # Analyze transactions & flagged interactions
        flagged = [tx for tx in doc.get("transactions", []) if tx.get("risk") > 0.7]
        return {
            "wallet": wallet_address,
            "user_id": doc.get("coinbase_id"),
            "email": doc.get("email"),
            "flagged_txs": flagged
        }
    except Exception as e:
        logger.error(f"Coinbase tracing error: {e}")
        return {}

# -----------------------------
# Flashbot MEV Interceptor (WebSocket Scaffold)
# -----------------------------
async def flashbot_listener():
    """Connect to Flashbots relayers, intercept bundles, analyze MEV"""
    try:
        async with websockets.connect("wss://relay.flashbots.net") as ws:
            logger.info("Flashbot listener connected")
            async for message in ws:
                bundle = json.loads(message)
                # Analyze bundle: Searcher, Victim, Payload, Gas tips
                logger.debug(f"Bundle intercepted: {bundle.get('hash')}")
    except Exception as e:
        logger.error(f"Flashbot listener error: {e}")
        await asyncio.sleep(5)
        await flashbot_listener()  # Self-healing reconnect

# -----------------------------
# Risk Scoring
# -----------------------------
def compute_risk(wallet_profile: dict, osint_profile: dict):
    score = 0.0
    if osint_profile.get("riskScore"):
        score += osint_profile["riskScore"] * 0.5
    if wallet_profile.get("confidence_score"):
        score += (1.0 - wallet_profile["confidence_score"]) * 0.5
    return min(score, 1.0)

# -----------------------------
# Telegram Alerts
# -----------------------------
def send_telegram_alert(message: str):
    try:
        api_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        resp = requests.post(api_url, json={"chat_id": "@nemesis_alerts", "text": message})
        resp.raise_for_status()
    except Exception as e:
        logger.error(f"Telegram alert failed: {e}")

# -----------------------------
# Main Wallet Processing
# -----------------------------
async def process_wallet(wallet_address: str):
    try:
        # Gemini classification
        wallet_profile = classify_wallet(wallet_address)
        # OSINT scraping
        osint_profile = await osint_scraper(wallet_address)
        # Coinbase tracing
        cb_profile = trace_coinbase_wallet(wallet_address)
        # Risk scoring
        risk_score = compute_risk(wallet_profile, osint_profile)
        # Merge and store in MongoDB
        merged_doc = {
            "wallet": wallet_address,
            "wallet_profile": wallet_profile,
            "osint_profile": osint_profile,
            "coinbase_profile": cb_profile,
            "risk_score": risk_score,
            "lastUpdated": utc_now_iso()
        }
        wallet_labels_col.update_one({"wallet": wallet_address}, {"$set": merged_doc}, upsert=True)
        
        # Build and push Neo4j Hyper-node
        node = {
            "wallet_address": wallet_address,
            "identities": {
                "TWITTER": osint_profile.get("twitter_handles", []),
                "GITHUB": osint_profile.get("github_accounts", []),
                "DOMAIN": osint_profile.get("domains", []),
                "ENS": osint_profile.get("ens_names", [])
            },
            "confidence_score": risk_score * 100,
            "timeline": [{
                "timestamp": utc_now_iso(),
                "event": "Nemesis Recon Scan"
            }],
            "entity_name": wallet_profile.get("entity_name", "Unknown"),
            "entity_type": wallet_profile.get("entity_type", "unknown")
        }
        # Schedule the async DB insert (since this script already runs in an asyncio loop)
        asyncio.create_task(db_connector.save_identity_graph(node))
        # Telegram alert if high risk
        if risk_score > 0.75:
            send_telegram_alert(f"⚠️ High-risk wallet detected: {wallet_address}, score: {risk_score}")
    except Exception:
        logger.error(f"Processing failed for wallet {wallet_address}:\n{traceback.format_exc()}")

# -----------------------------
# Batch Wallet Processor
# -----------------------------
async def batch_process(wallets: list):
    sem = asyncio.Semaphore(MAX_PARALLEL)
    async def sem_task(wallet):
        async with sem:
            await process_wallet(wallet)
    await asyncio.gather(*(sem_task(w) for w in wallets))

# -----------------------------
# Main Async Entry
# -----------------------------
async def main():
    # Example: Fetch wallets from MongoDB queue or batch
    wallet_queue = [doc["wallet"] for doc in wallet_labels_col.find().limit(50)]
    if not wallet_queue:
        logger.warning("No wallets found in database to process.")
        return
    await asyncio.gather(
        batch_process(wallet_queue),
        flashbot_listener()
    )

# -----------------------------
# CLI Entry
# -----------------------------
if __name__ == "__main__":
    asyncio.run(main())