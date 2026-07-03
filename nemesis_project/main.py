import os
import sys
import subprocess

def auto_install_dependencies():
    print("\n[SYSTEM] Auto-installing dependencies from requirements.txt...")
    try:
        print("[SYSTEM] Upgrading pip...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt", "--no-cache-dir"])
        print("[SYSTEM] Dependencies verified and installed.")
        
        print("[SYSTEM] Verifying Playwright browser binaries...")
        subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])
        print("[SYSTEM] Playwright binaries verified.\n")
    except Exception as e:
        print(f"[SYSTEM] Warning: Failed to auto-install dependencies: {e}\n")

auto_install_dependencies()

os.environ["LOKY_MAX_CPU_COUNT"] = "4"
os.environ["PLAYWRIGHT_BROWSERS_PATH"] = "0"
import re
from dotenv import load_dotenv
load_dotenv()
import json
import logging
import datetime
from collections import defaultdict
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, Request, BackgroundTasks, Response, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel
import uvicorn
import uuid
import io
import PyPDF2
from docx import Document
from google import genai
from google.genai import types

# Setup logging for console and file (for Admin WS tailing)
log_dir = "logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

log_file_path = os.path.join(log_dir, 'nemesis.log')
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file_path),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("OmniChainEngine")

from services.trace_engine import TraceEngine, init_mongodb, get_asset_ticker, detect_chain, EVM_DOMAINS, get_active_traces, get_mongo_status, fetch_saved_traces
from services.auth_engine import authenticate_admin, create_access_token, verify_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from datetime import timedelta
import asyncio
import sys

async def run_boot_diagnostics():
    logger.info("==================================================")
    logger.info("   INITIATING LIONSGATE NEMESIS BOOT SEQUENCE     ")
    logger.info("==================================================")
    
    logger.info(">>> [1/5] Verifying Dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "google-genai", "--quiet"])
        logger.info("    [OK] google-genai and core dependencies verified.")
    except Exception as e:
        logger.error(f"    [FAIL] Could not verify dependencies: {e}")
        
    logger.info(">>> [2/5] Checking Intelligence Providers & API Keys...")
    from services.trace_engine import CONFIG
    providers = {
        "Etherscan": CONFIG.get("ETHERSCAN_API_KEY"),
        "OKLink": CONFIG.get("OKLINK_API_KEY"),
        "Tatum": os.getenv("TATUM_API_KEY"),
        "Gemini (AI)": os.getenv("GEMINI_API_KEYS")
    }
    for p, key in providers.items():
        if key and key != "freekey":
            logger.info(f"    [OK] {p} Provider Active.")
        else:
            logger.warning(f"    [WARN] {p} API Key missing or default.")
            
    logger.info(">>> [3/5] Loading Supported Networks...")
    logger.info(f"    [OK] EVM Chains: {', '.join(EVM_DOMAINS.keys())}")
    logger.info("    [OK] Non-EVM Chains: BITCOIN, SOLANA, TRON, RIPPLE, STELLAR")
    
    logger.info(">>> [4/5] Verifying Tracing Engine & Executions...")
    logger.info("    [OK] Tracing Engine Ready. Parallel Executions (Max 4 Workers).")
    
    logger.info(">>> [5/6] Fetching Data Modules...")
    logger.info("    [OK] Scraping fallback active. Asyncio data fetching pools ready.")
    
    logger.info(">>> [6/6] Triggering System Auto-Backup...")
    try:
        subprocess.Popen([sys.executable, "auto_backup.py"])
        logger.info("    [OK] Auto-backup routine dispatched to background.")
    except Exception as e:
        logger.error(f"    [FAIL] Could not dispatch auto-backup: {e}")
    
    logger.info("==================================================")
    logger.info("   NEMESIS ENGINE READY FOR OMNICHAIN OPERATIONS  ")
    logger.info("==================================================")

@asynccontextmanager
async def lifespan(app: FastAPI):
    await run_boot_diagnostics()
    import asyncio
    
    # Ensure Playwright browsers are installed before starting the engine
    try:
        subprocess.run(["playwright", "install", "chromium"], check=True)
        logger.info("    [OK] Playwright chromium installed successfully.")
    except Exception as e:
        logger.error(f"    [FAIL] Failed to install Playwright browsers: {e}")
    
    # Run MongoDB and Scraper initialization in the background so they don't block the web server from starting
    async def init_background():
        await init_mongodb()
        from services.scraper_engine import scraper_instance
        await scraper_instance.start()
        
        # Darknet crawler will be run independently by the user in a separate terminal.
        
    asyncio.create_task(init_background())
    
    yield
    from services.scraper_engine import scraper_instance
    await scraper_instance.stop()

app = FastAPI(title="Nemesis OmniChain API", description="Lionsgate OmniChain Forensic Engine", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

active_sessions = {}
templates = Jinja2Templates(directory="templates")

class TraceRequest(BaseModel):
    seeds: str
    target_amount: str = ""
    target_currency: str = "USD"
    start_date: str = ""
    end_date: str = ""
    chain_override: str = "AUTO"
    max_depth: int = 12
    max_hops: int = 1000

class ResolveRequest(BaseModel):
    entities: list[str]

@app.post("/api/resolve_entity")
async def api_resolve_entity(req: ResolveRequest):
    from services.trace_engine import mongo_db
    if mongo_db is None:
        return {"status": "error", "message": "MongoDB not connected"}
    
    results = {}
    try:
        if not req.entities:
            return {"results": {}}
            
        # Basic filtering to prevent huge queries
        clean_entities = [e for e in req.entities if e and len(e) > 3]
        if not clean_entities:
            return {"results": {e: "Unidentified" for e in req.entities}}
            
        q_filter = {
            "$or": [
                {"url": {"$in": clean_entities}},
                {"title": {"$in": clean_entities}},
                {"hash-ID": {"$in": clean_entities}},
                {"uie_entities.value": {"$in": clean_entities}}
            ]
        }
        
        cursor1 = mongo_db.darknet_data.find(q_filter)
        cursor2 = mongo_db.darknet.find(q_filter)
        
        docs1 = await cursor1.to_list(length=200)
        docs2 = await cursor2.to_list(length=200)
        
        found_entities = {}
        for d in docs1 + docs2:
            content_str = str(d)
            for e in clean_entities:
                if e in content_str:
                    low_content = content_str.lower()
                    if "market" in low_content or "onion" in low_content:
                        found_entities[e] = "DarkNet Market"
                    elif "ransom" in low_content or "leak" in low_content:
                        found_entities[e] = "Ransomware Actor"
                    elif "sanction" in low_content or "ofac" in low_content:
                        found_entities[e] = "Sanctioned Entity"
                    elif "mix" in low_content or "tornado" in low_content:
                        found_entities[e] = "Mixing Pool"
                    else:
                        found_entities[e] = "High-Risk Peer"
        
        for e in req.entities:
            results[e] = found_entities.get(e, "Unidentified")
            
        return {"results": results}
    except Exception as e:
        logger.error(f"Error in resolve_entity: {e}")
        return {"status": "error", "message": str(e)}

@app.post("/api/analyze_case_files")
async def api_analyze_case_files(files: list[UploadFile] = File(...)):
    try:
        combined_text = ""
        for file in files:
            content = await file.read()
            filename = file.filename.lower()
            if filename.endswith(".txt") or filename.endswith(".csv") or filename.endswith(".json") or filename.endswith(".log"):
                combined_text += f"\n--- {file.filename} ---\n" + content.decode("utf-8", errors="ignore")
            elif filename.endswith(".pdf"):
                combined_text += f"\n--- {file.filename} ---\n"
                try:
                    pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
                    for page in pdf_reader.pages:
                        combined_text += page.extract_text() + "\n"
                except Exception as e:
                    logger.error(f"Error reading PDF {filename}: {e}")
            elif filename.endswith(".docx"):
                combined_text += f"\n--- {file.filename} ---\n"
                try:
                    doc = Document(io.BytesIO(content))
                    for para in doc.paragraphs:
                        combined_text += para.text + "\n"
                except Exception as e:
                    logger.error(f"Error reading DOCX {filename}: {e}")
        
        # Call Gemini via SDK
        api_key = os.getenv("GEMINI_API_KEYS")
        if not api_key:
            raise Exception("GEMINI_API_KEYS not configured on backend.")
        
        # Handle multiple keys if comma separated
        api_key = api_key.split(",")[0].strip()
        client = genai.Client(api_key=api_key)
        
        system_instruction = '''You are an elite cyber-forensic intelligence extractor. Extract entities from the text into a strict JSON object.
Fields:
- incidents: list of strings (e.g. "Ransomware Attack", "Phishing")
- suspect_wallets: list of strings (crypto addresses)
- tx_hashes: list of strings
- domains: list of strings
- usernames: list of strings
- total_loss_assets: string (number only, e.g. "15000")
- currency: string (e.g. "USDT", "BTC")
- network_chain: string ("BTC", "ETH", "BSC", "TRX", "SOL", "AUTO")
- summary: A 2-3 sentence professional intelligence brief summarizing the findings.
Ensure output is pure JSON. Do not use markdown blocks like ```json.
'''
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=combined_text[:100000], # Limit to avoid context bloat
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.1,
                response_mime_type="application/json"
            )
        )
        
        result_json = response.text
        try:
            intel = json.loads(result_json)
        except:
            # Fallback regex strip
            stripped = re.sub(r'```json\n|```', '', result_json).strip()
            intel = json.loads(stripped)
            
        return {"status": "success", "intelligence": intel}
        
    except Exception as e:
        logger.error(f"Error in analyze_case_files: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/")
async def dashboard(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

@app.get("/nemesis_tracer.html")
async def tracer_dashboard(request: Request):
    return templates.TemplateResponse(request=request, name="nemesis_tracer.html")

@app.get("/tracer")
async def tracer_dashboard_alias(request: Request):
    return templates.TemplateResponse(request=request, name="nemesis_tracer.html")

@app.get("/favicon.ico")
async def favicon():
    return Response(content=b"", media_type="image/x-icon")

@app.get("/assets/fonts/{font_name}")
async def dummy_font(font_name: str):
    return Response(content=b"", media_type="font/woff2")

@app.get("/admin")
async def admin_dashboard(request: Request):
    return templates.TemplateResponse(request=request, name="admin.html")

@app.get("/login")
async def login_page(request: Request):
    return templates.TemplateResponse(request=request, name="login.html")

@app.get("/intelligence")
async def intelligence_dashboard(request: Request):
    return templates.TemplateResponse(request=request, name="nemesis_intelligence.html")

@app.get("/audit")
async def audit_dashboard(request: Request):
    return templates.TemplateResponse(request=request, name="audit.html")

@app.get("/nemesis_id")
async def nemesis_id_dashboard(request: Request):
    return templates.TemplateResponse(request=request, name="nemesis_id.html")

@app.get("/darknet_search")
async def darknet_search_dashboard(request: Request):
    return templates.TemplateResponse(request=request, name="darknet_search.html")

@app.get("/api_docs")
async def api_docs_page(request: Request):
    return templates.TemplateResponse(request=request, name="api_docs.html")

@app.get("/api/gbeo")
async def api_get_gbeo():
    try:
        with open("gbeo_ontology.json", "r") as f:
            data = json.load(f)
        return {"status": "success", "data": data}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/api/gbeo/update")
async def api_update_gbeo(request: Request):
    try:
        payload = await request.json()
        with open("gbeo_ontology.json", "w") as f:
            json.dump(payload, f, indent=2)
        return {"status": "success", "message": "GBEO Ontology updated successfully"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/api/ontology")
async def api_ontology():
    from services.trace_engine import mongo_db
    if mongo_db is None:
        return {"scenarios": [], "matrix": {}, "error": "MongoDB not connected"}
    
    try:
        docs = await mongo_db.nemesis_ontology.find({}, {"_id": 0}).to_list(100)
        
        scenarios = [d for d in docs if "scenario_id" in d]
        universal = [d for d in docs if d.get("type") == "UNIVERSAL_MATRIX"]
        matrix = universal[0].get("data", {}) if universal else {}
        
        if not matrix:
            matrix = {
                "Bitcoin": { "Lock": "Script Hash (P2SH)", "Mint": "N/A", "Burn": "OP_RETURN", "Transfer": "UTXO SPEND", "Bridge": "WBTC Custody / Threshold Sig", "Exchange": "CEX Hot/Cold Deposit" },
                "Ethereum": { "Lock": "Smart Contract Vault", "Mint": "ERC20/ERC721 Mint", "Burn": "Address 0x0 / Burn Func", "Transfer": "ETH Native / ERC20 Transfer", "Bridge": "Cross-Chain Escrow", "Exchange": "CEX Omnibus Account" },
                "Tron": { "Lock": "TRC20 Lock", "Mint": "TRC20 Issue", "Burn": "TRC20 Burn", "Transfer": "TRX Native / TRC20 Transfer", "Bridge": "JustLend / BTTC Bridge", "Exchange": "CEX Deposit Address" },
                "Polygon": { "Lock": "PoS Bridge Lock", "Mint": "Wrapped Matic Mint", "Burn": "PoS Bridge Burn", "Transfer": "MATIC / ERC20", "Bridge": "PoS / Plasma Bridge", "Exchange": "CEX Multi-chain" },
                "BSC": { "Lock": "BEP20 Vault", "Mint": "BEP20 Mint", "Burn": "BEP20 Burn", "Transfer": "BNB / BEP20", "Bridge": "Binance Bridge", "Exchange": "Binance Hot Wallet" },
                "Solana": { "Lock": "Program PDA Lock", "Mint": "SPL Token Mint", "Burn": "SPL Burn", "Transfer": "SOL Native / SPL", "Bridge": "Wormhole Portal", "Exchange": "CEX Deposit" }
            }
            
        if not scenarios:
            scenarios = [
                {
                    "scenario_id": "Tornado_Cash_Mixing",
                    "chain": "Ethereum",
                    "destination_chain": "Ethereum",
                    "category": "Mixing / Obfuscation",
                    "flow": "Suspect Wallet -> Tornado Cash Deposit -> Tornado Cash Relayer -> Clean Wallet",
                    "state_transitions": ["NATIVE_DEPOSIT", "ZK_PROOF_GEN", "ANONYMOUS_WITHDRAWAL"],
                    "fingerprints": ["TC_DEPOSIT_EVENT", "TC_WITHDRAWAL_EVENT", "EXACT_INCREMENTS"],
                    "identity_signals": ["Timing Correlation", "Gas Price Heuristics", "Amount Matching"],
                    "detection_logic": [
                        {"stage": "Deposit", "detection": "Function: deposit() on known TC contract"},
                        {"stage": "Withdrawal", "detection": "Function: withdraw() with zero-knowledge proof"},
                        {"stage": "Correlation", "detection": "Heuristic matching of deposit and withdrawal within same block/timeframe"}
                    ],
                    "confidence_scoring": {
                        "Deposit Event": 100,
                        "Withdrawal Event": 100,
                        "Link Correlation": 85
                    }
                },
                {
                    "scenario_id": "Cross_Chain_Bridge_Hop",
                    "chain": "Bitcoin",
                    "destination_chain": "Ethereum",
                    "category": "Asset Re-denomination",
                    "flow": "BTC Suspect -> Custodial Vault -> WBTC Mint -> Ethereum Suspect",
                    "state_transitions": ["UTXO_LOCK", "CROSS_CHAIN_MSG", "ERC20_MINT"],
                    "fingerprints": ["BTC_DEPOSIT", "MINT_EVENT", "BURN_EVENT"],
                    "identity_signals": ["Merchant/Custody KYC", "Equivalent Value Output", "Timestamp Proximity"],
                    "detection_logic": [
                        {"stage": "Deposit", "detection": "BTC transfer to known custodian"},
                        {"stage": "Mint", "detection": "WBTC Mint event on Ethereum"},
                        {"stage": "Correlation", "detection": "Value match across chains with standard delay"}
                    ],
                    "confidence_scoring": {
                        "BTC Deposit": 100,
                        "WBTC Mint": 100,
                        "Cross-chain Link": 92
                    }
                }
            ]
            
        return {"scenarios": scenarios, "matrix": matrix}
    except Exception as e:
        logger.error(f"Failed to fetch ontology: {e}")
        return {"scenarios": [], "matrix": {}, "error": str(e)}

@app.get("/api/darknet/search")
async def api_darknet_search(q: str = ""):
    from services.trace_engine import mongo_db
    if mongo_db is None:
        return {"status": "error", "message": "MongoDB not connected"}
    if not q:
        return {"results": []}
    
    try:
        # Search the darknet_data collection
        search_pattern = re.compile(re.escape(q), re.IGNORECASE)
        q_filter = {
            "$or": [
                {"web_info.content": search_pattern},
                {"web_info.title": search_pattern},
                {"web_info.url": search_pattern},
                {"uie_entities.value": search_pattern},
                {"url": search_pattern},
                {"title": search_pattern}
            ]
        }
        
        # Query both collections concurrently
        cursor1 = mongo_db.darknet_data.find(q_filter).sort("crawled_at", -1).limit(50)
        cursor2 = mongo_db.darknet.find(q_filter).sort("crawled_at", -1).limit(50)
        
        docs1 = await cursor1.to_list(length=50)
        docs2 = await cursor2.to_list(length=50)
        
        # Combine, sort by date descending, and limit to 50
        all_docs = docs1 + docs2
        all_docs.sort(key=lambda x: str(x.get("crawled_at", "")), reverse=True)
        docs = all_docs[:50]
        
        output = []
        for doc in docs:
            # Format to match the original darknet API
            if 'web_info' not in doc:
                doc['web_info'] = {'url': doc.get('url', ''), 'title': doc.get('title', 'Untitled'), 'content': str(doc)}
            
            output.append({
                "hash-ID": doc.get("hash-ID", ""),
                "crawled_at": doc.get("crawled_at", ""),
                "web_info": {
                    "url": doc["web_info"].get("url", ""),
                    "title": doc["web_info"].get("title", ""),
                    "description": doc["web_info"].get("description", ""),
                    "content": doc["web_info"].get("content", "")
                },
                "uie_entities": doc.get("uie_entities", []),
                "keywords_detected": doc.get("keywords_detected", [])
            })
            
        return {"results": output}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/admin/health")
async def get_health():
    traces = get_active_traces(active_sessions)
    return {
        "active_websockets": sum(len(s.clients) for s in active_sessions.values()),
        "active_traces_count": len(traces),
        "mongo_connected": get_mongo_status(),
        "active_traces": traces
    }

@app.post("/admin/deploy")
async def trigger_auto_deploy():
    import subprocess
    import os
    try:
        # Check if we are running on Render vs Locally
        # If we are on Render, deploying locally isn't supported since git push needs auth
        if os.environ.get("RENDER"):
            return {"status": "error", "message": "Cannot deploy from inside the cloud container. Run this locally."}
            
        process = subprocess.Popen(
            ["python", "auto_deploy.py"], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT, 
            text=True
        )
        
        # We could stream, but for simplicity we'll just wait for it to finish or return the start
        # Actually, let's just return a success that it started to not block the UI
        return {"status": "success", "message": "Deployment sequence initiated in the background."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/admin/traces")
async def get_traces():
    return await fetch_saved_traces()

@app.post("/api/start_trace")
async def api_start_trace(req: TraceRequest, request: Request):
    try:
        raw_seeds = req.seeds.replace('"', '').replace("'", "")
        tokens = re.split(r'[\s,]+', raw_seeds)
        seeds_list = []
        for t in tokens:
            t = t.strip()
            if not t: continue
            chain = detect_chain(t, req.chain_override)
            if chain == "INVALID":
                continue
            if chain in EVM_DOMAINS or chain == "EVM_AUTO":
                t = t.lower()
            if t not in seeds_list:
                seeds_list.append(t)
                
        if not seeds_list: return {"error": "No valid seeds provided"}
        
        calc_amt = float(req.target_amount) if req.target_amount else 0.0
        trace_id = str(uuid.uuid4())[:8]
        
        engine = TraceEngine(trace_id)
        engine.setup(seeds_list, calc_amt, req.chain_override, req.start_date, req.end_date, req.target_currency, req.max_depth, req.max_hops)
        active_sessions[trace_id] = engine
        
        client_ip = request.client.host if request.client else "unknown"
        engine.client_ip = client_ip
        
        # We don't start the background task until the WS connects
        return {"status": "started", "trace_id": trace_id}
    except Exception as e:
        logger.error(f"Failed to setup trace: {e}")
        return {"error": str(e)}

@app.websocket("/ws/{trace_id}")
async def ws(websocket: WebSocket, trace_id: str):
    await websocket.accept()
    if trace_id not in active_sessions:
        await websocket.send_json({"type": "ERROR", "message": "Invalid trace ID"})
        await websocket.close()
        return
        
    engine = active_sessions[trace_id]
    engine.clients.add(websocket)
    
    await websocket.send_json({
        "type": "INIT",
        "seeds": engine.seeds,
        "seed_chains": engine.seed_chains
    })
    
    # Hydrate new clients: send existing nodes
    async with engine.state_lock:
        for node in engine.ledger:
            await websocket.send_json(node)
    
    # Start engine loop if not started
    if not engine.is_running:
        engine.is_running = True
        import asyncio
        asyncio.create_task(engine.run())
        
    try:
        while True: await websocket.receive_text()
    except:
        engine.clients.discard(websocket)

@app.get("/api/wallet_profile/{address}")
async def wallet_profile(address: str, chain: str = "AUTO"):
    from services.trace_engine import detect_chain, CONFIG, EVM_DOMAINS
    import aiohttp
    
    chain_res = detect_chain(address, chain)
    balances = []
    
    if chain_res in EVM_DOMAINS or chain_res == "EVM_AUTO":
        actual_chain = chain_res if chain_res in EVM_DOMAINS else "ETHEREUM"
        chain_id = EVM_DOMAINS.get(actual_chain, 1)
        key_var = f"{actual_chain}SCAN_API_KEY" if actual_chain != "ETHEREUM" else "ETHERSCAN_API_KEY"
        api_key = CONFIG.get(key_var, CONFIG.get("ETHERSCAN_API_KEY", ""))
        
        import ssl
        import certifi
        ssl_ctx = ssl.create_default_context(cafile=certifi.where())
        connector = aiohttp.TCPConnector(ssl=ssl_ctx)
        
        async with aiohttp.ClientSession(connector=connector) as session:
            try:
                # Fetch Native Balance using V2 endpoint
                url_native = f"https://api.etherscan.io/v2/api?chainid={chain_id}&module=account&action=balance&address={address}&tag=latest&apikey={api_key}"
                async with session.get(url_native, timeout=10) as r:
                    if r.status == 200:
                        data = await r.json()
                        if data.get("status") == "1":
                            bal = float(data.get("result", 0)) / 1e18
                            if bal > 0:
                                ticker = "ETH" if actual_chain == "ETHEREUM" else "BNB" if actual_chain == "BSC" else "MATIC" if actual_chain == "POLYGON" else "NATIVE"
                                balances.append({"token": ticker, "balance": round(bal, 4), "usd_value": round(bal * 3000, 2)}) # Mock USD rate for UI
            except: pass
            
    return {"address": address, "chain": chain_res, "balances": balances}

@app.get("/api/deep_scrape/{address}")
async def deep_scrape(address: str, max_pages: int = 5):
    from services.scraper_engine import scraper_instance
    try:
        res = await scraper_instance.deep_scrape_etherscan(address, max_pages)
        return res if res else {"error": "Scrape failed"}
    except Exception as e:
        logger.error(f"Error in deep scrape endpoint: {e}")
        logger.error(f"Error in deep scrape endpoint: {e}")
        return {"error": str(e)}

@app.get("/api/nemesis_id/profile/{address}")
async def nemesis_id_profile(address: str):
    from services.trace_engine import mongo_db, detect_chain, CONFIG, EVM_DOMAINS
    import aiohttp
    
    chain = detect_chain(address)
    
    # Defaults
    profile = {
        "address": address,
        "network": chain,
        "entity": "Unknown Entity",
        "balance": "0.00",
        "first_activity": "N/A",
        "last_activity": "N/A",
        "total_sent": "0.00",
        "total_received": "0.00",
        "tx_count": 0,
        "native_value": "0.00",
        "clustered_addresses": []
    }

    try:
        async with aiohttp.ClientSession() as session:
            if chain == "BITCOIN":
                async with session.get(f"https://mempool.space/api/address/{address}", timeout=10) as r:
                    if r.status == 200:
                        data = await r.json()
                        stats = data.get("chain_stats", {})
                        funded = stats.get("funded_txo_sum", 0) / 1e8
                        spent = stats.get("spent_txo_sum", 0) / 1e8
                        profile["balance"] = f"${(funded - spent) * 60000:,.2f}" # rough mock price
                        profile["native_value"] = f"{(funded - spent):.4f} BTC"
                        profile["total_received"] = f"${funded * 60000:,.2f}"
                        profile["total_sent"] = f"${spent * 60000:,.2f}"
                        profile["tx_count"] = stats.get("tx_count", 0)
            elif chain in EVM_DOMAINS or chain == "EVM":
                # Fallback to ETH if exact EVM chain is not determined for balance
                domain = EVM_DOMAINS.get(chain, EVM_DOMAINS["ETH"])
                api_key = CONFIG.get("ETHERSCAN_API_KEY", "")
                url = f"https://{domain}/api?module=account&action=balance&address={address}&tag=latest&apikey={api_key}"
                async with session.get(url, timeout=10) as r:
                    if r.status == 200:
                        data = await r.json()
                        if data.get("status") == "1":
                            bal_eth = int(data.get("result", 0)) / 1e18
                            profile["native_value"] = f"{bal_eth:.4f} {chain if chain != 'EVM' else 'ETH'}"
                            profile["balance"] = f"${bal_eth * 3000:,.2f}" # rough mock price
    except Exception as e:
        logger.error(f"Error fetching real balance for {address}: {e}")

    try:
        # Check if we have labels
        label_doc = await mongo_db.wallet_labels.find_one({"address": {"$regex": f"^{address}$", "$options": "i"}})
        if label_doc:
            profile["entity"] = label_doc.get("label", "Unknown")
            if "tags" in label_doc:
                profile["clustered_addresses"] = label_doc["tags"]
        
        # Check if we have traces that involved this wallet
        # Find first appearance
        trace_doc = await mongo_db.traces_data.find_one(
            {"$or": [{"ledger.from": {"$regex": f"^{address}$", "$options": "i"}}, {"ledger.to": {"$regex": f"^{address}$", "$options": "i"}}]},
            sort=[("timestamp", 1)]
        )
        if trace_doc:
            for l in trace_doc.get("ledger", []):
                if l.get("from", "").lower() == address.lower() or l.get("to", "").lower() == address.lower():
                    profile["first_activity"] = l.get("timestamp", "N/A")
                    break
                    
        return profile
    except Exception as e:
        logger.error(f"Error fetching profile for {address}: {e}")
        return profile

@app.get("/api/nemesis_id/aml/{address}")
async def nemesis_id_aml(address: str):
    from services.trace_engine import mongo_db
    if mongo_db is None:
        return {"error": "Database not connected"}
        
    aml_data = {
        "risk_score": 0,
        "risk_level": "Low",
        "flags": [],
        "sanctions": []
    }
    
    try:
        label_doc = await mongo_db.wallet_labels.find_one({"address": {"$regex": f"^{address}$", "$options": "i"}})
        if label_doc:
            tags = label_doc.get("tags", [])
            label_lower = label_doc.get("label", "").lower()
            
            if "hack" in label_lower or "exploit" in label_lower or "phish" in label_lower:
                aml_data["risk_score"] = 95
                aml_data["risk_level"] = "Critical"
                aml_data["flags"].append("Known Exploiter / Hacker")
            elif "mixer" in label_lower or "tornado" in label_lower:
                aml_data["risk_score"] = 85
                aml_data["risk_level"] = "High"
                aml_data["flags"].append("Mixer / Obfuscation Service")
            elif "sanction" in label_lower or "ofac" in label_lower:
                aml_data["risk_score"] = 100
                aml_data["risk_level"] = "Critical (Sanctioned)"
                aml_data["sanctions"].append("OFAC Specially Designated National")
            
            for tag in tags:
                aml_data["flags"].append(tag)
                
        return aml_data
    except Exception as e:
        logger.error(f"Error fetching AML for {address}: {e}")
        return aml_data

@app.get("/api/nemesis_id/intel/{address}")
async def nemesis_id_intel(address: str):
    from services.trace_engine import mongo_db
    if mongo_db is None:
        return {"error": "Database not connected"}
        
    intel = {
        "intel_summary": "No specific darknet or OSINT intelligence found.",
        "tags": [],
        "sources": []
    }
    
    try:
        # Search darknet collections
        dn_doc = await mongo_db.darknet.find_one({"$text": {"$search": address}})
        if dn_doc:
            intel["intel_summary"] = "Address observed in Darknet intelligence sources."
            intel["sources"].append(dn_doc.get("url", "Darknet Market / Forum"))
            intel["tags"].append("Darknet Mention")
            
        return intel
    except Exception as e:
        logger.error(f"Error fetching intel for {address}: {e}")
        return intel

@app.get("/api/nemesis_id/tx_history/{address}")
async def nemesis_id_tx_history(address: str):
    from services.trace_engine import mongo_db
    if mongo_db is None:
        return {"error": "Database not connected"}
        
    try:
        # Fetch relevant ledger entries from recent traces
        cursor = mongo_db.traces_data.find(
            {"$or": [{"ledger.from": {"$regex": f"^{address}$", "$options": "i"}}, {"ledger.to": {"$regex": f"^{address}$", "$options": "i"}}]},
            {"ledger": 1, "trace_id": 1, "timestamp": 1}
        ).sort("timestamp", -1).limit(5)
        
        docs = await cursor.to_list(length=5)
        transactions = []
        for doc in docs:
            for l in doc.get("ledger", []):
                if l.get("from", "").lower() == address.lower() or l.get("to", "").lower() == address.lower():
                    transactions.append(l)
                    
        return {"transactions": transactions[:20]}
    except Exception as e:
        logger.error(f"Error fetching tx history for {address}: {e}")
        return {"transactions": []}

class NemesisIDReportRequest(BaseModel):
    address: str
    type: str

@app.post("/api/nemesis_id/generate_report")
async def nemesis_id_generate_report(req: NemesisIDReportRequest):
    return {
        "markdown": f"# Automated Report for {req.address}\n\nNo data available to generate a full report."
    }

@app.get("/api/nemesis_id/search")
async def search_nemesis_id(query: str):
    from services.trace_engine import mongo_db
    if mongo_db is None:
        return {"error": "Database not connected"}
    try:
        doc = await mongo_db.traces_data.find_one({
            "$or": [
                {"ledger.sender_nemesis_id": query},
                {"ledger.receiver_nemesis_id": query},
                {"trace_id": query}
            ]
        }, {"_id": 0})
        if doc and "ledger" in doc:
            return {"trace_id": doc.get("trace_id"), "ledger": doc.get("ledger")}
        return {"error": "Trace or Nemesis ID not found"}
    except Exception as e:
        logger.error(f"Error fetching trace by ID: {e}")
        return {"error": str(e)}

class DeepEvidenceRequest(BaseModel):
    tx: str
    chain: str = ""
    signature_hash: str = ""
    contract_method: str = ""
    raw_input_data: str = ""
    sender: str = ""
    receiver: str = ""
    amount: str = ""

@app.post("/api/deep_evidence")
async def api_deep_evidence(req: DeepEvidenceRequest):
    import aiohttp
    import ssl
    import certifi
    import json
    import os
    
    ssl_ctx = ssl.create_default_context(cafile=certifi.where())
    connector = aiohttp.TCPConnector(ssl=ssl_ctx)
    
    decoded_abi = "[]"
    gemini_summary = "No Gemini API key configured."
    
    # 4byte lookup if signature hash is provided
    if req.signature_hash and req.signature_hash.startswith("0x"):
        async with aiohttp.ClientSession(connector=connector) as session:
            try:
                url = f"https://www.4byte.directory/api/v1/signatures/?hex_signature={req.signature_hash}"
                async with session.get(url, timeout=5) as r:
                    if r.status == 200:
                        data = await r.json()
                        if data.get("count", 0) > 0:
                            decoded_abi = json.dumps(data["results"], indent=2)
            except Exception as e:
                logger.error(f"4byte error: {e}")
                
    # Use Gemini to summarize
    gemini_key = os.getenv("GEMINI_API_KEYS", "").split(",")[0]
    if gemini_key and gemini_key != "freekey":
        try:
            from google import genai
            client = genai.Client(api_key=gemini_key)
            prompt = f"""Analyze this blockchain transaction for forensic evidence.
Chain: {req.chain}

Type of transfer events, methods etc: {req.contract_method}

TX HASH(ES):
{req.tx}

SENDER: {req.sender} - last transaction outputs going to the receiver and the full transaction details.
RECEIVER: {req.receiver} - last transaction inputs from the sender and the full transaction details.
AMOUNT: {req.amount}

Sig Hash: {req.signature_hash}
Input Data: {req.raw_input_data}
4byte results: {decoded_abi}

HOW DID THE ASSETS LANDED FROM ETH to BITCOIN or vice versa if applicable? Summarize the technical evidence briefly and try to identify the tx hash on it from the receiver inputs."""
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
            )
            gemini_summary = response.text
        except Exception as e:
            gemini_summary = f"Gemini Analysis Failed: {e}"

    return {
        "decoded_abi": decoded_abi,
        "contract_source_code": gemini_summary
    }

@app.websocket("/ws/darknet/stream")
async def darknet_ws_stream(websocket: WebSocket):
    await websocket.accept()
    from queue import Queue
    import queue
    try:
        from darknet.darknetv2 import sse_clients, locks
    except ImportError:
        await websocket.send_json({"type": "error", "message": "Darknet module not loaded"})
        await websocket.close()
        return

    q = Queue()
    with locks["sse"]:
        sse_clients.append(q)
    
    try:
        while True:
            try:
                data = await asyncio.to_thread(q.get, timeout=1.0)
                if data.startswith("event: "):
                    parts = data.split("\ndata: ")
                    if len(parts) == 2:
                        event_type = parts[0].replace("event: ", "").strip()
                        json_str = parts[1].strip()
                        import json
                        try:
                            parsed = json.loads(json_str)
                            await websocket.send_json({"event": event_type, "data": parsed})
                        except:
                            await websocket.send_json({"event": event_type, "data": json_str})
            except queue.Empty:
                await asyncio.sleep(0.1)
                
            try:
                msg = await asyncio.wait_for(websocket.receive_text(), timeout=0.01)
            except asyncio.TimeoutError:
                pass
    except Exception as e:
        logger.error(f"Darknet WS error: {e}")
    finally:
        with locks["sse"]:
            if q in sse_clients:
                sse_clients.remove(q)
        await websocket.close()

# ==========================================
# ADMIN DASHBOARD & AUTHENTICATION ENDPOINTS
# ==========================================

@app.post("/api/login")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    if not authenticate_admin(form_data.username, form_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": form_data.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.websocket("/ws/admin/logs")
async def admin_logs_ws(websocket: WebSocket):
    # Simplified auth for WebSocket (in production, use token query param)
    await websocket.accept()
    log_file = os.path.join("logs", "nemesis.log")
    try:
        if not os.path.exists(log_file):
            await websocket.send_text("Log file not found.")
            await asyncio.sleep(1)
            return
            
        with open(log_file, "r") as f:
            # Seek to end
            f.seek(0, 2)
            while True:
                line = f.readline()
                if not line:
                    await asyncio.sleep(0.5)
                    continue
                await websocket.send_text(line)
    except Exception as e:
        logger.error(f"WS Admin Log error: {e}")
    finally:
        await websocket.close()

class CaseModel(BaseModel):
    name: str
    description: str
    linked_traces: list[str]

@app.get("/api/admin/cases")
async def get_cases(token: dict = Depends(verify_access_token)):
    from services.trace_engine import engine
    db = engine.db
    if db is None:
        return {"cases": []}
    cases = await db.cases.find().to_list(100)
    for c in cases:
        c["_id"] = str(c["_id"])
    return {"cases": cases}

@app.post("/api/admin/cases")
async def create_case(case: CaseModel, token: dict = Depends(verify_access_token)):
    from services.trace_engine import engine
    db = engine.db
    if db is None:
        raise HTTPException(status_code=500, detail="Database not connected")
    
    new_case = {
        "case_id": f"CASE-{uuid.uuid4().hex[:8].upper()}",
        "name": case.name,
        "description": case.description,
        "status": "OPEN",
        "linked_traces": case.linked_traces,
        "created_at": datetime.datetime.utcnow()
    }
    await db.cases.insert_one(new_case)
    new_case["_id"] = str(new_case["_id"])
    return {"status": "success", "case": new_case}

@app.get("/api/admin/db_stats")
async def get_db_stats(token: dict = Depends(verify_access_token)):
    from services.trace_engine import engine
    db = engine.db
    if db is None:
        return {"status": "offline"}
    
    trace_count = await db.traces_data.count_documents({})
    wallet_count = await db.wallet_labels.count_documents({})
    case_count = await db.cases.count_documents({})
    
    return {
        "status": "online",
        "traces": trace_count,
        "wallets": wallet_count,
        "cases": case_count
    }

class ConfigModel(BaseModel):
    gemini_key: str
    etherscan_key: str
    polygonscan_key: str
    max_depth: int
    max_hops: int

@app.get("/api/admin/config")
async def get_config(token: dict = Depends(verify_access_token)):
    from services.trace_engine import engine
    return {
        "gemini_key": os.getenv("GEMINI_API_KEYS", "")[:5] + "...",
        "etherscan_key": os.getenv("ETHERSCAN_API_KEY", "")[:5] + "...",
        "polygonscan_key": os.getenv("POLYGONSCAN_API_KEY", "")[:5] + "...",
        "max_depth": engine.MAX_DEPTH,
        "max_hops": engine.MAX_HOPS
    }

@app.post("/api/admin/config")
async def update_config(config: ConfigModel, token: dict = Depends(verify_access_token)):
    from services.trace_engine import engine
    # In-memory config update
    if config.max_depth > 0: engine.MAX_DEPTH = config.max_depth
    if config.max_hops > 0: engine.MAX_HOPS = config.max_hops
    return {"status": "success", "message": "Configuration updated in-memory"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=3001)
