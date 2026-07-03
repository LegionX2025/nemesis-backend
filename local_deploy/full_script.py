r"""
==============================================================================
🛡️ LIONSGATE INTELLIGENCE NETWORK - NEMESIS X (NEXT GENERATION)
==============================================================================
VERSION: 12000.0 (GLOBAL INTELLIGENCE OS)
STATUS: Production Stable | Premium Light-Mode SaaS UI | Taxonomy Mapped
==============================================================================
"""

import sys
import os
import subprocess
import multiprocessing
import asyncio
import socket
import time
import random

# 🔥 CRITICAL UVICORN BYPASS: Prevent WinError 10014 in Python 3.13
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    try:
        asyncio.WindowsProactorEventLoopPolicy = asyncio.WindowsSelectorEventLoopPolicy
    except AttributeError:
        pass
        
    _orig_getpeername = socket.socket.getpeername
    def _safe_getpeername(self):
        try:
            return _orig_getpeername(self)
        except OSError as e:
            if getattr(e, 'winerror', None) == 10014:
                return ('0.0.0.0', 0)
            raise
    socket.socket.getpeername = _safe_getpeername

os.environ["LOKY_MAX_CPU_COUNT"] = str(multiprocessing.cpu_count() or 4)

# ==============================================================================
# 📦 1. PRE-FLIGHT: AUTO-DEPENDENCY INSTALLER
# ==============================================================================
def bootstrap_system():
    print("🔄 [BOOT] Initializing Nemesis X Dependency Matrix...")
    packages = {
        "aiohttp": "aiohttp", "motor": "motor", "asyncpg": "asyncpg", 
        "dotenv": "python-dotenv", "fastapi": "fastapi", "uvicorn": "uvicorn", 
        "certifi": "certifi", "playwright": "playwright", 
        "playwright_stealth": "playwright-stealth", "pydantic": "pydantic", 
        "bs4": "beautifulsoup4", "google.genai": "google-genai"
    }
    
    missing = []
    for module, pip_name in packages.items():
        try:
            if module == "google.genai": import google.genai
            else: __import__(module.split('.')[0])
        except ImportError: missing.append(pip_name)
            
    if missing:
        print(f"⚠️ [BOOT] Missing modules. Auto-Installing: {', '.join(missing)}")
        try: subprocess.check_call([sys.executable, "-m", "pip", "uninstall", "-y", "google-generativeai"])
        except Exception: pass
        subprocess.check_call([sys.executable, "-m", "pip", "install", *missing])
        if "playwright" in missing:
            subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])
        print("✅ [BOOT] Dependencies injected. Restarting kernel...")
        os.execv(sys.executable, ['python'] + sys.argv)

if __name__ == "__main__":
    bootstrap_system()

# ==============================================================================
# 🚀 2. CORE IMPORTS & CONFIGURATION
# ==============================================================================
import certifi
import aiohttp
import json
import logging
import re
from datetime import datetime, timezone
from collections import defaultdict
from contextlib import asynccontextmanager

from bs4 import BeautifulSoup
try: import asyncpg
except ImportError: asyncpg = None

from google import genai 

from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import HTMLResponse
import uvicorn
from dotenv import load_dotenv

try:
    from playwright.async_api import async_playwright
    from playwright_stealth import Stealth
    PLAYWRIGHT_AVAILABLE = True
except ImportError: PLAYWRIGHT_AVAILABLE = False

load_dotenv()
os.environ['SSL_CERT_FILE'] = certifi.where()
os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("NEMESIS_OS")

def safe_int_parse(val, default=10000, unlimited_val=999999):
    if not val: return default
    val_str = str(val).strip().upper()
    if val_str in ["UNLIMITED", "MAX", "ALL", "INF"]: return unlimited_val
    try: return int(val_str)
    except (ValueError, TypeError): return default

class Config:
    CONCURRENCY_LIMIT = safe_int_parse(os.getenv("PARALLEL_FETCH_LIMIT"), default=50)
    
    raw_keys = os.getenv("GEMINI_API_KEYS", "") or os.getenv("GEMINI_API_KEY", "")
    GEMINI_KEYS = [k.strip().replace('"', '').replace("'", "") for k in raw_keys.split(",") if k.strip()]
    
    AIML_KEYS = {
        "DEEPSEEK": os.getenv("AIML_API_KEY_DEEPSEEK", ""),
        "CHATGPT": os.getenv("AIML_API_KEY_CHATGPT", ""),
        "LLAMA": os.getenv("AIML_API_KEY_LLAMA", "")
    }
    
    @classmethod
    def get_api_key(cls, chain):
        mapping = {
            "ETHEREUM": "ETHERSCAN_API_KEY", "BSC": "BSCSCAN_API_KEY", 
            "POLYGON": "POLYGONSCAN_API_KEY", "ARBITRUM": "ARBISCAN_API_KEY", 
            "BASE": "BASESCAN_API_KEY", "TRON": "TRONSCAN_API_KEY"
        }
        return os.getenv(mapping.get(chain, ""), "")

API_EXPLORER_DOMAINS = {
    "ETHEREUM": "api.etherscan.io", "BSC": "api.bscscan.com", "POLYGON": "api.polygonscan.com", 
    "ARBITRUM": "api.arbiscan.io", "BASE": "api.basescan.org"
}

UI_EXPLORER_DOMAINS = {
    "ETHEREUM": "etherscan.io", "BSC": "bscscan.com", "POLYGON": "polygonscan.com", 
    "ARBITRUM": "arbiscan.io", "BASE": "basescan.org", "OPTIMISM": "optimistic.etherscan.io",
    "AVALANCHE": "snowtrace.io", "TRON": "tronscan.org", "SOLANA": "solscan.io", 
    "XRP": "xrpscan.com", "BITCOIN": "mempool.space"
}

NULL_ADDRESS = "0x0000000000000000000000000000000000000000"

def detect_chain(val: str, override: str = "AUTO"):
    if override != "AUTO": return override.upper()
    val = val.strip()
    if re.match(r"^\b(?:bc1|[13])[a-zA-HJ-NP-Z0-9]{25,39}\b$", val): return "BITCOIN"
    if re.match(r"^\bT[1-9A-HJ-NP-Za-km-z]{33}\b$", val): return "TRON"
    if re.match(r"^\br[1-9A-HJ-NP-Za-km-z]{24,34}\b$", val): return "XRP"
    if re.match(r"^\b[1-9A-HJ-NP-Za-km-z]{32,44}\b$", val) and not val.startswith("0x"): return "SOLANA"
    if re.match(r"^\b0x[a-fA-F0-9]{40}\b$", val): return "ETHEREUM"
    return "UNKNOWN"

def get_asset_ticker(chain: str) -> str:
    mapping = {
        "ETHEREUM": "ETH", "BSC": "BNB", "POLYGON": "MATIC", "ARBITRUM": "ETH", 
        "BASE": "ETH", "BITCOIN": "BTC", "TRON": "TRX", "XRP": "XRP", "SOLANA": "SOL"
    }
    return mapping.get(chain.upper(), "ASSET")

# ==============================================================================
# 🧠 3. AUTONOMOUS INVESTIGATOR SWARM (TAXONOMY MAPPED AI)
# ==============================================================================
class AutonomousInvestigator:
    def __init__(self):
        self.gemini_active = bool(Config.GEMINI_KEYS)
        self.aiml_active = any(Config.AIML_KEYS.values())
        logger.info(f"✅ [LAYER 8] Autonomous Investigator Online. Taxonomy Embedded.")
        
    async def process_digital_twin(self, address, chain, entity, risk, tx_count, balance):
        prompt = f"""
        [SYSTEM: NEMESIS X - GLOBAL INTELLIGENCE OS]
        You are a Senior Cyber Forensics AI. You strictly adhere to the Global Blockchain Network Taxonomy.
        
        ENTITY PROFILE:
        Target Node: {address}
        Network Domain: {chain}
        Resolved Identity: {entity}
        Calculated Risk: {risk}/100
        Temporal Footprint: {tx_count} Events
        Terminal Exposure: ${balance:,.2f} USD

        INSTRUCTIONS:
        1. Classify the entity using the Canonical Taxonomy (e.g., Custodial Exchange, DEX, Mixer, Threat Actor, MEV Searcher, Bridge, Smart Contract, EOA).
        2. Describe the Flow Type (e.g., Wallet -> Exchange, Wallet -> Mixer -> Wallet).
        3. Identify likely Transaction Categories (e.g., DeFi Swap, Cross-chain Execution, Token Transfer, NFT Mint).
        
        OUTPUT FORMAT (Strict JSON without Markdown wrappers):
        {{
            "summary": "A highly technical, 2-sentence executive summary classifying the entity and its primary operational flow according to forensic taxonomy.", 
            "affidavit": "A detailed 2-paragraph forensic affidavit. Paragraph 1: Analyze the structural Network Activity, Flow Types, and Transaction Categories. Paragraph 2: Assess the Threat Posture, Entity Attribution, and Jurisdiction/Custodial off-ramp risks."
        }}
        """
        
        # Priority 1: Deep-Mind Gemini Matrix
        if self.gemini_active:
            for i, key in enumerate(Config.GEMINI_KEYS):
                if not key: continue
                try: client = genai.Client(api_key=key)
                except Exception: continue
                    
                for attempt in range(2): 
                    try:
                        resp = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
                        data = json.loads(resp.text.replace("```json", "").replace("```", "").strip())
                        logger.info(f"🧠 [LAYER 7] Cognitive Synthesis complete via Primary Engine (Node {i}).")
                        return data.get("summary", "Analysis complete."), data.get("affidavit", "Data compiled.")
                    except Exception as e:
                        err_msg = str(e)
                        if "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg.upper():
                            await asyncio.sleep(2 ** attempt + random.uniform(0.5, 1.5))
                        else: break

        # Priority 2: AIML Gateways
        if self.aiml_active:
            models_to_try = [
                ("deepseek/deepseek-chat", Config.AIML_KEYS["DEEPSEEK"]),
                ("gpt-4o-mini", Config.AIML_KEYS["CHATGPT"])
            ]
            for model_id, api_key in models_to_try:
                if not api_key: continue
                try:
                    async with aiohttp.ClientSession() as session:
                        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
                        payload = {"model": model_id, "messages": [{"role": "user", "content": prompt}]}
                        async with session.post("https://api.aimlapi.com/v1/chat/completions", json=payload, headers=headers, timeout=15) as r:
                            if r.status == 200:
                                result = await r.json()
                                content = result['choices'][0]['message']['content']
                                data = json.loads(content.replace("```json", "").replace("```", "").strip())
                                logger.info(f"🧠 [LAYER 7] Synthesis complete via Secondary Engine ({model_id}).")
                                return data.get("summary", "Analysis complete."), data.get("affidavit", "Data compiled.")
                except Exception: continue

        # Priority 3: Local Deterministic Heuristics
        logger.warning("⚠️ [LAYER 7] AI Endpoints Offline. Engaging Deterministic Heuristic Fallback.")
        if tx_count == 0:
            summary = "DATA VOID DETECTED: The Heuristic Engine processed this Digital Twin, but no on-chain footprint was verified. The node is classified as Dormant/Uninitialized."
        else:
            summary = f"Digital Twin resolution identifies this node as '{entity}' operating in the {chain} domain. Automated scoring classifies the risk at {risk}/100 across a footprint of {tx_count} events representing ${balance:,.2f}."
            
        affidavit = f"FORENSIC AFFIDAVIT:\n\n1. NETWORK ACTIVITY: The subject cryptographic entity ({address}) has executed {tx_count} confirmed ledger operations. The terminal exposure is calculated at ${balance:,.2f} USD equivalents.\n\n"
        if risk >= 80: affidavit += f"2. THREAT POSTURE: CRITICAL. A risk score of {risk}/100 strongly correlates with obfuscation typologies (e.g. Sanctioned Mixers, APT campaigns). Immediate mitigation recommended.\n\n"
        elif risk >= 40: affidavit += f"2. THREAT POSTURE: ELEVATED. Indicates interaction with high-risk counterparties or cross-chain layering.\n\n"
        else: affidavit += f"2. THREAT POSTURE: LOW. Standard transactional behavior within regulated frameworks.\n\n"
        affidavit += f"3. ONTOLOGY RESOLUTION: Open-source intelligence (OSINT) strictly associates this node with '{entity}'."
        
        return summary, affidavit

INVESTIGATOR_SWARM = AutonomousInvestigator()

# ==============================================================================
# 🗄️ 4. OSINT ENGINE (LAYER 6: HEADLESS DOM PARSING)
# ==============================================================================
class OSINT_Engine:
    def __init__(self):
        self.playwright, self.browser, self.context = None, None, None
        self.lock = asyncio.Lock()

    async def start_browser(self):
        if not PLAYWRIGHT_AVAILABLE: return
        async with self.lock:
            if self.context: return
            try:
                self.playwright = await async_playwright().start()
                self.browser = await self.playwright.chromium.launch(headless=True)
                self.context = await self.browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
                await Stealth().apply_stealth_async(self.context)
                logger.info("✅ [LAYER 6] Playwright OSINT Scraper Online.")
            except Exception as e: logger.warning(f"⚠️ [LAYER 6] Scraper Init Failed: {e}")

    async def scrape_entity(self, addr, chain):
        domain = UI_EXPLORER_DOMAINS.get(chain, "etherscan.io")
        if chain == "SOLANA": url = f"https://{domain}/account/{addr}"
        elif chain == "TRON": url = f"https://{domain}/#/address/{addr}"
        elif chain == "XRP": url = f"https://{domain}/account/{addr}"
        else: url = f"https://{domain}/address/{addr}"
        
        if not self.context: await self.start_browser()
        if self.context:
            page = None
            try:
                page = await self.context.new_page()
                await page.goto(url, wait_until="domcontentloaded", timeout=15000)
                
                # 🎯 PRECISION EXTRACTOR: Avoids Token Dropdowns
                extract_script = '''() => {
                    const pubTag = document.querySelector('span[title="Public Name Tag (viewable by anyone)"]');
                    if (pubTag && pubTag.textContent) return pubTag.textContent.trim();
                    
                    const fullTitle = document.title || "";
                    let titleName = fullTitle.includes('|') ? fullTitle.split('|')[0].trim() : fullTitle;
                    titleName = titleName.replace('Token Tracker', '').replace('Etherscan', '').replace('Address', '').trim();
                    
                    if (titleName && !titleName.startsWith('0x') && !titleName.includes('Blockchain Explorer')) {
                        return titleName;
                    }
                    return null;
                }'''
                entity_name = await page.evaluate(extract_script)
                if entity_name: return entity_name
            except Exception: pass
            finally:
                if page: await page.close()
        return "Unknown Entity"

OSINT = OSINT_Engine()

# ==============================================================================
# 🛰️ 5. MULTI-ARCHITECTURE DATA ADAPTERS (BEHAVIORAL TAXONOMY MAPPING)
# ==============================================================================
HTTP_SEMAPHORE = asyncio.Semaphore(Config.CONCURRENCY_LIMIT)

async def fetch_tron_txs(session, addr):
    url = f"https://apilist.tronscanapi.com/api/transfer?sort=-timestamp&count=true&limit=150&start=0&address={addr}"
    events = []
    async with HTTP_SEMAPHORE:
        try:
            async with session.get(url, timeout=12) as r:
                if r.status == 200:
                    for tx in (await r.json()).get("data", []):
                        ticker = tx.get("tokenInfo", {}).get("tokenAbbr", "TRX").upper()
                        amt = float(tx.get("amount", 0)) / (10 ** int(tx.get("tokenInfo", {}).get("tokenDecimal", 6)))
                        events.append({"hash": tx.get("transactionHash"), "to": tx.get("transferToAddress", ""), "from": tx.get("transferFromAddress", ""), "amount": amt, "ticker": ticker, "type": "Token Transfer" if ticker != "TRX" else "Native Transfer", "ts": str(tx.get("timestamp", 0) // 1000)})
        except: pass
    return events

async def fetch_bitcoin_txs(session, addr):
    url = f"https://mempool.space/api/address/{addr}/txs"
    events = []
    async with HTTP_SEMAPHORE:
        try:
            async with session.get(url, timeout=12) as r:
                if r.status == 200:
                    for tx in await r.json():
                        for vout in tx.get("vout", []):
                            to_addr = vout.get("scriptpubkey_address", "")
                            if to_addr: events.append({"hash": tx.get("txid"), "to": to_addr, "from": "UNKNOWN_INPUT" if to_addr == addr else addr, "amount": float(vout.get("value", 0)) / 100000000, "ticker": "BTC", "type": "Native Transfer", "ts": str(tx.get("status", {}).get("block_time", 0))})
                        for vin in tx.get("vin", []):
                            if vin.get("prevout", {}).get("scriptpubkey_address", ""): events[-1]["from"] = vin["prevout"]["scriptpubkey_address"]
        except: pass
    return events

async def fetch_xrp_txs(session, addr):
    url = f"https://api.xrpscan.com/api/v1/account/{addr}/transactions"
    events = []
    async with HTTP_SEMAPHORE:
        try:
            async with session.get(url, timeout=12) as r:
                if r.status == 200:
                    for tx in (await r.json()).get("transactions", []):
                        if tx.get("TransactionType") == "Payment":
                            to_addr = tx.get("Destination", "")
                            amt_data = tx.get("Amount", 0)
                            if isinstance(amt_data, dict): amt, ticker = float(amt_data.get("value", 0)), amt_data.get("currency", "UNKNOWN")
                            else: amt, ticker = float(amt_data) / 1000000, "XRP"
                            try: ts_str = str(datetime.strptime(tx.get("date"), "%Y-%m-%dT%H:%M:%S.000Z").replace(tzinfo=timezone.utc).timestamp())
                            except: ts_str = "0"
                            events.append({"hash": tx.get("hash"), "to": to_addr, "from": tx.get("Account", ""), "amount": amt, "ticker": ticker, "type": "Native Transfer", "ts": ts_str})
        except: pass
    return events

async def fetch_evm_explorer_layer(session, addr, action, chain, pages=2):
    api_key = Config.get_api_key(chain)
    domain = API_EXPLORER_DOMAINS.get(chain, 'api.etherscan.io')
    
    async def fetch_page(p):
        url = f"https://{domain}/api?module=account&action={action}&address={addr}&startblock=0&endblock=99999999&page={p}&offset=100&sort=desc&apikey={api_key}"
        for attempt in range(3): 
            try:
                async with HTTP_SEMAPHORE:
                    async with session.get(url, timeout=12) as r:
                        if r.status == 200:
                            data = await r.json()
                            if data.get("status") == "1": return data.get("result", [])
                            elif "Max rate limit reached" in str(data.get("result", "")):
                                await asyncio.sleep(1 + attempt)
                                continue
                        return []
            except Exception:
                await asyncio.sleep(1 + attempt)
        return []

    results = await asyncio.gather(*(fetch_page(p) for p in range(1, pages + 1)))
    all_txs = []
    for res in results:
        if isinstance(res, list): all_txs.extend(res)
    return all_txs

async def unified_fetch_all_txs(session, addr, chain):
    if chain == "TRON": return await fetch_tron_txs(session, addr)
    elif chain == "BITCOIN": return await fetch_bitcoin_txs(session, addr)
    elif chain == "XRP": return await fetch_xrp_txs(session, addr)
    elif chain == "SOLANA": return [] 
    
    results = await asyncio.gather(
        fetch_evm_explorer_layer(session, addr, "txlist", chain, pages=2),
        fetch_evm_explorer_layer(session, addr, "txlistinternal", chain, pages=1),
        fetch_evm_explorer_layer(session, addr, "tokentx", chain, pages=1),
        return_exceptions=True
    )
    
    native = results[0] if isinstance(results[0], list) else []
    internal = results[1] if isinstance(results[1], list) else []
    token = results[2] if isinstance(results[2], list) else []
    
    # --- TAXONOMY BEHAVIORAL CLASSIFIER ---
    DEX_ROUTERS = ["0x7a250d5630b4cf539739df2c5dacb4c659f2488d", "0x68b3465833fb72a70ecdf485e0e4c7bd8665fc45", "0x1111111254fb6c44bac0bed2854e76f90643097d"]
    BRIDGE_ROUTERS = ["0x8731d54e9d02c286767d56ac03e8037c07e01e98", "0x3ee18b2214aff97000d974cf647e7c347e8fa585", "0x283751a21eafbfcd52297820d27c1f1963d9b5b4"]
    MIXER_ROUTERS = ["0xd90e2f925da726b50c4ed8d0fb90ad053324f31b", "0x12d66f87a04a9e220743712ce6d9bb1b5616b8fc", "0x47ce0c6ed5b0ce3d3a51fdb1c52dc66a7c3c2936"]
    
    def classify_primitive(tx, is_token=False):
        to_addr = tx.get("to", "").lower()
        func_name = tx.get("functionName", "").lower()
        
        if to_addr in MIXER_ROUTERS or "tornado" in func_name: return "Mixer Deposit"
        if to_addr in DEX_ROUTERS or "swap" in func_name: return "DeFi Swap"
        if to_addr in BRIDGE_ROUTERS or "bridge" in func_name or "cross" in func_name: return "Bridge Cross-chain"
        if "mint" in func_name: return "Token Mint"
        if "burn" in func_name: return "Token Burn"
        if "deposit" in func_name: return "DeFi Deposit"
        if "withdraw" in func_name: return "DeFi Withdraw"
        if "stake" in func_name: return "Staking"
        if func_name and func_name != "0x" and "transfer" not in func_name: return "Smart Contract Call"
        
        return "Token Transfer" if is_token else "Native Transfer"

    events = []
    for tx in native + internal:
        try: amt = float(tx.get("value", 0)) / 1e18
        except: amt = 0.0
        events.append({"hash": tx.get("hash"), "to": tx.get("to", "").lower(), "from": tx.get("from", "").lower(), "amount": amt, "ticker": get_asset_ticker(chain), "type": classify_primitive(tx, False), "ts": tx.get("timeStamp", 0)})
    for tx in token:
        try: amt = float(tx.get("value", 0)) / (10 ** int(tx.get("tokenDecimal", 18)))
        except: amt = 0.0
        events.append({"hash": tx.get("hash"), "to": tx.get("to", "").lower(), "from": tx.get("from", "").lower(), "amount": amt, "ticker": tx.get("tokenSymbol", "ERC20"), "type": classify_primitive(tx, True), "ts": tx.get("timeStamp", 0)})
    
    events.sort(key=lambda x: int(float(x.get("ts", 0))), reverse=True) 
    return events

# ==============================================================================
# 🌐 6. FRONTEND HTML STRING (PREMIUM LIGHT-MODE SAAS UI)
# ==============================================================================
FRONTEND_HTML = r"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NEMESIS X | Global Intelligence Operating System</title>
    
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;800;900&family=Space+Mono:ital,wght@0,400;0,700;1,400&family=Playfair+Display:ital,wght@0,600;1,600&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script type="text/javascript" src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.10.1/html2pdf.bundle.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>

    <script>
        tailwind.config = {
            theme: {
                extend: {
                    fontFamily: { 
                        sans: ['Outfit', 'sans-serif'], 
                        mono: ['Space Mono', 'monospace'],
                        serif: ['Playfair Display', 'serif']
                    },
                    colors: { 
                        nemesis: { 50: '#f8fafc', 100: '#f1f5f9', 500: '#3b82f6', 600: '#2563eb', 900: '#0f172a' } 
                    },
                    animation: { 
                        'spin-slow': 'spin 12s linear infinite', 
                        'spin-reverse': 'spin 8s linear infinite reverse', 
                        'float': 'float 6s ease-in-out infinite' 
                    },
                    keyframes: { 
                        float: { '0%, 100%': { transform: 'translateY(0)' }, '50%': { transform: 'translateY(-10px)' } } 
                    }
                }
            }
        }
    </script>

    <style>
        /* LIGHT MODE PREMIUM SAAS AESTHETIC */
        body { background-color: #f8fafc; color: #1e293b; overflow-x: hidden; scroll-behavior: smooth; }
        ::-webkit-scrollbar { width: 6px; height: 6px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 10px; }
        
        #webgl-container { position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; z-index: -1; pointer-events: none; }
        .mesh-bg { position: fixed; inset: 0; z-index: -2; background: radial-gradient(circle at 10% 20%, rgba(224, 242, 254, 0.4) 0%, transparent 40%), radial-gradient(circle at 90% 80%, rgba(233, 213, 255, 0.4) 0%, transparent 40%); pointer-events: none; }

        /* Quantum Loader */
        #global-loader { position: fixed; inset: 0; background: rgba(255, 255, 255, 0.9); backdrop-filter: blur(24px); z-index: 9999; display: flex; flex-direction: column; align-items: center; justify-content: center; transition: opacity 0.5s ease; display: none; }
        .quantum-core { position: relative; width: 140px; height: 140px; transform-style: preserve-3d; animation: rotateCore 12s linear infinite; margin-bottom: 2.5rem; }
        .quantum-ring { position: absolute; inset: 0; border: 2px solid transparent; border-radius: 50%; box-shadow: 0 0 25px rgba(59, 130, 246, 0.2), inset 0 0 25px rgba(139, 92, 246, 0.2); border-top-color: #3b82f6; border-bottom-color: #8b5cf6; }
        .quantum-ring:nth-child(1) { transform: rotateX(75deg) rotateY(0deg); animation: spinRing 2s linear infinite; }
        .quantum-ring:nth-child(2) { transform: rotateX(75deg) rotateY(60deg); animation: spinRing 2.5s linear infinite reverse; }
        .quantum-ring:nth-child(3) { transform: rotateX(75deg) rotateY(120deg); animation: spinRing 3s linear infinite; }
        .quantum-particle { position: absolute; top: 50%; left: 50%; width: 20px; height: 20px; background: #fff; border-radius: 50%; transform: translate(-50%, -50%); box-shadow: 0 0 25px 8px #3b82f6, 0 0 50px 15px #8b5cf6; animation: pulseCore 1.5s ease-in-out infinite alternate; }
        @keyframes rotateCore { 0% { transform: rotateX(20deg) rotateY(0deg); } 100% { transform: rotateX(20deg) rotateY(360deg); } }
        @keyframes spinRing { 0% { transform: rotateZ(0deg); } 100% { transform: rotateZ(360deg); } }
        @keyframes pulseCore { 0% { transform: translate(-50%, -50%) scale(0.8); opacity: 0.8; } 100% { transform: translate(-50%, -50%) scale(1.2); opacity: 1; } }
        .progress-container { width: 320px; height: 4px; background: #e2e8f0; border-radius: 4px; overflow: hidden; margin-top: 1.5rem; }
        .progress-bar { height: 100%; width: 0%; background: linear-gradient(90deg, #3b82f6, #8b5cf6, #3b82f6); background-size: 200% 100%; transition: width 0.4s ease; }

        /* Premium Bento UI Cards */
        .glass-panel { background: rgba(255, 255, 255, 0.85); backdrop-filter: blur(20px); border: 1px solid rgba(226, 232, 240, 0.8); box-shadow: 0 4px 20px rgba(0,0,0,0.03); }
        .data-card { background: #ffffff; border: 1px solid #f1f5f9; border-radius: 1.5rem; padding: 1.75rem; box-shadow: 0 10px 40px -10px rgba(0,0,0,0.05); transition: all 0.3s ease; overflow: hidden; position: relative; }
        .data-card:hover { border-color: #e2e8f0; box-shadow: 0 15px 50px -10px rgba(37, 99, 235, 0.08); transform: translateY(-2px); }
        
        /* Typography & Tables */
        h1, h2, h3 { letter-spacing: -0.02em; }
        .cyber-table { width: 100%; border-collapse: separate; border-spacing: 0; }
        .cyber-table th { background: #f8fafc; border-bottom: 2px solid #e2e8f0; padding: 1rem; font-size: 0.7rem; font-weight: 700; text-transform: uppercase; color: #64748b; text-align: left; position: sticky; top: 0; z-index: 10; }
        .cyber-table td { border-bottom: 1px solid #f1f5f9; padding: 1rem; font-size: 0.8rem; color: #475569; transition: background 0.2s; }
        .cyber-table tr:hover td { background-color: #f8fafc; color: #0f172a; }

        /* Left Dock Navigation */
        .nav-dock { background: #ffffff; border: 1px solid #e2e8f0; box-shadow: 0 10px 30px -5px rgba(0, 0, 0, 0.05); }
        .nav-item { width: 3.5rem; height: 3.5rem; border-radius: 1rem; display: flex; align-items: center; justify-content: center; color: #94a3b8; transition: all 0.2s; position: relative; }
        .nav-item:hover { background: #f1f5f9; color: #3b82f6; transform: scale(1.05); }
        .nav-item.active { background: #eff6ff; color: #2563eb; border: 1px solid #bfdbfe; }
        
        .tab-content { display: none; animation: slideUp 0.4s ease forwards; }
        .tab-content.active { display: block; }
        @keyframes slideUp { from { opacity: 0; transform: translateY(15px); } to { opacity: 1; transform: translateY(0); } }

        .val-native { display: none; } body.show-native .val-native { display: inline-block; } body.show-native .val-usd { display: none; }
        
        /* Taxonomy Badges */
        .tag-swap { background: #eff6ff; color: #2563eb; border: 1px solid #bfdbfe; }
        .tag-bridge { background: #fdf4ff; color: #9333ea; border: 1px solid #e9d5ff; }
        .tag-mixer { background: #fef2f2; color: #dc2626; border: 1px solid #fecaca; }
        .tag-mint { background: #ecfdf5; color: #059669; border: 1px solid #a7f3d0; }
        .tag-standard { background: #f8fafc; color: #475569; border: 1px solid #e2e8f0; }

        #custom-context-menu { display: none; position: absolute; z-index: 1000; background: #ffffff; border: 1px solid #e2e8f0; border-radius: 0.75rem; box-shadow: 0 10px 30px rgba(0,0,0,0.1); padding: 0.5rem 0; min-width: 200px; }
        .context-menu-item { padding: 0.5rem 1rem; font-family: 'Space Mono', monospace; font-size: 0.75rem; color: #475569; cursor: pointer; transition: background 0.2s; display: flex; align-items: center; gap: 0.5rem; }
        .context-menu-item:hover { background: #f8fafc; color: #2563eb; }
        
        #side-panel { position: fixed; top: 0; right: -600px; width: 500px; height: 100vh; background: #ffffff; box-shadow: -10px 0 40px rgba(0,0,0,0.05); transition: right 0.3s ease; z-index: 999; border-left: 1px solid #e2e8f0; overflow-y: auto; }
        #side-panel.open { right: 0; }
        .doc-style { background: #fff; box-shadow: 0 10px 30px rgba(0,0,0,0.03); border: 1px solid #e2e8f0; }
    </style>
</head>
<body class="h-screen flex flex-col show-usd">
    
    <div class="mesh-bg"></div>
    <div id="webgl-container"></div>

    <!-- Minimalist Landing Screen -->
    <div id="pre-search-container" class="fixed inset-0 z-[9999] flex flex-col items-center justify-center transition-all duration-700 bg-white/70 backdrop-blur-xl">
        <div class="max-w-2xl w-full px-6">
            <div class="text-center mb-10 animate-float">
                <div class="w-20 h-20 bg-blue-600 rounded-2xl shadow-[0_10px_30px_rgba(37,99,235,0.3)] flex items-center justify-center mx-auto mb-6">
                    <i class="fa-solid fa-fingerprint text-3xl text-white"></i>
                </div>
                <h1 class="text-5xl md:text-6xl font-black text-slate-900 mb-2">NEMESIS</h1>
                <p class="text-slate-500 font-mono text-xs uppercase tracking-[0.2em]">Global Intelligence Operating System</p>
            </div>
            
            <div class="bg-white p-2 rounded-2xl shadow-[0_20px_50px_rgba(0,0,0,0.08)] border border-slate-100 flex flex-col md:flex-row gap-2">
                <div class="relative flex-grow">
                    <i class="fa-solid fa-magnifying-glass absolute left-5 top-1/2 -translate-y-1/2 text-slate-400"></i>
                    <input type="text" id="wallet-input-field" class="w-full bg-slate-50 border-none rounded-xl pl-12 pr-4 py-4 text-slate-900 font-mono text-sm outline-none focus:ring-2 focus:ring-blue-100 transition-all placeholder-slate-400" placeholder="Target Node (Address, IP, Hash)..." onkeydown="if(event.key === 'Enter') startDossierSearch(document.getElementById('wallet-input-field').value)">
                </div>
                <button onclick="startDossierSearch(document.getElementById('wallet-input-field').value)" class="bg-blue-600 hover:bg-blue-700 text-white font-bold py-4 px-8 rounded-xl transition-all font-mono uppercase tracking-widest text-xs flex items-center justify-center gap-2 shadow-md">
                    Deploy <i class="fa-solid fa-arrow-right"></i>
                </button>
            </div>
        </div>
    </div>
    
    <!-- Quantum Fusion Loader -->
    <div id="global-loader">
        <div class="quantum-core"><div class="quantum-ring"></div><div class="quantum-ring"></div><div class="quantum-ring"></div><div class="quantum-particle"></div></div>
        <h2 class="text-slate-900 font-bold text-lg tracking-widest uppercase">NEMESIS MATRIX SYNC</h2>
        <div id="real-time-status" class="text-slate-500 font-mono text-xs mt-3 tracking-widest uppercase h-6 text-center transition-all duration-300">Establishing Secure Connection...</div>
        <div class="progress-container"><div id="loader-progress-bar" class="progress-bar"></div></div>
    </div>

    <!-- MAIN DASHBOARD -->
    <div id="app-content" class="w-full max-w-[1800px] mx-auto p-4 md:p-8 hidden opacity-0 transition-opacity duration-700">
        
        <nav class="fixed left-6 top-1/2 -translate-y-1/2 z-[60] nav-dock rounded-[1.5rem] p-2 flex flex-col gap-2">
            <button class="nav-item active" onclick="switchIdTab('tab-profile', this)" title="Digital Twin Profile"><i class="fa-solid fa-building-user text-lg"></i></button>
            <button class="nav-item" onclick="switchIdTab('tab-graph', this)" title="Knowledge Graph"><i class="fa-solid fa-project-diagram text-lg"></i></button>
            <button class="nav-item" onclick="switchIdTab('tab-ai', this)" title="Cognitive AI"><i class="fa-solid fa-brain text-lg"></i></button>
            <div class="h-px w-6 mx-auto bg-slate-100 my-1"></div>
            <button class="nav-item hover:bg-red-50 hover:text-red-500 hover:border-red-100" onclick="location.reload()" title="New Scan"><i class="fa-solid fa-power-off text-lg"></i></button>
        </nav>

        <header class="glass-panel rounded-3xl px-8 py-5 mb-6 z-50 sticky top-4 ml-24 flex flex-col xl:flex-row justify-between items-center gap-6">
            <div class="flex items-center gap-5 w-full xl:w-auto">
                <div class="w-14 h-14 bg-blue-600 rounded-xl flex items-center justify-center shadow-lg shadow-blue-500/20 text-white">
                    <i class="fa-solid fa-fingerprint text-2xl"></i>
                </div>
                <div>
                    <h1 class="text-xl font-mono font-black text-slate-900 tracking-tight flex items-center gap-3">
                        <span id="hdr-address">0xPendingTarget...</span> 
                        <button onclick="copyToClipboard(document.getElementById('hdr-address').innerText)" class="text-slate-400 hover:text-blue-600 transition bg-slate-50 hover:bg-blue-50 px-2 py-1 rounded-md"><i class="fa-solid fa-copy text-xs"></i></button>
                    </h1>
                    <div class="flex items-center gap-3 mt-1.5">
                        <span class="bg-indigo-50 text-indigo-700 px-2.5 py-0.5 rounded text-[10px] font-bold font-mono border border-indigo-100 uppercase tracking-widest"><i class="fa-solid fa-link mr-1"></i> <span id="hdr-chain">ETH</span></span>
                        <span class="text-[10px] font-bold text-slate-500 uppercase tracking-widest bg-slate-100 px-3 py-0.5 rounded-full"><span id="hdr-entity">SUBJECT ENTITY</span></span>
                    </div>
                </div>
            </div>

            <div class="flex items-center gap-4 w-full xl:w-auto justify-end">
                <div id="hdr-aml-tags" class="flex gap-2"></div>
                <div class="h-6 w-px bg-slate-200 hidden sm:block mx-1"></div>
                <button onclick="toggleCurrency()" class="bg-white hover:bg-slate-50 border border-slate-200 text-slate-600 font-bold py-2 px-5 rounded-lg shadow-sm transition text-xs flex items-center gap-2 font-mono uppercase tracking-widest">
                    <i class="fa-solid fa-retweet text-blue-500"></i> <span class="hidden sm:inline">Toggle Value</span>
                </button>
            </div>
        </header>

        <div class="ml-24 flex flex-col gap-6" id="id-results-panel">
            
            <nav class="bg-white rounded-2xl flex overflow-x-auto p-1.5 gap-1.5 shadow-sm border border-slate-200 w-max">
                <button class="id-tab-btn tab-btn active px-5 py-2 rounded-xl bg-slate-50 text-slate-800 font-bold" onclick="switchIdTab('tab-profile', this)"><i class="fa-solid fa-id-card mr-2 text-blue-500"></i> Digital Twin</button>
                <button class="id-tab-btn tab-btn px-5 py-2 rounded-xl text-slate-500 hover:bg-slate-50" onclick="switchIdTab('tab-graph', this)"><i class="fa-solid fa-project-diagram mr-2"></i> Knowledge Graph</button>
                <button class="id-tab-btn tab-btn px-5 py-2 rounded-xl text-slate-500 hover:bg-slate-50" onclick="switchIdTab('tab-ai', this)"><i class="fa-solid fa-brain mr-2"></i> Cognitive AI</button>
            </nav>

            <div class="flex-grow">
                <!-- =====================================
                     TAB 1: PROFILE
                ====================================== -->
                <div id="tab-profile" class="id-tab-content tab-content active space-y-6">
                    <div class="grid grid-cols-2 md:grid-cols-4 gap-5">
                        <div class="data-card !bg-blue-600 text-white !border-blue-700"><p class="text-[10px] font-bold text-blue-200 uppercase tracking-widest mb-1">Truth Balance</p><h3 class="text-2xl font-black font-mono"><span class="val-usd" id="flow-bal-usd">--</span><span class="val-native" id="flow-bal-native">--</span></h3></div>
                        <div class="data-card"><p class="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">Total Inbound</p><h3 class="text-xl font-black text-slate-800 font-mono"><span class="val-usd text-emerald-600" id="flow-in-usd">--</span><span class="val-native text-emerald-600" id="flow-in-native">--</span></h3></div>
                        <div class="data-card"><p class="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">Total Outbound</p><h3 class="text-xl font-black text-slate-800 font-mono"><span class="val-usd text-red-600" id="flow-out-usd">--</span><span class="val-native text-red-600" id="flow-out-native">--</span></h3></div>
                        <div class="data-card"><p class="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">Tx Footprint</p><h3 class="text-xl font-black text-slate-800 font-mono" id="id-meta-tx">--</h3></div>
                    </div>
                    
                    <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
                        <div class="data-card md:col-span-2">
                            <h3 class="text-xs font-bold uppercase text-slate-400 tracking-widest mb-5 border-b border-slate-100 pb-2">Entity Metadata Ontology</h3>
                            <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 font-mono text-sm">
                                <div class="p-3 rounded-lg border border-slate-100 bg-slate-50"><span class="block text-[10px] text-slate-400 uppercase mb-1">Identity Binding</span><strong id="id-meta-class" class="text-slate-800">--</strong></div>
                                <div class="p-3 rounded-lg border border-slate-100 bg-slate-50"><span class="block text-[10px] text-slate-400 uppercase mb-1">Network Context</span><strong id="id-meta-net" class="text-slate-800">--</strong></div>
                                <div class="p-3 rounded-lg border border-slate-100 bg-slate-50"><span class="block text-[10px] text-slate-400 uppercase mb-1">Genesis / First Seen</span><strong id="id-meta-first" class="text-slate-800">--</strong></div>
                                <div class="p-3 rounded-lg border border-slate-100 bg-slate-50"><span class="block text-[10px] text-slate-400 uppercase mb-1">Terminal / Last Seen</span><strong id="id-meta-last" class="text-slate-800">--</strong></div>
                            </div>
                        </div>

                        <div class="data-card flex flex-col items-center justify-center text-center !bg-slate-50">
                            <h3 class="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-5">Threat Actor Score</h3>
                            <div class="w-32 h-32 rounded-full border-[6px] border-white flex items-center justify-center relative shadow-sm bg-white" id="aml-ring">
                                <span class="text-4xl font-black font-mono text-slate-800" id="aml-score">0</span>
                            </div>
                            <span class="mt-5 bg-white text-slate-600 px-4 py-1.5 rounded-md text-[10px] font-bold uppercase tracking-widest border border-slate-200 shadow-sm" id="aml-label">Unscanned</span>
                        </div>
                    </div>
                    
                    <div id="prof-ai-summary" class="text-sm text-slate-700 font-serif leading-relaxed bg-white p-6 rounded-2xl border border-slate-200 shadow-sm border-l-4 border-l-blue-500"></div>
                    
                    <div class="data-card p-0">
                        <div class="p-5 border-b border-slate-100 bg-slate-50/80 flex justify-between items-center">
                            <h3 class="text-xs font-bold uppercase text-slate-500 tracking-widest flex items-center gap-2"><i class="fa-solid fa-clock-rotate-left text-blue-500"></i> Temporal Graph Ledger</h3>
                            <span class="text-[9px] font-mono text-emerald-600 bg-emerald-50 border border-emerald-100 px-2 py-0.5 rounded font-bold">TAXONOMY ACTIVE</span>
                        </div>
                        <div class="overflow-auto max-h-[500px]">
                            <table class="cyber-table w-full text-left">
                                <thead><tr><th>Date</th><th>Taxonomy</th><th>Hash</th><th>Flow</th><th>Counterparty</th><th class="text-right">Value</th></tr></thead>
                                <tbody id="id-tx-body" class="font-mono text-xs divide-y divide-slate-100"></tbody>
                            </table>
                        </div>
                    </div>
                </div>
                
                <!-- =====================================
                     TAB 2: GRAPH
                ====================================== -->
                <div id="tab-graph" class="id-tab-content tab-content h-[700px]">
                    <div class="data-card p-0 w-full h-full relative flex flex-col">
                        <div class="absolute top-4 left-4 z-10 bg-white/90 backdrop-blur px-3 py-2 rounded-lg border border-slate-200 text-[10px] font-mono font-bold text-slate-600 shadow-sm flex items-center gap-2">
                            <span class="w-1.5 h-1.5 rounded-full bg-blue-500 animate-pulse"></span> TRACE ACTIVE
                        </div>
                        <div id="id-vis-network" class="flex-grow w-full rounded-2xl" style="background-color: #f8fafc; background-image: radial-gradient(#e2e8f0 1px, transparent 1px); background-size: 20px 20px;"></div>
                    </div>
                </div>
                
                <!-- =====================================
                     TAB 3: AI INSIGHTS
                ====================================== -->
                <div id="tab-ai" class="id-tab-content tab-content space-y-6">
                    <div class="data-card doc-style max-w-4xl mx-auto">
                        <div class="flex justify-between items-center border-b border-slate-200 pb-5 mb-6">
                            <div>
                                <h2 class="text-xl font-black text-slate-900 uppercase tracking-widest flex items-center gap-2 font-serif"><i class="fa-solid fa-file-contract text-blue-600"></i> Forensic Affidavit</h2>
                                <p class="text-slate-400 text-[10px] font-mono mt-1 uppercase tracking-widest">Generated by Deep-Mind AI Swarm</p>
                            </div>
                            <button onclick="window.print()" class="bg-slate-900 hover:bg-blue-600 text-white px-5 py-2 rounded-lg text-xs font-bold font-mono uppercase tracking-widest transition shadow-sm"><i class="fa-solid fa-print mr-2"></i> Print</button>
                        </div>
                        <div class="prose max-w-none text-sm text-slate-700 font-serif leading-loose" id="id-ai-report">
                            Awaiting Matrix Sync...
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Right-Click Menu -->
    <div id="custom-context-menu">
        <div class="px-3 py-2 border-b border-slate-100 text-[9px] font-bold text-slate-400 uppercase tracking-widest mb-1 bg-slate-50 rounded-t-lg">Entity Operations</div>
        <div class="context-menu-item" onclick="closeContextMenu()"><i class="fa-solid fa-microchip text-blue-500 w-4"></i> Run Diagnostics</div>
        <div class="context-menu-item" onclick="closeContextMenu()"><i class="fa-solid fa-globe text-emerald-500 w-4"></i> OSINT Surface Scan</div>
        <div class="context-menu-item border-t border-slate-100 mt-1 pt-1" onclick="closeContextMenu()"><i class="fa-solid fa-xmark w-4"></i> Close</div>
    </div>

    <!-- Side Panel -->
    <div id="side-panel" class="flex flex-col">
        <div class="bg-slate-50 border-b border-slate-200 text-slate-900 p-4 flex justify-between items-center sticky top-0 z-10">
            <h3 class="font-bold tracking-widest uppercase text-xs flex items-center gap-2 font-mono text-slate-600"><i class="fa-solid fa-folder-open text-blue-500"></i> Intelligence Detail</h3>
            <button onclick="closeSidePanel()" class="text-slate-400 hover:text-slate-700 transition"><i class="fa-solid fa-xmark text-lg"></i></button>
        </div>
        <div class="p-6 text-sm font-mono text-slate-600" id="side-panel-content"></div>
    </div>

    <script>
        function switchIdTab(tabId, btn) {
            document.querySelectorAll('.id-tab-content').forEach(c => c.classList.remove('active'));
            document.querySelectorAll('.id-tab-btn').forEach(b => {
                b.classList.remove('active', 'bg-slate-50', 'text-slate-800', 'font-bold');
                b.classList.add('text-slate-500');
            });
            document.getElementById(tabId).classList.add('active');
            if(btn) {
                btn.classList.add('active', 'bg-slate-50', 'text-slate-800', 'font-bold');
                btn.classList.remove('text-slate-500');
            }
            if(tabId === 'tab-graph' && window.idGraphNodes && !window.idGraphInited) { renderIdGraph(); window.idGraphInited = true; }
        }

        function toggleCurrency() { document.body.classList.toggle('show-usd'); document.body.classList.toggle('show-native'); }
        function copyToClipboard(text) { navigator.clipboard.writeText(text); alert("Node address copied to secure clipboard."); }
        function closeContextMenu() { document.getElementById('custom-context-menu').style.display = 'none'; }
        function closeSidePanel() { document.getElementById('side-panel').classList.remove('open'); }

        function openDossier(title) {
            document.getElementById('side-panel-content').innerHTML = `<h4 class="font-black text-slate-900 uppercase text-base border-b border-slate-200 pb-2 mb-4"><i class="fa-solid fa-microchip text-blue-600 mr-2"></i> ${title}</h4><p class="text-xs text-slate-500 leading-relaxed">NEMESIS X Entity details rendered here.</p>`;
            document.getElementById('side-panel').classList.add('open');
        }

        function initWeb3GLBackground() {
            const canvas = document.getElementById('webgl-container');
            if(!canvas || !window.THREE) return;
            const scene = new THREE.Scene(); 
            scene.fog = new THREE.FogExp2(0xf8fafc, 0.002);
            
            const camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.1, 1000);
            const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true }); 
            renderer.setSize(window.innerWidth, window.innerHeight); 
            renderer.setPixelRatio(window.devicePixelRatio);
            canvas.appendChild(renderer.domElement);
            
            const particleCount = 120;
            const geometry = new THREE.BufferGeometry(); 
            const positions = new Float32Array(particleCount * 3);
            for (let i = 0; i < particleCount * 3; i++) positions[i] = (Math.random() - 0.5) * 800;
            geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
            
            const material = new THREE.PointsMaterial({color: 0x94a3b8, size: 3, transparent: true, opacity: 0.6, sizeAttenuation: true}); 
            const particles = new THREE.Points(geometry, material); 
            scene.add(particles);
            
            const lineMaterial = new THREE.LineBasicMaterial({color: 0xcbd5e1, transparent: true, opacity: 0.2});
            const lineGeometry = new THREE.BufferGeometry();
            const linePositions = new Float32Array(particleCount * particleCount * 3); 
            lineGeometry.setAttribute('position', new THREE.BufferAttribute(linePositions, 3));
            const linesMesh = new THREE.LineSegments(lineGeometry, lineMaterial);
            scene.add(linesMesh);
            
            camera.position.z = 400; 
            
            let mouseX = 0; let mouseY = 0;
            document.addEventListener('mousemove', (event) => {
                mouseX = (event.clientX - window.innerWidth / 2) * 0.05;
                mouseY = (event.clientY - window.innerHeight / 2) * 0.05;
            });

            let time = 0;
            function animate() { 
                requestAnimationFrame(animate); 
                time += 0.001; 
                particles.rotation.y = time * 0.1; particles.rotation.x = time * 0.05;
                linesMesh.rotation.y = time * 0.1; linesMesh.rotation.x = time * 0.05;
                camera.position.x += (mouseX - camera.position.x) * 0.02;
                camera.position.y += (-mouseY - camera.position.y) * 0.02;
                camera.lookAt(scene.position);

                const pos = particles.geometry.attributes.position.array;
                let vIdx = 0;
                for (let i = 0; i < particleCount; i++) {
                    for (let j = i + 1; j < particleCount; j++) {
                        const dx = pos[i*3] - pos[j*3]; const dy = pos[i*3+1] - pos[j*3+1]; const dz = pos[i*3+2] - pos[j*3+2];
                        if (Math.sqrt(dx*dx + dy*dy + dz*dz) < 120) { 
                            linePositions[vIdx++] = pos[i*3]; linePositions[vIdx++] = pos[i*3+1]; linePositions[vIdx++] = pos[i*3+2];
                            linePositions[vIdx++] = pos[j*3]; linePositions[vIdx++] = pos[j*3+1]; linePositions[vIdx++] = pos[j*3+2];
                        }
                    }
                }
                linesMesh.geometry.setDrawRange(0, vIdx / 3);
                linesMesh.geometry.attributes.position.needsUpdate = true;
                renderer.render(scene, camera); 
            } 
            animate();
            window.addEventListener('resize', () => { camera.aspect = window.innerWidth / window.innerHeight; camera.updateProjectionMatrix(); renderer.setSize(window.innerWidth, window.innerHeight); });
        }

        document.addEventListener('DOMContentLoaded', () => { 
            initWeb3GLBackground(); 
            document.addEventListener('click', (e) => {
                if(!e.target.closest('#custom-context-menu')) closeContextMenu();
            });
        });

        let idNetGraph = null;
        function renderIdGraph() {
            if(!window.idGraphNodes || !window.idGraphNodes.counterparties) return;
            const container = document.getElementById('id-vis-network');
            let gNodes = new vis.DataSet([{ id: 'SUBJECT', label: 'TARGET\n' + window.idGraphNodes.target.substring(0,8), color: {background: '#3b82f6', border: '#2563eb'}, size: 30, shape: 'dot', font: {color: '#ffffff', face: 'Space Mono', bold: true}, borderWidth: 3 }]);
            let gEdges = new vis.DataSet([]);
            
            window.idGraphNodes.counterparties.slice(0, 50).forEach((cp) => {
                gNodes.add({ id: cp.name, label: cp.name.substring(0,8), color: {background: '#ffffff', border: '#cbd5e1'}, size: 12, shape: 'dot', font: {color: '#475569', face: 'Space Mono', size: 10}, borderWidth: 2 });
                if(cp.inbound > 0) gEdges.add({ from: cp.name, to: 'SUBJECT', color: {color: '#10b981'}, label: cp.inbound.toFixed(2) });
                if(cp.outbound > 0) gEdges.add({ from: 'SUBJECT', to: cp.name, color: {color: '#ef4444'}, label: cp.outbound.toFixed(2) });
            });

            if(idNetGraph) idNetGraph.destroy();
            idNetGraph = new vis.Network(container, {nodes: gNodes, edges: gEdges}, {
                physics: { solver: 'forceAtlas2Based', forceAtlas2Based: { gravitationalConstant: -30, centralGravity: 0.01, springLength: 120 } },
                edges: { arrows: 'to', font: { size: 9, align: 'middle', background: 'rgba(255,255,255,0.9)', color: '#475569' }, smooth: { type: 'continuous' } }
            });

            idNetGraph.on("oncontext", function (params) {
                params.event.preventDefault();
                const nodeId = this.getNodeAt(params.pointer.DOM);
                if (nodeId) {
                    const menu = document.getElementById('custom-context-menu'); 
                    menu.style.display = 'block'; 
                    menu.style.left = (params.pointer.DOM.x + container.getBoundingClientRect().left) + 'px'; 
                    menu.style.top = (params.pointer.DOM.y + container.getBoundingClientRect().top) + 'px'; 
                }
            });
            
            idNetGraph.on("click", function(params) {
                if (params.nodes.length > 0) openDossier("Node: " + gNodes.get(params.nodes[0]).label);
                else closeSidePanel();
            });
        }

        let loaderInterval = null;
        function startLoader() {
            const loader = document.getElementById('global-loader');
            const statusEl = document.getElementById('real-time-status');
            const progressBar = document.getElementById('loader-progress-bar');
            loader.style.display = 'flex';
            setTimeout(() => loader.style.opacity = '1', 10);
            
            const messages = ["Initiating Global Intelligence Corpus...", "Querying Parallel Trace RPCs...", "Evaluating Taxonomy Patterns...", "Deploying Deep-Mind Swarm...", "Constructing Digital Twin..."];
            let msgIndex = 0; statusEl.innerText = messages[0]; progressBar.style.width = '10%';
            
            loaderInterval = setInterval(() => {
                if (msgIndex < messages.length - 1) {
                    msgIndex++; statusEl.innerText = messages[msgIndex];
                    progressBar.style.width = (10 + ((90 / messages.length) * msgIndex)) + '%';
                }
            }, 1800);
        }

        function stopLoader(success = true) {
            clearInterval(loaderInterval);
            const progressBar = document.getElementById('loader-progress-bar');
            const statusEl = document.getElementById('real-time-status');
            if (success) { progressBar.style.width = '100%'; statusEl.innerText = "DIGITAL TWIN CONSTRUCTED."; statusEl.style.color = "#10b981"; } 
            else { statusEl.innerText = "FUSION FAILED."; statusEl.style.color = "#ef4444"; progressBar.style.background = "#ef4444"; }
            
            setTimeout(() => {
                const loader = document.getElementById('global-loader');
                loader.style.opacity = '0';
                setTimeout(() => { loader.style.display = 'none'; statusEl.style.color = "#64748b"; progressBar.style.background = "linear-gradient(90deg, #3b82f6, #8b5cf6)"; }, 500);
            }, 800);
        }

        async function startDossierSearch(address) {
            if(!address || address.trim() === '') return;
            const preSearch = document.getElementById('pre-search-container');
            if(preSearch) { preSearch.style.opacity = '0'; setTimeout(() => preSearch.style.display = 'none', 500); }
            startLoader();
            try {
                const res = await fetch('/api/dossier?address=' + encodeURIComponent(address));
                if (!res.ok) throw new Error("API request failed");
                const json = await res.json();
                if(json.status === 'success') { populateDashboard(json.data); stopLoader(true); } 
                else { alert("Error loading dossier."); stopLoader(false); }
            } catch(e) { console.error(e); alert("Engine connection failed."); stopLoader(false); }
        }
        
        function populateDashboard(data) {
            const txs = Array.isArray(data.transactions) ? data.transactions : (data.transactions?.history || []);
            
            if (txs.length === 0) {
                document.getElementById('prof-ai-summary').innerHTML = `
                    <div class="p-6 border border-amber-200 bg-amber-50 rounded-xl shadow-sm">
                        <h3 class="text-amber-700 font-bold text-sm mb-2"><i class="fas fa-exclamation-triangle mr-2"></i> DATA VOID DETECTED</h3>
                        <p class="text-slate-600 text-xs font-sans leading-relaxed">The Temporal Graph Engine processed this entity, but no on-chain activity was detected. This node appears to be dormant.</p>
                    </div>`;
            } else { document.getElementById('prof-ai-summary').innerHTML = `<strong>Intelligence Summary:</strong> ${data.ai_summary}`; }

            // Bind Header
            document.getElementById('hdr-address').innerText = data.address.substring(0, 16) + '...';
            document.getElementById('hdr-entity').innerText = data.entity;
            document.getElementById('hdr-chain').innerText = data.chain;
            
            // Bind Metrics
            document.getElementById('id-meta-class').innerText = data.entity_class;
            document.getElementById('id-meta-net').innerText = data.chain;
            document.getElementById('id-meta-tx').innerText = data.tx_count.toLocaleString();
            document.getElementById('id-meta-first').innerText = data.first_seen || 'N/A';
            document.getElementById('id-meta-last').innerText = data.last_seen || 'N/A';
            
            document.getElementById('flow-bal-usd').innerText = "$" + Number(data.balance_usd).toLocaleString(undefined, {maximumFractionDigits:2});
            document.getElementById('flow-bal-native').innerText = Number(data.balance_native).toFixed(4) + " " + data.ticker;
            document.getElementById('flow-in-usd').innerText = "$" + Number(data.total_inbound_usd).toLocaleString(undefined, {maximumFractionDigits:2});
            document.getElementById('flow-in-native').innerText = Number(data.total_inbound_native).toFixed(4) + " " + data.ticker;
            document.getElementById('flow-out-usd').innerText = "$" + Number(data.total_outbound_usd).toLocaleString(undefined, {maximumFractionDigits:2});
            document.getElementById('flow-out-native').innerText = Number(data.total_outbound_native).toFixed(4) + " " + data.ticker;

            // Render Transactions with Behavioral Badges
            let tbody = document.getElementById('id-tx-body');
            tbody.innerHTML = '';
            if(txs.length > 0) {
                txs.forEach(tx => {
                    let isOut = tx.flow === 'OUT';
                    let cp = isOut ? tx.receiver_entity : tx.sender_entity;
                    let flowIcon = isOut ? '<span class="text-red-500 font-bold"><i class="fa-solid fa-arrow-right"></i> OUT</span>' : '<span class="text-emerald-500 font-bold"><i class="fa-solid fa-arrow-left"></i> IN</span>';
                    
                    let badgeClass = 'tag-standard';
                    let icon = 'fa-arrow-right-arrow-left';
                    if(tx.type.includes('Mixer')) { badgeClass = 'tag-mixer'; icon = 'fa-mask'; }
                    else if(tx.type.includes('Swap')) { badgeClass = 'tag-swap'; icon = 'fa-retweet'; }
                    else if(tx.type.includes('Bridge')) { badgeClass = 'tag-bridge'; icon = 'fa-bridge'; }
                    else if(tx.type.includes('Mint')) { badgeClass = 'tag-mint'; icon = 'fa-plus'; }

                    tbody.innerHTML += `<tr class="border-b border-slate-100 hover:bg-slate-50 transition cursor-pointer" onclick="verifyOnExplorer('${tx.hash}')">
                        <td class="text-slate-400">${tx.timestamp.substring(0,19)}</td>
                        <td><span class="px-2 py-0.5 rounded text-[9px] font-bold uppercase tracking-widest shadow-sm ${badgeClass}"><i class="fa-solid ${icon} mr-1"></i> ${tx.type}</span></td>
                        <td class="text-blue-600 font-bold hover:underline">${tx.hash.substring(0,10)}...</td>
                        <td class="text-center font-black">${flowIcon}</td>
                        <td class="font-mono">${cp.substring(0,12)}...</td>
                        <td class="text-right font-black text-slate-800"><span class="val-usd">$${Number(tx.value_usd).toLocaleString(undefined,{maximumFractionDigits:2})}</span><span class="val-native">${Number(tx.value_native).toFixed(4)} ${tx.ticker}</span></td>
                    </tr>`;
                });
            } else { tbody.innerHTML = '<tr><td colspan="6" class="text-center text-slate-400 italic py-8">No temporal graph nodes found.</td></tr>'; }

            // AML Ring
            const rScore = data.risk_score;
            document.getElementById('aml-score').innerText = rScore;
            const amlRing = document.getElementById('aml-ring');
            const amlLabel = document.getElementById('aml-label');
            const hdrAmlTags = document.getElementById('hdr-aml-tags');
            
            if (rScore >= 80) {
                amlRing.className = "w-32 h-32 rounded-full border-[6px] border-red-500 flex items-center justify-center relative bg-red-50 shadow-sm";
                amlLabel.innerText = "Critical Alert"; amlLabel.className = "mt-5 bg-red-600 text-white px-4 py-1.5 rounded-md text-[10px] font-bold uppercase tracking-widest shadow-sm";
                document.getElementById('aml-score').classList.replace("text-slate-800", "text-red-600");
                hdrAmlTags.innerHTML = `<span class="bg-red-50 text-red-700 border border-red-200 px-3 py-1 rounded-md text-[10px] font-bold font-mono shadow-sm"><i class="fa-solid fa-skull mr-1"></i> Threat: CRITICAL</span>`;
            } else if (rScore >= 40) {
                amlRing.className = "w-32 h-32 rounded-full border-[6px] border-amber-500 flex items-center justify-center relative bg-amber-50 shadow-sm";
                amlLabel.innerText = "High Risk"; amlLabel.className = "mt-5 bg-amber-500 text-white px-4 py-1.5 rounded-md text-[10px] font-bold uppercase tracking-widest shadow-sm";
                document.getElementById('aml-score').classList.replace("text-slate-800", "text-amber-600");
                hdrAmlTags.innerHTML = `<span class="bg-amber-50 text-amber-700 border border-amber-200 px-3 py-1 rounded-md text-[10px] font-bold font-mono shadow-sm"><i class="fa-solid fa-triangle-exclamation mr-1"></i> Threat: ELEVATED</span>`;
            } else {
                amlRing.className = "w-32 h-32 rounded-full border-[6px] border-emerald-500 flex items-center justify-center relative bg-emerald-50 shadow-sm";
                amlLabel.innerText = "Neutral / Clean"; amlLabel.className = "mt-5 bg-emerald-500 text-white px-4 py-1.5 rounded-md text-[10px] font-bold uppercase tracking-widest shadow-sm";
                document.getElementById('aml-score').classList.replace("text-slate-800", "text-emerald-600");
                hdrAmlTags.innerHTML = `<span class="bg-emerald-50 text-emerald-700 border border-emerald-200 px-3 py-1 rounded-md text-[10px] font-bold font-mono shadow-sm"><i class="fa-solid fa-shield-check mr-1"></i> Threat: LOW</span>`;
            }

            let aiText = `**Cognitive Executive Summary:**\n${data.ai_summary}\n\n**Forensic Affidavit:**\n${data.ai_insights}`;
            document.getElementById('id-ai-report').innerHTML = marked.parse(aiText);

            window.idGraphNodes = { target: data.address, counterparties: data.counterparties || [] };
            window.idGraphInited = false;
            
            document.getElementById('app-content').classList.remove('hidden');
            setTimeout(() => document.getElementById('app-content').classList.remove('opacity-0'), 50);
            switchIdTab('tab-profile', document.querySelector('.id-tab-btn.active'));
        }
    </script>
</body>
</html>
"""

# ==============================================================================
# 🚀 8. FASTAPI ROUTES & MOUNTING (WITH CACHING)
# ==============================================================================
SIMPLE_CACHE = {}
CACHE_TTL = 3600

@asynccontextmanager
async def lifespan(app: FastAPI):
    if PLAYWRIGHT_AVAILABLE: asyncio.create_task(OSINT.start_browser())
    yield
    logger.info("🛑 SHUTTING DOWN NEMESIS OS")

app = FastAPI(title="Lionsgate Nemesis X", lifespan=lifespan)

@app.get("/api/dossier")
async def get_dossier(address: str, chain: str = "AUTO"):
    """NEMESIS X: Layer 1-9 Intelligence Mapping"""
    chain = detect_chain(address, chain)
    if chain == "UNKNOWN": chain = "ETHEREUM"
    
    cache_key = f"{address.lower()}_{chain}"
    if cache_key in SIMPLE_CACHE:
        cached_time, cached_data = SIMPLE_CACHE[cache_key]
        if time.time() - cached_time < CACHE_TTL: return cached_data
            
    entity_label = await OSINT.scrape_entity(address, chain)
    e_upper = entity_label.upper()
    
    entity_class = "PRIVATE"
    if any(k in e_upper for k in ["BINANCE", "KRAKEN", "COINBASE", "KUCOIN", "OKX", "MEXC", "HOT WALLET"]): entity_class = "EXCHANGE"
    elif "TORNADO" in e_upper or "MIXER" in e_upper: entity_class = "MIXER"
    elif "BRIDGE" in e_upper: entity_class = "BRIDGE"

    risk_score = 100 if entity_class == "MIXER" else (10 if entity_class == "EXCHANGE" else 45)
    
    total_inbound = 0.0
    total_outbound = 0.0
    formatted_txs = []
    counterparties = defaultdict(lambda: {"inbound": 0.0, "outbound": 0.0, "type": "PRIVATE"})
    first_seen, last_seen = "N/A", "N/A"
    ticker = get_asset_ticker(chain)
    
    try:
        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(limit=50)) as session:
            events = await unified_fetch_all_txs(session, address, chain)

            if len(events) > 0:
                first_seen = datetime.fromtimestamp(int(float(events[-1].get("ts", 0)))).strftime('%Y-%m-%d %H:%M:%S')
                last_seen = datetime.fromtimestamp(int(float(events[0].get("ts", 0)))).strftime('%Y-%m-%d %H:%M:%S')

            for e in events:
                amt = e.get("amount", 0.0)
                is_outbound = e.get("from", "").lower() == address.lower()
                cp = e.get("to") if is_outbound else e.get("from")
                
                if is_outbound:
                    total_outbound += amt
                    counterparties[cp]["outbound"] += amt
                else:
                    total_inbound += amt
                    counterparties[cp]["inbound"] += amt
                
                try: ts_int = int(float(e.get("ts", 0)))
                except: ts_int = 0
                
                formatted_txs.append({
                    "timestamp": datetime.fromtimestamp(ts_int).strftime('%Y-%m-%d %H:%M:%S') if ts_int > 0 else "N/A", 
                    "hash": e.get("hash", ""), 
                    "flow": "OUT" if is_outbound else "IN",
                    "sender_entity": e.get("from", "").lower(), "receiver_entity": e.get("to", "").lower(),
                    "value_native": amt, "value_usd": amt * 3000.0, "ticker": e.get("ticker", ticker), "type": e.get("type", "TRANSFER")
                })
    except Exception as e:
        logger.error(f"Dossier Fetch Error: {e}")

    balance = max(0.0, total_inbound - total_outbound)
    cp_list = [{"name": k, "type": v["type"], "inbound": v["inbound"], "outbound": v["outbound"]} for k, v in counterparties.items()]

    ai_sum, ai_aff = await INVESTIGATOR_SWARM.process_digital_twin(address, chain, entity_label, risk_score, len(events), balance * 3000.0)

    payload = {
        "status": "success",
        "data": {
            "address": address, "chain": chain, "entity": entity_label, "entity_class": entity_class,
            "ticker": ticker,
            "risk_score": risk_score,
            "ai_summary": ai_sum,
            "ai_insights": ai_aff,
            "tx_count": len(events), "first_seen": first_seen, "last_seen": last_seen,
            "total_inbound_usd": total_inbound * 3000.0, "total_inbound_native": total_inbound,
            "total_outbound_usd": total_outbound * 3000.0, "total_outbound_native": total_outbound,
            "balance_usd": balance * 3000.0, "balance_native": balance,
            "transactions": formatted_txs[:150],
            "counterparties": cp_list
        }
    }
    
    SIMPLE_CACHE[cache_key] = (time.time(), payload)
    return payload

if __name__ == "__main__":
    print("""
    ███╗   ██╗███████╗███╗   ███╗███████╗███████╗██╗███████╗
    ████╗  ██║██╔════╝████╗ ████║██╔════╝██╔════╝██║██╔════╝
    ██╔██╗ ██║█████╗  ██╔████╔██║█████╗  ███████╗██║███████╗
    ██║╚██╗██║██╔══╝  ██║╚██╔╝██║██╔══╝  ╚════██║██║╚════██║
    ██║ ╚████║███████╗██║ ╚═╝ ██║███████╗███████║██║███████║
    ╚═╝  ╚═══╝╚══════╝╚═╝     ╚═╝╚══════╝╚══════╝╚═╝╚══════╝
    [v12000.0] NEMESIS X - GLOBAL INTELLIGENCE OS ONLINE
    """)
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)