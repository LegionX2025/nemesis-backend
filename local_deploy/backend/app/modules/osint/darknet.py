"""
 - All-in-one OSINT & darknet crawler (Enhanced Edition v5 - OSINT Recon)

Features:
- Auto-create venv and install dependencies if needed, re-executes inside venv
- Auto-start Tor (Windows: tor.exe, Linux/macOS: tor) and verify via check.torproject.org
- Multi-DB support: MongoDB (URI), SQLite, MySQL, PostgreSQL
- Recursive multithreaded crawling with query-parameter expansion
- 🧠 UIE REGEX ENGINE (v1): Robust entity extraction
- 🧠 NEMESIS INTELLIGENCE ONTOLOGY v3.0: Unified Entity Matrix & Autonomous Task Framework
- Real-time insert into DB + append newline-delimited JSON (export.jsonl)
- Real-time auto-export to CSV for extracted entities
- 🚀 ADVANCED RICH UI: Modern Interactive Console Tables & Telemetry
- Autonomous Subprocess OSINT Mapper (Auto-opens in secondary console with Auto-RECON)
"""

import os
import sys
import time
import json
import csv
import re
import hashlib
import random
import threading
import subprocess
import webbrowser
import socket
import concurrent.futures
from collections import deque
from queue import Queue, Empty
from datetime import datetime, timezone
from urllib.parse import urlparse, urljoin, parse_qs, urlencode
from bs4 import XMLParsedAsHTMLWarning
import warnings

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

import requests

proxies = {
    "http": "socks5h://127.0.0.1:9050",
    "https": "socks5h://127.0.0.1:9050"
}

# Tor check moved to post-startup
# -------------------- VENV BOOTSTRAP & DEPENDENCIES --------------------
VENV_DIR = os.path.join(os.getcwd(), "venv")
IN_VENV_FLAG = "INTEL_CRAWLER_IN_VENV"
REQUIRED_PKGS = [
    "requests[socks]>=2.31.0",
    "beautifulsoup4>=4.12.2",
    "pymongo>=4.4.0",
    "psycopg2-binary>=2.9.7",
    "mysql-connector-python>=8.0.32",
    "sqlalchemy>=2.0.20",
    "lxml>=4.9.3",
    "fake_useragent>=1.1.0",
    "python-dotenv>=1.0.0",
    "rich>=13.5.0",
    "stem>=1.8.1",
    "PySocks>=1.7.1",
    "neo4j>=5.10.0"
]

def create_venv_and_install():
    if os.environ.get(IN_VENV_FLAG) == "1":
        return

    if not os.path.isdir(VENV_DIR):
        print("[*] Creating virtual environment at ./venv ...", flush=True)
        import venv
        venv.EnvBuilder(with_pip=True).create(VENV_DIR)

    if os.name == "nt":
        python_bin = os.path.join(VENV_DIR, "Scripts", "python.exe")
        pip_call = [python_bin, "-m", "pip", "install", "--upgrade", "pip"]
    else:
        python_bin = os.path.join(VENV_DIR, "bin", "python")
        pip_call = [python_bin, "-m", "pip", "install", "--upgrade", "pip"]

    try:
        subprocess.check_call(pip_call, stdout=subprocess.DEVNULL)
    except Exception as e:
        print(f"[!] Failed to upgrade pip in venv: {e}", flush=True)

    for pkg in REQUIRED_PKGS:
        try:
            print(f"[*] Ensuring package: {pkg}", flush=True)
            subprocess.check_call([python_bin, "-m", "pip", "install", pkg], stdout=subprocess.DEVNULL)
        except Exception as e:
            print(f"[!] Failed to install {pkg}: {e}", flush=True)

    env = os.environ.copy()
    env[IN_VENV_FLAG] = "1"
    print("[*] Re-executing script inside venv...", flush=True)
    
    try:
        ret_code = subprocess.call([python_bin] + sys.argv, env=env)
        sys.exit(ret_code)
    except KeyboardInterrupt:
        # Gracefully handle Ctrl+C in the parent venv wrapper
        sys.exit(0)
    except Exception as e:
        print(f"[!] Failed to execute venv Python: {e}", flush=True)
        sys.exit(1)

create_venv_and_install()

# -------------------- IMPORTS (after venv ensured) --------------------
import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from dotenv import load_dotenv

# API & UI Imports
from flask import Flask, request, jsonify, Response, render_template
from flask_cors import CORS
from rich.console import Console
from rich.live import Live
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.tree import Tree
from rich.align import Align
from rich import box

# DB drivers
try:
    from pymongo import MongoClient
except Exception:
    MongoClient = None
try:
    import sqlite3
except Exception:
    sqlite3 = None
try:
    import mysql.connector as mysql_connector
except Exception:
    mysql_connector = None
try:
    import psycopg2
except Exception:
    psycopg2 = None

load_dotenv()
console = Console()

# -------------------- CONFIG & GLOBALS --------------------
AUTONOMOUS_MODE = os.getenv("VITE_CRAWLER_ENABLED", "false").lower() == "true"
USE_TOR = os.getenv("VITE_TOR_AUTO_START", "true").lower() == "true"
TOR_PORT = os.getenv("VITE_TOR_SOCKS_PORT", "9050")
TOR_CHECK_URL = "http://check.torproject.org"
TOR_PROXY = {"http": f"socks5h://127.0.0.1:{TOR_PORT}", "https": f"socks5h://127.0.0.1:{TOR_PORT}"}

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
MAX_WORKERS = int(os.getenv("VITE_CRAWLER_MAX_THREADS", 10))
SAVE_STATE_INTERVAL = 30
STATE_FILE = "state.json"
EXPORT_JSONL = "export.jsonl"
EXPORT_CSV = "entities_export.csv"
SEED_FILE = "darknet_urls.txt"
KEYWORDS_FILE = "keywords.txt"
PLATFORMS_FILE = "platforms.json"

DEFAULT_KEYWORDS = ["bitcoin", "ethereum", "ransomware", "login verify", "account support", "private key"]

# 🧠 NEMESIS INTELLIGENCE ONTOLOGY v3.0
NEMESIS_ONTOLOGY = {
    "PERSON": {
        "tasks": ["T1: Identity verification", "T2: Alias resolution", "T3: Social graph mapping", "T5: Phone ↔ email ↔ wallet linking", "T6: Risk scoring"]
    },
    "ORGANIZATION": {
        "tasks": ["T9: Corporate registry lookup", "T10: Director/shareholder mapping", "T11: Domain/IP linkage", "T13: Fraud cluster detection"]
    },
    "BANK_ACCOUNT": {
        "tasks": ["T15: Inflow/outflow tracing", "T16: Transaction clustering", "T18: AML risk scoring", "T20: Fiat → crypto bridge detection"]
    },
    "CRYPTO_WALLET": {
        "tasks": ["T21: Transaction graph building", "T22: Multi-hop tracing", "T25: Mixer detection", "T27: Cross-chain bridging detection"]
    },
    "DOMAIN": {
        "tasks": ["T28: WHOIS lookup", "T29: DNS enumeration", "T30: SSL certificate analysis", "T32: Hosting/IP correlation"]
    },
    "IP_ADDRESS": {
        "tasks": ["T34: Geolocation", "T35: ISP identification", "T36: Threat scoring", "T38: Infrastructure mapping"]
    },
    "EMAIL": {
        "tasks": ["T39: Breach lookup", "T40: Domain correlation", "T41: Alias detection", "T42: Social account linking"]
    },
    "PHONE": {
        "tasks": ["T44: Carrier lookup", "T46: Social linkage", "T48: Communication graph mapping"]
    },
    "FILE_DOC": {
        "tasks": ["T49: Metadata extraction", "T50: Hash generation", "T52: IoC extraction"]
    },
    "MALWARE_IOC": {
        "tasks": ["T64: Threat attribution", "T65: Signature matching", "T67: Campaign detection"]
    },
    "NETWORK_ENTITY": {
        "tasks": ["T71: Network mapping", "T72: Endpoint tracing"]
    }
}

# Regex Type -> Ontology Class Mapping
ONTOLOGY_MAP = {
    "person": "PERSON", "usernames": "PERSON", "ssn": "PERSON", "device": "PERSON",
    "org": "ORGANIZATION",
    "domain": "DOMAIN", "url_path": "DOMAIN",
    "email": "EMAIL",
    "ip": "IP_ADDRESS",
    "eth": "CRYPTO_WALLET", "btc": "CRYPTO_WALLET", "sol": "CRYPTO_WALLET",
    "bitcoin": "CRYPTO_WALLET", "ethereum": "CRYPTO_WALLET", "bsc": "CRYPTO_WALLET", 
    "solana": "CRYPTO_WALLET", "ripple": "CRYPTO_WALLET", "avalanche": "CRYPTO_WALLET", 
    "tron": "CRYPTO_WALLET", "polygon": "CRYPTO_WALLET", "litecoin": "CRYPTO_WALLET", 
    "bitcoin_cash": "CRYPTO_WALLET", "stellar": "CRYPTO_WALLET", "bsv": "CRYPTO_WALLET", 
    "multiversx": "CRYPTO_WALLET", "algorand": "CRYPTO_WALLET", "flow": "CRYPTO_WALLET", 
    "klaytn": "CRYPTO_WALLET", "bitcoingold": "CRYPTO_WALLET", "zcash": "CRYPTO_WALLET", 
    "dash": "CRYPTO_WALLET", "harmony": "CRYPTO_WALLET", "verge": "CRYPTO_WALLET", 
    "provenance": "CRYPTO_WALLET", "sui": "CRYPTO_WALLET", "dogecoin": "CRYPTO_WALLET", 
    "cardano": "CRYPTO_WALLET", "conflux": "CRYPTO_WALLET", "ethereum_classic": "CRYPTO_WALLET", 
    "celo": "CRYPTO_WALLET", "fantom": "CRYPTO_WALLET", "moonbeam": "CRYPTO_WALLET", 
    "cronos": "CRYPTO_WALLET", "everscale": "CRYPTO_WALLET", "filecoin": "CRYPTO_WALLET", 
    "hedera": "CRYPTO_WALLET", "tezos": "CRYPTO_WALLET", "coreum": "CRYPTO_WALLET", "coti": "CRYPTO_WALLET",
    "phone": "PHONE",
    "documents": "FILE_DOC",
    "hash": "MALWARE_IOC",
    "tox_ids": "NETWORK_ENTITY",
    "credit_cards": "BANK_ACCOUNT"
}

# 🧠 UIE REGEX ENGINE (v1)
PATTERNS = {
    "person": r"\b(?!Inc|Ltd|LLC|Corp|Company|Department|University|Institute)([A-Z][a-z]+(?:\s[A-Z][a-z]+){1,3})\b",
    "org": r"\b([A-Z][A-Za-z0-9&.,'-]+\s(?:Inc|LLC|Ltd|Corp|Corporation|Foundation|Group|Agency|Institute|University))\b",
    "domain": r"\b((?:https?:\/\/)?(?:www\.)?[a-zA-Z0-9-]+\.[a-z]{2,}(?:\.[a-z]{2,})?)\b",
    "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
    "ip": r"\b(?:(?:25[0-5]|2[0-4]\d|1?\d?\d)\.){3}(?:25[0-5]|2[0-4]\d|1?\d?\d)\b",
    "url_path": r"https?:\/\/(?:www\.)?[^\s/$.?#].[^\s]*",
    "bitcoin": r"\b(?:bc1[a-z0-9]{25,39}|[13][a-km-zA-HJ-NP-Z1-9]{25,34})\b",
    "ethereum": r"\b0x[a-fA-F0-9]{40}\b",
    "bsc": r"\b0x[a-fA-F0-9]{40}\b",
    "solana": r"\b[1-9A-HJ-NP-Za-km-z]{32,44}\b",
    "ripple": r"\br[1-9A-HJ-NP-Za-km-z]{24,34}\b",
    "avalanche": r"\b0x[a-fA-F0-9]{40}\b",
    "tron": r"\bT[1-9A-HJ-NP-Za-km-z]{33}\b",
    "polygon": r"\b0x[a-fA-F0-9]{40}\b",
    "litecoin": r"\b(?:ltc1[a-z0-9]{25,65}|[LM3][a-km-zA-HJ-NP-Z1-9]{26,33})\b",
    "bitcoin_cash": r"\b(?:bitcoincash:)?(?:q|p)[a-z0-9]{41}\b",
    "stellar": r"\bG[A-Z2-7]{55}\b",
    "bsv": r"\b[13][a-km-zA-HJ-NP-Z1-9]{25,34}\b",
    "multiversx": r"\berd1[a-z0-9]{58}\b",
    "algorand": r"\b[A-Z2-7]{58}\b",
    "flow": r"\b0x[a-fA-F0-9]{8,64}\b",
    "klaytn": r"\b0x[a-fA-F0-9]{40}\b",
    "bitcoingold": r"\b[13][a-km-zA-HJ-NP-Z1-9]{25,34}\b",
    "zcash": r"\b(?:t1|t3)[a-km-zA-HJ-NP-Z1-9]{25,34}\b",
    "dash": r"\b[Xx][a-km-zA-HJ-NP-Z1-9]{25,34}\b",
    "harmony": r"\b0x[a-fA-F0-9]{40}\b",
    "verge": r"\b[DdXxYyZz][a-km-zA-HJ-NP-Z1-9]{25,34}\b",
    "provenance": r"\b0x[a-fA-F0-9]{40}\b",
    "sui": r"\b0x[a-fA-F0-9]{40,64}\b",
    "dogecoin": r"\bD{1}[a-km-zA-HJ-NP-Z1-9]{25,34}\b",
    "cardano": r"\b(?:addr1|addr_test1)[0-9a-z]{58,}\b",
    "conflux": r"\b(?:cfx:)?0x[a-fA-F0-9]{40}\b",
    "ethereum_classic": r"\b0x[a-fA-F0-9]{40}\b",
    "celo": r"\b0x[a-fA-F0-9]{40}\b",
    "fantom": r"\b0x[a-fA-F0-9]{40}\b",
    "moonbeam": r"\b0x[a-fA-F0-9]{40}\b",
    "cronos": r"\b0x[a-fA-F0-9]{40}\b",
    "everscale": r"\b0:[a-fA-F0-9]{64,}\b",
    "filecoin": r"\b(?:f|t)[0-9][a-z0-9]{20,}\b",
    "hedera": r"\b0\.0\.\d+\b",
    "tezos": r"\b(?:tz1|tz2|tz3|KT1)[1-9A-HJ-NP-Za-km-z]{33}\b",
    "coreum": r"\b0x[a-fA-F0-9]{40}\b",
    "coti": r"\b[1-9A-HJ-NP-Za-km-z]{25,45}\b",
    "device": r"\b([A-Z0-9]{8,}-[A-Z0-9]{4,}-[A-Z0-9]{4,}-[A-Z0-9]{4,}-[A-Z0-9]{12,})\b",
    "event": r"\b([A-Z][a-zA-Z]+(?:\s[A-Z][a-zA-Z]+)*\s(?:202[0-9]|19[0-9]{2}))\b",
    "hash": r"\b[a-fA-F0-9]{32,64}\b",
    "tox_ids": r"\b[0-9A-Fa-f]{76}\b",
    "credit_cards": {
        "visa": r"\b4[0-9]{12}(?:[0-9]{3})?\b",
        "mastercard": r"\b5[1-5][0-9]{14}\b",
        "amex": r"\b3[47][0-9]{13}\b",
        "discover": r"\b6(?:011|5[0-9]{2})[0-9]{12}\b",
    },
    "ssn": r"\b(?!000|666)[0-8][0-9]{2}-(?!00)[0-9]{2}-(?!0000)[0-9]{4}\b",
    "phone": r"\b(?:\+?1[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}\b",
    "documents": r"\b\S+\.(?:pdf|xml|docx?|txt|csv|xlsx?)\b",
    "usernames": r"(?<=^|(?<=[^a-zA-Z0-9-_\.]))@([A-Za-z0-9_]{3,40})"
}

# Runtime structures
session = requests.Session()
if USE_TOR:
    session.proxies.update(TOR_PROXY)
session.headers.update(HEADERS)
try:
    ua = UserAgent()
except Exception:
    ua = None

queue_urls = Queue()
queued_set = set()
processed_set = set()

locks = {
    "processed": threading.Lock(),
    "queued": threading.Lock(),
    "state": threading.Lock(),
    "stats": threading.Lock(),
    "log": threading.Lock(),
    "sse": threading.Lock()
}

keywords = []
stats = {
    "seed": 0, "processed": 0, "pending": 0, 
    "btc_found": 0, "eth_found": 0, "sol_found": 0, "emails_found": 0, 
    "docs_found": 0, "orgs_found": 0, "hashes_found": 0
}

# Global event stream for UI
recent_logs = deque(maxlen=8)
recent_entities = deque(maxlen=12) # Holds tuples of (ts, ont_class, val, url)
sse_clients = []

# -------------------- 🧠 UIE REGEX ENGINE & ONTOLOGY NORMALIZATION --------------------
class UIEEngine:
    @staticmethod
    def score_entity(e_type, value):
        confidence = 0.5
        if e_type in ['ip', 'hash', 'tox_ids'] or ONTOLOGY_MAP.get(e_type) == 'CRYPTO_WALLET':
            confidence = 0.95
        if e_type == 'org' and any(suffix in value for suffix in ['Inc', 'LLC', 'Corp']):
            confidence += 0.3
        if e_type == 'person':
            words = value.split()
            if len(words) >= 2 and all(w[0].isupper() for w in words):
                confidence += 0.2
            else:
                confidence -= 0.2
        if e_type == 'email' and '@' in value:
            confidence = 0.9
        
        return round(min(1.0, max(0.1, confidence)), 2)

    @staticmethod
    def extract(text, source_url):
        uie_master = []
        ts = datetime.now(timezone.utc).isoformat()
        
        for e_type, pattern in PATTERNS.items():
            category = ONTOLOGY_MAP.get(e_type, "UNKNOWN")
            tasks = NEMESIS_ONTOLOGY.get(category, {}).get("tasks", [])
            
            if e_type == 'credit_cards':
                for cc_type, cc_pattern in pattern.items():
                    matches = list(set(re.findall(cc_pattern, text)))
                    for match in matches:
                        uie_master.append({
                            "type": "credit_card", "ontology_class": "BANK_ACCOUNT", "subtype": cc_type, "value": match,
                            "confidence": 0.9, "sourceSpan": source_url, "timestamp": ts,
                            "autonomous_tasks": NEMESIS_ONTOLOGY["BANK_ACCOUNT"]["tasks"]
                        })
            else:
                matches = list(set(re.findall(pattern, text)))
                for match in matches:
                    val = match[0] if isinstance(match, tuple) else match
                    val = val.strip()
                    if len(val) < 2: continue
                    
                    uie_master.append({
                        "type": e_type, "ontology_class": category, "value": val, 
                        "confidence": UIEEngine.score_entity(e_type, val),
                        "sourceSpan": source_url, "timestamp": ts,
                        "autonomous_tasks": tasks
                    })
        
        filtered_master = [e for e in uie_master if e['confidence'] >= 0.4]
        return filtered_master

class SigmaGraphEngine:
    @staticmethod
    def stream_nodes(uie_entities):
        high_conf_nodes = [e for e in uie_entities if e['confidence'] >= 0.9]
        if high_conf_nodes:
            pass

# -------------------- PARALLEL API ENRICHMENT ENGINE --------------------
class WalletEnrichmentEngine:
    def __init__(self):
        self.providers = {
            "ETH": [
                {"name": "Etherscan", "url": "https://api.etherscan.io/api?module=account&action=txlist&address={}&apikey={key}", "key": os.getenv("VITE_ETHERSCAN_API_KEY", "")},
                {"name": "Blockscout", "url": "https://eth.blockscout.com/api?module=account&action=txlist&address={}", "key": ""}
            ],
            "BTC": [
                {"name": "Blockchain.info", "url": "https://blockchain.info/rawaddr/{}", "key": ""},
                {"name": "BlockCypher", "url": "https://api.blockcypher.com/v1/btc/main/addrs/{}", "key": ""}
            ]
        }
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=5)

    def fetch_data(self, address, network):
        providers = self.providers.get(network.upper(), [])
        if not providers:
            return {"status": "skipped", "message": f"No providers for {network}"}

        for provider in providers:
            try:
                url = provider["url"].format(address, key=provider["key"]) if provider["key"] else provider["url"].format(address)
                headers = {"User-Agent": "Nemesis-OSINT-Engine/3.0"}
                resp = requests.get(url, headers=headers, timeout=5)
                
                if resp.status_code == 200:
                    data = resp.json()
                    tx_count = 0
                    balance = "0"
                    
                    if provider["name"] in ["Etherscan", "Blockscout"]:
                        txs = data.get("result", [])
                        tx_count = len(txs) if isinstance(txs, list) else 0
                    elif provider["name"] == "Blockchain.info":
                        tx_count = data.get("n_tx", 0)
                        balance = str(data.get("final_balance", 0))
                    
                    return {
                        "status": "success",
                        "provider": provider["name"],
                        "tx_count": tx_count,
                        "balance": balance
                    }
                elif resp.status_code == 429:
                    continue # Rate limited, instantly failover to fallback provider
            except Exception:
                continue # Connection error, instantly failover to fallback provider
        return {"status": "error", "message": "All API providers failed or rate-limited"}

    def enrich(self, entities):
        wallets = [e for e in entities if e.get("ontology_class") == "CRYPTO_WALLET"]
        if not wallets:
            return entities
            
        future_to_wallet = {}
        for w in wallets:
            addr = w["value"]
            net = "ETH" if str(addr).startswith("0x") else "BTC"
            future = self.executor.submit(self.fetch_data, addr, net)
            future_to_wallet[future] = w

        for future in concurrent.futures.as_completed(future_to_wallet):
            w = future_to_wallet[future]
            try:
                res = future.result()
                if res["status"] == "success":
                    w["enrichment"] = res
                    # Auto-label based on on-chain activity volume
                    if res.get("tx_count", 0) > 50:
                        w["tags"] = ["HIGH_ACTIVITY_NODE"]
                    elif res.get("tx_count", 0) == 0:
                        w["tags"] = ["INACTIVE"]
                    else:
                        w["tags"] = ["ACTIVE"]
            except Exception:
                pass
        
        return entities

enrichment_engine = WalletEnrichmentEngine()

# -------------------- OSINT MAPPER SUBPROCESS (AUTO-RECON) --------------------
def run_osint_mapper():
    """Runs exclusively in the secondary console window to display OSINT Recon results."""
    console.print(Panel.fit("[bold magenta]🧠 NEMESIS AUTONOMOUS OSINT MAPPER (v3.0)[/bold magenta]"))
    console.print("Tailing `export.jsonl` for UIE Identity Cross-Referencing & Auto-Recon...\n")
    
    platforms = {
        "GitHub": "https://github.com/{}",
        "Twitter": "https://twitter.com/{}",
        "Reddit": "https://www.reddit.com/user/{}/"
    }

    # Wait until export.jsonl is created by the main process
    while not os.path.exists(EXPORT_JSONL):
        time.sleep(1)

    # Use a standard tail -f reading mechanism to prevent lagging/re-reading the whole file
    with open(EXPORT_JSONL, "r", encoding="utf-8") as f:
        while True:
            line = f.readline()
            if not line:
                time.sleep(0.5)
                continue
            
            line = line.strip()
            if not line:
                continue
                
            try:
                record = json.loads(line)
                web_info = record.get("web_info", {})
                metadata = web_info.get("metadata", {})
                url = web_info.get("url", "Unknown")
                uie_entities = record.get("uie_entities", [])
                
                # If no entities and no metadata, skip to avoid spamming the console
                if not uie_entities and not metadata:
                    continue
                
                # --- 1. Display Target and Scraped Metadata ---
                console.print(Panel(f"[bold green]Target Node:[/bold green] {url}", border_style="green"))
                
                if metadata:
                    meta_tree = Tree("[bold cyan]📄 Page Meta-Data Extracted[/bold cyan]")
                    for k, v in metadata.items():
                        meta_tree.add(f"[dim]{k}:[/dim] {v}")
                    console.print(meta_tree)
                
                # --- 2. Auto-Recon on Entities ---
                for entity in uie_entities:
                    if entity.get('confidence', 0) < 0.8: continue
                    
                    val = entity.get('value', 'Unknown')
                    ont_class = entity.get('ontology_class', 'UNKNOWN')
                    tasks = entity.get('autonomous_tasks', [])
                    
                    tree = Tree(f"[bold cyan]Entity Discovered:[/bold cyan] {val} [yellow]({ont_class})[/yellow]")
                    
                    # Display auto-labels and parallel enrichment data if available
                    if 'enrichment' in entity:
                        enrich_data = entity['enrichment']
                        tags = entity.get('tags', [])
                        tag_str = f" [bold red]{tags}[/bold red]" if tags else ""
                        tree.add(f"[bold green]📊 On-Chain Stats:[/bold green] {enrich_data.get('tx_count')} TXs via {enrich_data.get('provider')}{tag_str}")

                    recon_branch = tree.add("[bold yellow]🔍 Auto-OSINT Recon Links & Actions:[/bold yellow]")
                    
                    # Standard Platform Lookups
                    if ont_class in ['PERSON', 'EMAIL', 'NETWORK_ENTITY']:
                        target = val.replace("@", "")
                        for plat_name, tmpl in platforms.items():
                            try:
                                p_url = tmpl.format(target) if "{}" in tmpl else tmpl + target
                                r = requests.get(p_url, headers=HEADERS, timeout=3)
                                if r.status_code == 200:
                                    recon_branch.add(f"[green]✔ {plat_name} Match![/green] -> {p_url}")
                            except Exception: pass
                            
                    # Specialized Passive Reconnaissance
                    if ont_class == 'IP_ADDRESS':
                        recon_branch.add(f"AbuseIPDB (Threat check): https://www.abuseipdb.com/check/{val}")
                        recon_branch.add(f"Shodan (Port check): https://www.shodan.io/host/{val}")
                    
                    elif ont_class == 'CRYPTO_WALLET':
                        recon_branch.add(f"Blockchair Explorer: https://blockchair.com/search?q={val}")
                        recon_branch.add(f"OXT Analytics: https://oxt.me/address/{val}")
                        
                    elif ont_class == 'MALWARE_IOC':
                        recon_branch.add(f"VirusTotal Analysis: https://www.virustotal.com/gui/search/{val}")
                        
                    elif ont_class == 'DOMAIN':
                        clean_domain = val.replace("https://", "").replace("http://", "").split("/")[0]
                        try:
                            resolved_ip = socket.gethostbyname(clean_domain)
                            recon_branch.add(f"[bold green]Resolved IP:[/bold green] {resolved_ip}")
                            recon_branch.add(f"Shodan: https://www.shodan.io/host/{resolved_ip}")
                        except Exception:
                            recon_branch.add("[dim]DNS Resolution Failed (Likely Hidden Service/Tor)[/dim]")
                        recon_branch.add(f"WHOIS Lookup: https://who.is/whois/{clean_domain}")
                        
                    elif ont_class == 'EMAIL':
                        recon_branch.add(f"HaveIBeenPwned: https://haveibeenpwned.com/account/{val}")

                    if tasks:
                        task_branch = tree.add("[bold magenta]⚡ Autonomous Task Pipeline:[/bold magenta]")
                        for task in tasks[:3]:
                            task_branch.add(f"[blue]Queued ->[/blue] {task}")
                            
                    console.print(tree)
                    console.print("-" * 70)
                    
            except json.JSONDecodeError: 
                pass
            except Exception as e:
                console.print(f"[red]Error processing mapped line: {e}[/red]")

def spawn_osint_mapper():
    script = os.path.abspath(sys.argv[0])
    try:
        if os.name == 'nt':
            # Uses subprocess.CREATE_NEW_CONSOLE to safely bypass cmd.exe quoting restrictions
            subprocess.Popen([sys.executable, script, "--osint-mapper"], creationflags=subprocess.CREATE_NEW_CONSOLE)
        elif sys.platform == 'darwin':
            cmd_args = f'"{sys.executable}" "{script}" --osint-mapper'
            subprocess.Popen(f'osascript -e \'tell app "Terminal" to do script "{cmd_args}"\'', shell=True)
        else:
            # Linux fallback list
            terminals = ['gnome-terminal', 'xfce4-terminal', 'konsole', 'x-terminal-emulator']
            launched = False
            for t in terminals:
                if os.system(f"which {t} > /dev/null") == 0:
                    subprocess.Popen([t, '-e', f'{sys.executable} {script} --osint-mapper'])
                    launched = True
                    break
            if not launched:
                log("[WARN] Could not find a compatible terminal to auto-spawn on Linux.", style="yellow")
                
        log("[SYSTEM] Auto-Recon OSINT Mapper console launched.", style="bold magenta")
    except Exception as e:
        log(f"[WARN] Could not auto-spawn mapper window: {e}", style="red")

if "--osint-mapper" in sys.argv:
    run_osint_mapper()
    sys.exit(0)

# -------------------- FRONTEND SSE INTEGRATION --------------------
def push_sse_event(event_type, data):
    """Pushes real-time events to all connected React dashboards"""
    msg = f"event: {event_type}\ndata: {json.dumps(data)}\n\n"
    with locks["sse"]:
        for client_queue in sse_clients:
            client_queue.put(msg)

def log(msg, style="white"):
    ts = datetime.now().strftime("%H:%M:%S")
    with locks["log"]:
        recent_logs.append(f"[{ts}] [{style}]{msg}[/{style}]")
    push_sse_event("log", {"ts": ts, "message": msg, "style": style})

def record_entity(ont_class, value, source_url):
    ts = datetime.now().strftime("%H:%M:%S")
    with locks["log"]:
        display_url = source_url[:45] + "..." if len(source_url) > 45 else source_url
        recent_entities.append((ts, ont_class, value, display_url))
    push_sse_event("entity", {"ts": ts, "type": ont_class, "val": value, "src": source_url})

# -------------------- FLASK API SERVER --------------------
import logging
# Suppress default Flask/Werkzeug startup logs to prevent them from breaking the Rich UI
logging.getLogger('werkzeug').setLevel(logging.ERROR)
os.environ['WERKZEUG_RUN_MAIN'] = 'true'

app = Flask(__name__)
CORS(app)

global_dbh = None

@app.route('/')
def index():
    try:
        return render_template('index.html')
    except Exception as e:
        return f"<h2>UI Template Not Found</h2><p>Please ensure you have a <b>templates</b> folder containing <b>index.html</b> in the same directory as this script.</p>", 404

@app.route('/api/stats')
def api_stats():
    with locks["stats"]:
        return jsonify({"status": "success", "metrics": stats})

@app.route('/api/search')
def api_search():
    query = request.args.get('q', '').strip()
    filter_type = request.args.get('filter', 'ALL').upper()
    
    if not query or not global_dbh:
        return jsonify({"results": []})
        
    try:
        output = []
        if global_dbh.dbtype == "mongodb":
            search_pattern = re.compile(re.escape(query), re.IGNORECASE)
            mongo_query = {
                "$or": [
                    {"web_info.content": search_pattern},
                    {"web_info.title": search_pattern},
                    {"uie_entities.value": search_pattern}
                ]
            }
            if filter_type != 'ALL':
                filter_map = {
                    'CRYPTO_WALLET': ['CRYPTO_WALLET', 'BANK_ACCOUNT', 'CRYPTO_TRANSACTION'],
                    'EMAIL/PERSON': ['PERSON', 'EMAIL'],
                    'MALWARE_IOC': ['MALWARE_IOC'],
                    'ORGANIZATION': ['ORGANIZATION']
                }
                allowed = filter_map.get(filter_type, [])
                if allowed: mongo_query["uie_entities.ontology_class"] = {"$in": allowed}
                
            cursor = global_dbh.coll.find(mongo_query).sort("crawled_at", -1).limit(50)
            for doc in cursor:
                doc['_id'] = str(doc['_id'])
                output.append(doc)

        elif global_dbh.dbtype in ["sqlite", "postgresql"]:
            # Fallback SQL Search 
            q = f"%{query}%"
            global_dbh.cursor.execute("SELECT url, title, description, content, crawled_at FROM crawled WHERE content LIKE ? LIMIT 50", (q,))
            for row in global_dbh.cursor.fetchall():
                output.append({
                    "crawled_at": row[4],
                    "web_info": {"url": row[0], "title": row[1], "content": row[3][:500]},
                    "uie_entities": []
                })
                
        return jsonify({"results": output})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/stream')
def api_stream():
    def event_stream():
        q = Queue()
        with locks["sse"]: sse_clients.append(q)
        try:
            while True: yield q.get()
        except GeneratorExit:
            with locks["sse"]: sse_clients.remove(q)
    return Response(event_stream(), mimetype="text/event-stream")

def start_api_server(dbh):
    global global_dbh
    global_dbh = dbh
    # Disable reloader to prevent duplicate threads
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

# -------------------- DB ABSTRACTION --------------------
class DBHandler:
    def __init__(self, dbtype, conn_info):
        self.dbtype = dbtype.lower()
        self.conn_info = conn_info
        self.client = None
        self.conn = None
        self.cursor = None
        self.db = None

    def connect_and_prepare(self):
        if self.dbtype == "mongodb":
            if MongoClient is None: raise RuntimeError("pymongo not installed")
            self.client = MongoClient(self.conn_info, serverSelectionTimeoutMS=8000)
            self.client.server_info()
            try: self.db = self.client.get_database()
            except Exception: self.db = self.client["blockchain"]
            self.coll = self.db["darknet_data"]
            log(f"MongoDB connected: {self.db.name}.darknet_data", style="green")
            
        # AUTO-CONNECT NEO4J IF PRESENT IN ENV
        self.neo4j_driver = None
        neo_uri = os.environ.get("NEO4J_URI")
        if neo_uri:
            try:
                from neo4j import GraphDatabase
                neo_user = os.environ.get("NEO4J_USER", "neo4j")
                neo_pass = os.environ.get("NEO4J_PASSWORD", "")
                self.neo4j_driver = GraphDatabase.driver(neo_uri, auth=(neo_user, neo_pass))
                log("Neo4j multi-DB ingestion connected.", style="green")
            except Exception as e:
                log(f"Neo4j connect error: {e}", style="red")

        elif self.dbtype == "sqlite":
            path = self.conn_info.get("path", "crawler_data.db") if isinstance(self.conn_info, dict) else self.conn_info
            self.conn = sqlite3.connect(path, check_same_thread=False)
            self.cursor = self.conn.cursor()
            self._create_sqlite_tables()
            log(f"SQLite connected: {path}", style="green")
        elif self.dbtype == "postgresql":
            if psycopg2 is None: raise RuntimeError("psycopg2 not installed")
            if isinstance(self.conn_info, dict): self.conn = psycopg2.connect(**self.conn_info)
            else: self.conn = psycopg2.connect(self.conn_info)
            self.cursor = self.conn.cursor()
            self._create_postgres_tables()
            log(f"PostgreSQL connected", style="green")
        else:
            log(f"Export-only mode (No DB specified)", style="yellow")

    def _create_sqlite_tables(self):
        create = """CREATE TABLE IF NOT EXISTS crawled (
            id INTEGER PRIMARY KEY AUTOINCREMENT, hash_id TEXT, crawled_at TEXT, url TEXT UNIQUE, title TEXT,
            description TEXT, query_parameters TEXT, content TEXT, links TEXT, financial TEXT, person TEXT, documents TEXT, keywords_detected TEXT
        );"""
        self.cursor.execute(create)
        self.conn.commit()

    def _create_postgres_tables(self):
        create = """CREATE TABLE IF NOT EXISTS crawled (
            id SERIAL PRIMARY KEY, hash_id TEXT, crawled_at TEXT, url TEXT UNIQUE, title TEXT,
            description TEXT, query_parameters TEXT, content TEXT, links TEXT, financial TEXT, person TEXT, documents TEXT, keywords_detected TEXT
        );"""
        self.cursor.execute(create)
        self.conn.commit()

    def insert_record(self, record):
        try:
            uie_entities = record.get("uie_entities", [])
            fin_data = [e for e in uie_entities if e['ontology_class'] in ['CRYPTO_WALLET', 'BANK_ACCOUNT']]
            per_data = [e for e in uie_entities if e['ontology_class'] in ['PERSON', 'EMAIL', 'PHONE', 'NETWORK_ENTITY']]
            doc_data = [e for e in uie_entities if e['ontology_class'] in ['FILE_DOC', 'ORGANIZATION', 'DOMAIN', 'IP_ADDRESS', 'MALWARE_IOC']]

            # Inject root-level URL to satisfy MongoDB unique indexes
            record["url"] = record["web_info"].get("url")

            # --- NEO4J AUTO-PUSH ---
            if hasattr(self, 'neo4j_driver') and self.neo4j_driver:
                try:
                    with self.neo4j_driver.session() as session:
                        session.run("MERGE (d:DarknetSite {url: $url}) SET d.title = $title, d.last_crawled = $crawled", url=record["url"], title=record["web_info"].get("title"), crawled=record.get("crawled_at"))
                        for ent in fin_data + per_data + doc_data:
                            val = ent.get("value")
                            if val:
                                session.run("MERGE (e:Entity {value: $val}) ON CREATE SET e.type = $type MERGE (d:DarknetSite {url: $url}) MERGE (d)-[:MENTIONS]->(e)", val=val, type=ent.get("ontology_class"), url=record["url"])
                except Exception as e:
                    pass

            # --- CLOUDFLARE D1 AUTO-PUSH ---
            cf_account = os.environ.get("CLOUDFLARE_ACCOUNT_ID")
            cf_token = os.environ.get("CLOUDFLARE_API_TOKEN")
            cf_d1_id = os.environ.get("CLOUDFLARE_D1_ID")
            if cf_account and cf_token and cf_d1_id:
                try:
                    url = f"https://api.cloudflare.com/client/v4/accounts/{cf_account}/d1/database/{cf_d1_id}/query"
                    headers = {"Authorization": f"Bearer {cf_token}", "Content-Type": "application/json"}
                    payload = {"sql": "INSERT INTO darknet_data (hash_id, url, title, data) VALUES (?, ?, ?, ?)", "params": [record.get("hash-ID"), record["url"], record["web_info"].get("title"), json.dumps(record)]}
                    requests.post(url, headers=headers, json=payload, timeout=5)
                except Exception as e:
                    pass

            if self.dbtype == "mongodb":
                # Upsert prevents Duplicate Key Exceptions on revisits
                self.coll.update_one({"url": record["url"]}, {"$set": record}, upsert=True)
            elif self.dbtype == "sqlite":
                self.cursor.execute(
                    "INSERT OR IGNORE INTO crawled (hash_id,crawled_at,url,title,description,query_parameters,content,links,financial,person,documents,keywords_detected) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                    (
                        record.get("hash-ID"), record.get("crawled_at"), record["web_info"].get("url"),
                        record["web_info"].get("title"), record["web_info"].get("description"),
                        json.dumps(record["web_info"].get("query_parameters", {}), ensure_ascii=False),
                        record["web_info"].get("content"), json.dumps(record["web_info"].get("links", []), ensure_ascii=False),
                        json.dumps(fin_data, ensure_ascii=False),
                        json.dumps(per_data, ensure_ascii=False),
                        json.dumps(doc_data, ensure_ascii=False),
                        json.dumps(record.get("keywords_detected", []), ensure_ascii=False),
                    ),
                )
                self.conn.commit()
            elif self.dbtype == "postgresql":
                self.cursor.execute(
                    "INSERT INTO crawled (hash_id,crawled_at,url,title,description,query_parameters,content,links,financial,person,documents,keywords_detected) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (url) DO NOTHING",
                    (
                        record.get("hash-ID"), record.get("crawled_at"), record["web_info"].get("url"),
                        record["web_info"].get("title"), record["web_info"].get("description"),
                        json.dumps(record["web_info"].get("query_parameters", {}), ensure_ascii=False),
                        record["web_info"].get("content"), json.dumps(record["web_info"].get("links", []), ensure_ascii=False),
                        json.dumps(fin_data, ensure_ascii=False),
                        json.dumps(per_data, ensure_ascii=False),
                        json.dumps(doc_data, ensure_ascii=False),
                        json.dumps(record.get("keywords_detected", []), ensure_ascii=False),
                    ),
                )
                self.conn.commit()
        except Exception as e:
            log(f"[DB] insert error: {e}", style="red")

    def close(self):
        try:
            if self.dbtype == "mongodb" and self.client: self.client.close()
            elif self.dbtype in ("sqlite", "postgresql") and self.conn: self.conn.close()
        except Exception: pass

# -------------------- EXTRACTION & PARSING --------------------
def safe_get(url, retries=2, timeout=10, allow_redirects=True):
    for attempt in range(retries):
        try:
            headers = dict(HEADERS)
            if ua and os.getenv("VITE_CRAWLER_USER_AGENT_ROTATION") == "true":
                headers['User-Agent'] = ua.random
                
            r = session.get(url, headers=headers, timeout=timeout, allow_redirects=allow_redirects)
            
            if r.status_code == 200:
                return r
            elif r.status_code == 404:
                log(f"[HTTP 404] Not Found: {url}", style="dim")
                return None
            elif r.status_code in [403, 401]:
                log(f"[HTTP {r.status_code}] Forbidden/Unauthorized: {url}", style="dim yellow")
                return None
            else:
                log(f"[HTTP {r.status_code}] Error: {url}", style="dim red")
                return None
        except requests.exceptions.Timeout:
            pass # Suppress timeout errors
        except requests.exceptions.ConnectionError:
            pass # Suppress connection errors
        except Exception:
            time.sleep(1 + attempt)
    return None

def handle_query_param_expansion(url):
    parsed = urlparse(url)
    q = parse_qs(parsed.query)
    generated = []
    if not q: return generated
    
    for param in q.keys():
        for kw in list(keywords):
            new_q = {k: v[:] for k, v in q.items()}
            new_q[param] = [kw]
            new_url = parsed._replace(query=urlencode(new_q, doseq=True)).geturl()
            if enqueue_url(new_url):
                generated.append(new_url)
    return generated

def parse_page(url, html):
    soup = BeautifulSoup(content, "xml")
    text = soup.get_text(" ", strip=True)
    
    # NEW: Scrape Meta-Data
    metadata = {}
    for meta in soup.find_all("meta"):
        name = meta.get("name", meta.get("property", ""))
        content = meta.get("content", "")
        if name and content and len(content) < 500:
            metadata[name] = content
    
    uie_entities = UIEEngine.extract(text, url)
    
    # NEW: Run Parallel API Enrichment with Fallbacks & Auto-Labeling
    uie_entities = enrichment_engine.enrich(uie_entities)
    
    SigmaGraphEngine.stream_nodes(uie_entities) 

    links = []
    for a in soup.find_all("a", href=True):
        href = a.get("href")
        if not href: continue
        href = href.strip()
        try:
            abs_url = urljoin(url, href)
            parsed = urlparse(abs_url)
            if parsed.scheme in ("http", "https") or ".onion" in parsed.netloc:
                links.append(abs_url)
        except Exception: continue
            
    generated = handle_query_param_expansion(url)
    for l in links: enqueue_url(l)
    
    text_lower = text.lower()
    detected_kws = [k for k in keywords if k.lower() in text_lower]
        
    record = {
        "hash-ID": sha256(url),
        "crawled_at": datetime.now(timezone.utc).isoformat(),
        "web_info": {
            "url": url,
            "title": soup.title.string if soup.title else "N/A",
            "description": (soup.find("meta", {"name": "description"}) or {}).get("content", "N/A"),
            "metadata": metadata, # Added Metadata
            "query_parameters": parse_qs(urlparse(url).query),
            "content": text[:5000],
            "links": links,
            "subpages": links
        },
        "uie_entities": uie_entities,
        "keywords_detected": detected_kws
    }
    return record, generated

# -------------------- STATE & EXPORTS --------------------
def sha256(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def init_exports():
    if not os.path.exists(EXPORT_CSV):
        try:
            with open(EXPORT_CSV, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["Timestamp", "Ontology_Class", "Entity_Type", "Entity_Value", "Confidence", "Source_URL"])
        except Exception as e:
            log(f"[EXPORT] CSV init error: {e}", style="red")

def save_exports(record):
    try:
        with locks["state"]:
            with open(EXPORT_JSONL, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")
            
            uie_entities = record.get("uie_entities", [])
            if uie_entities:
                with open(EXPORT_CSV, "a", newline='', encoding="utf-8") as f:
                    writer = csv.writer(f)
                    for e in uie_entities:
                        writer.writerow([
                            e.get("timestamp"), e.get("ontology_class"), e.get("type"),
                            e.get("value"), e.get("confidence"), e.get("sourceSpan")
                        ])
    except Exception as e:
        log(f"[EXPORT] write error: {e}", style="red")

def save_state_file():
    try:
        with locks["state"]:
            payload = {"queued": list(queued_set), "processed": list(processed_set), "keywords": keywords}
            with open(STATE_FILE, "w", encoding="utf-8") as f: json.dump(payload, f, indent=2)
    except Exception as e: log(f"[STATE] save error: {e}", style="red")

def save_state_periodically(stop_event):
    while not stop_event.is_set():
        time.sleep(SAVE_STATE_INTERVAL)
        save_state_file()

def load_state_file():
    if not os.path.exists(STATE_FILE): return False
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f: payload = json.load(f)
        q = payload.get("queued", [])
        proc = payload.get("processed", [])
        kw = payload.get("keywords", [])
        for u in q: enqueue_url(u)
        with locks["processed"]: processed_set.update(proc)
        for k in kw:
            if k not in keywords: keywords.append(k)
        log(f"State loaded: Queued={len(q)} Processed={len(proc)}", style="green")
        return True
    except Exception as e:
        log(f"[STATE] load error: {e}", style="red")
        return False

def enqueue_url(u):
    try:
        if not u: return False
        u = u.strip()
        parsed = urlparse(u)
        if not parsed.scheme: return False
        normalized = parsed.geturl().split("#")[0]
        with locks["queued"]:
            if normalized in queued_set or normalized in processed_set: return False
            queue_urls.put(normalized)
            queued_set.add(normalized)
        return True
    except Exception: return False

# -------------------- TOR HANDLING --------------------
def is_tor_running():
    try:
        r = session.get(TOR_CHECK_URL, timeout=8)
        return (r.status_code == 200 and "Congratulations" in r.text)
    except Exception: return False

def start_tor_autorun():
    if not USE_TOR: return True
    if is_tor_running():
        log("[TOR] Already connected.", style="bold green")
        return True
    log("[TOR] Starting Tor process...", style="yellow")
    try:
        if os.name == "nt":
            candidates = ["tor.exe", os.path.join(os.getcwd(), "tor", "tor.exe")]
            for cand in candidates:
                try:
                    subprocess.Popen([cand], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    time.sleep(1)
                except Exception: continue
        else:
            try: subprocess.Popen(["tor"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except FileNotFoundError:
                log("[TOR] 'tor' not found. Please install Tor.", style="red")
                return False
    except Exception as e:
        log(f"[TOR] start error: {e}", style="red")
        return False

    for i in range(12):
        time.sleep(2)
        if is_tor_running():
            log("[TOR] Connected securely via port " + TOR_PORT, style="bold green")
            return True
    log("[TOR] Failed to verify connection", style="red")
    return False

# -------------------- WORKER THREAD --------------------
def worker_thread(db_handler: DBHandler, tid: int, stop_evt: threading.Event):
    while not stop_evt.is_set():
        try:
            url = queue_urls.get(timeout=2)
        except Empty:
            continue
                
        if url in processed_set:
            queue_urls.task_done()
            continue
            
        resp = safe_get(url)
        if resp and resp.text:
            try:
                record, generated = parse_page(url, resp.text)
                db_handler.insert_record(record)
                
                save_exports(record)
                
                with locks["processed"]: processed_set.add(url)
                with locks["stats"]:
                    stats["processed"] += 1
                    stats["pending"] = queue_urls.qsize()
                    
                # Push real-time ontology entities to UI Dashboard
                for e in record.get("uie_entities", []):
                    if e['confidence'] >= 0.8:
                        ont = e['ontology_class']
                        record_entity(ont, e['value'], url)
                        
                        if e['type'] in ['btc', 'bitcoin', 'litecoin', 'dogecoin', 'bitcoin_cash', 'bsv', 'bitcoingold', 'dash', 'zcash']:
                            with locks["stats"]: stats["btc_found"] += 1
                        elif e['type'] in ['sol', 'solana']:
                            with locks["stats"]: stats["sol_found"] += 1
                        elif e['ontology_class'] == 'CRYPTO_WALLET':
                            with locks["stats"]: stats["eth_found"] += 1
                        elif e['type'] == 'email':
                            with locks["stats"]: stats["emails_found"] += 1
                        elif e['type'] == 'org':
                            with locks["stats"]: stats["orgs_found"] += 1
                        elif e['type'] == 'hash':
                            with locks["stats"]: stats["hashes_found"] += 1
                        elif e['type'] == 'documents':
                            with locks["stats"]: stats["docs_found"] += 1
                    
                if record.get("keywords_detected"):
                    log(f"⚡ Phrases matched: {record['keywords_detected']} at {url[:40]}...", style="bold magenta")
                    
            except Exception as e:
                log(f"[PARSE] error for {url}: {e}", style="red")
        queue_urls.task_done()
            
        if stats["processed"] % 15 == 0:
            save_state_file()

# -------------------- RICH LIVE DASHBOARD --------------------
def get_color_for_ontology(ont_class):
    colors = {
        "CRYPTO_WALLET": "yellow",
        "PERSON": "cyan",
        "EMAIL": "magenta",
        "BANK_ACCOUNT": "green",
        "FILE_DOC": "blue",
        "MALWARE_IOC": "red",
        "ORGANIZATION": "bold white",
        "DOMAIN": "bold blue"
    }
    return colors.get(ont_class, "white")

def generate_dashboard_layout():
    """Generates the Rich Layout for real-time advanced console rendering."""
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="main"),
        Layout(name="footer", size=10)
    )
    layout["main"].split_row(
        Layout(name="stats", ratio=1),
        Layout(name="entities", ratio=2)
    )
    
    # Header Panel
    header_text = Align.center(f"[bold cyan]NEMESIS CRAWLER (LIONSGATE NETWORK)[/bold cyan] • Threads: {MAX_WORKERS} • Tor: {'[green]Active[/green]' if USE_TOR else '[red]Disabled[/red]'}")
    layout["header"].update(Panel(header_text, box=box.ROUNDED, style="blue"))
    
    # Stats Table
    stats_table = Table(box=box.SIMPLE_HEAVY, expand=True, title="[bold yellow]📊 SYSTEM TELEMETRY[/bold yellow]")
    stats_table.add_column("Metric", style="bold white")
    stats_table.add_column("Count", justify="right", style="bold cyan")
    with locks["stats"]:
        stats_table.add_row("🌐 Pending URLs", str(stats["pending"]))
        stats_table.add_row("✅ Processed URLs", str(stats["processed"]))
        stats_table.add_row("💰 Crypto (BTC/ETH/SOL)", f"{stats['btc_found']} / {stats['eth_found']} / {stats['sol_found']}")
        stats_table.add_row("📧 Target Emails", str(stats["emails_found"]))
        stats_table.add_row("🏢 Organizations", str(stats["orgs_found"]))
        stats_table.add_row("🦠 Forensic Hashes", str(stats["hashes_found"]))
        stats_table.add_row("📄 Documents Extracted", str(stats["docs_found"]))
    layout["stats"].update(Panel(stats_table, box=box.ROUNDED))
    
    # Live Ontology Table
    entity_table = Table(box=box.MINIMAL_DOUBLE_HEAD, expand=True, title="[bold cyan]📡 REAL-TIME ONTOLOGY EXTRACTION STREAM[/bold cyan]")
    entity_table.add_column("Time", style="dim", width=10)
    entity_table.add_column("Class", style="bold magenta", width=16)
    entity_table.add_column("Value", style="bold green", width=25)
    entity_table.add_column("Source", style="blue")
    
    with locks["log"]:
        # Reverse to show newest at the top
        for ts, ont, val, url in reversed(list(recent_entities)):
            c = get_color_for_ontology(ont)
            entity_table.add_row(ts, f"[{c}]{ont}[/{c}]", f"[{c}]{val}[/{c}]", url)

    layout["entities"].update(Panel(entity_table, box=box.ROUNDED))
    
    # Engine Logs
    log_text = "\n".join(list(recent_logs))
    layout["footer"].update(Panel(log_text, title="[magenta]Engine Subprocess Logs[/magenta]", box=box.ROUNDED))
    
    return layout

# -------------------- SEEDS & KEYWORDS --------------------
def load_seeds_and_keywords():
    loaded = 0
    if os.path.exists(SEED_FILE):
        with open(SEED_FILE, "r", encoding="utf-8") as f:
            for line in f:
                if enqueue_url(line): loaded += 1
    
    if not AUTONOMOUS_MODE:
        if loaded == 0:
            log("[AUTO] SEED_FILE empty. Enter seed URLs (empty line to finish):", style="bold yellow")
            while True:
                u = input("seed> ").strip()
                if not u: break
                if enqueue_url(u): loaded += 1
                
        # --- Multi-line, text file, & comma-separated User Keyword Input Prompt ---
        log("[AUTO] Enter custom keywords/phrases (one per line or comma-separated).", style="bold yellow")
        log("[AUTO] You can also type the path to a .txt file to load them.", style="bold yellow")
        log("[AUTO] Press Enter on an empty line to finish.", style="bold yellow")
        
        new_kws = []
        while True:
            user_input = input("keywords> ").strip()
            if not user_input:
                break
            
            if user_input.lower().endswith('.txt') and os.path.isfile(user_input):
                try:
                    with open(user_input, 'r', encoding='utf-8') as f:
                        for line in f:
                            k = line.strip()
                            if k and k not in keywords and k not in new_kws:
                                new_kws.append(k)
                    log(f"[AUTO] Loaded keywords from {user_input}", style="green")
                except Exception as e:
                    log(f"[WARN] Could not read {user_input}: {e}", style="red")
            else:
                for k in user_input.split(","):
                    k = k.strip()
                    if k and k not in keywords and k not in new_kws:
                        new_kws.append(k)
        
        if new_kws:
            keywords.extend(new_kws)
            try:
                with open(KEYWORDS_FILE, "a", encoding="utf-8") as f:
                    for k in new_kws:
                        f.write(f"{k}\n")
            except Exception: pass

    if loaded == 0:
        log("[AUTO] SEED_FILE empty. Hardcoding default entry points...")
        enqueue_url("http://ahmia.fi")
        loaded = 1

    if os.path.exists(KEYWORDS_FILE):
        with open(KEYWORDS_FILE, "r", encoding="utf-8") as f:
            for line in f:
                k = line.strip()
                if k and k not in keywords: keywords.append(k)
                
    if not keywords:
        keywords.extend(DEFAULT_KEYWORDS)
        
    log(f"[AUTO] Tracking {len(keywords)} active keywords.", style="cyan")
    return loaded

# -------------------- AUTO-RUN MAIN --------------------
def main():
    log("Engine initializing sequence...", style="green")
    
    init_exports()
    if USE_TOR: start_tor_autorun()

    if AUTONOMOUS_MODE:
        log("Autonomous mode active reading from .env", style="green")
        db_type = os.getenv("VITE_CRAWLER_DB_TYPE", "mongodb")
        conn_info = os.getenv("VITE_DATABASE_MONGO_URL", "") if db_type == "mongodb" else os.getenv("VITE_POSTGRES_URI", "crawler_data.db")
    else:
        db_type, conn_info = "sqlite", "crawler_data.db"

    dbh = DBHandler(db_type, conn_info)
    try: dbh.connect_and_prepare()
    except Exception as e: log(f"[DB] init failed: {e}", style="red")

    if not (os.path.exists(STATE_FILE) and load_state_file()):
        load_seeds_and_keywords()

    with locks["stats"]:
        stats["seed"] = queue_urls.qsize()
        stats["pending"] = queue_urls.qsize()
        stats["processed"] = len(processed_set)

    # Launch Flask Backend API in Daemon Thread
    api_thr = threading.Thread(target=start_api_server, args=(dbh,), daemon=True)
    api_thr.start()

    # Spawn secondary UI/Mapper
    spawn_osint_mapper()

    stop_saver = threading.Event()
    saver_thr = threading.Thread(target=save_state_periodically, args=(stop_saver,), daemon=True)
    saver_thr.start()

    worker_stop = threading.Event()
    workers = []
    for i in range(MAX_WORKERS):
        t = threading.Thread(target=worker_thread, args=(dbh, i+1, worker_stop), daemon=True)
        t.start()
        workers.append(t)

    # 🚀 ADVANCED RICH LIVE CONSOLE LOOP (OR HEADLESS MODE)
    headless = os.environ.get("HEADLESS", "").lower() in ["1", "true", "yes"] or os.environ.get("RENDER")
    try:
        if headless:
            print("[*] Running in HEADLESS mode. Terminal UI disabled.", flush=True)
            while True:
                time.sleep(5)
                if queue_urls.empty():
                    time.sleep(5)
                    if queue_urls.empty(): break
        else:
            with Live(generate_dashboard_layout(), refresh_per_second=4, screen=True) as live:
                while True:
                    time.sleep(0.5) # Refresh layout smoothly
                    live.update(generate_dashboard_layout())
                    if queue_urls.empty():
                        time.sleep(2)
                        if queue_urls.empty(): break
    except KeyboardInterrupt:
        pass # UI handled shutdown cleanly

    worker_stop.set()
    stop_saver.set()
    for t in workers: t.join(timeout=2)
    saver_thr.join(timeout=1)
    save_state_file()
    
    try: dbh.close()
    except Exception: pass

if __name__ == "__main__":
    main()