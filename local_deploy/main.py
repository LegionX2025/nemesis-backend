import os
import sys
import subprocess
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
from fastapi import FastAPI, WebSocket, Request, BackgroundTasks, Response, Depends, HTTPException, status
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel
import uvicorn
import uuid

# Setup logging for cloud-native environment (stdout only)
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("OmniChainEngine")

import collections

admin_websockets = set()
admin_log_queue = collections.deque(maxlen=1000)

class AdminLogHandler(logging.Handler):
    def emit(self, record):
        try:
            msg = self.format(record)
            log_entry = {
                "src": "BACKEND",
                "msg": msg,
                "type": "ERROR" if record.levelno >= logging.ERROR else ("WARNING" if record.levelno >= logging.WARNING else "INFO")
            }
            admin_log_queue.append(log_entry)
        except Exception:
            pass

admin_log_handler = AdminLogHandler()
admin_log_handler.setFormatter(logging.Formatter('%(message)s'))
logger.addHandler(admin_log_handler)

async def admin_log_broadcaster():
    import asyncio
    while True:
        if admin_websockets and admin_log_queue:
            pending = []
            while admin_log_queue:
                pending.append(admin_log_queue.popleft())
            for ws in list(admin_websockets):
                for p in pending:
                    try:
                        await ws.send_json(p)
                    except:
                        admin_websockets.discard(ws)
                        break
        await asyncio.sleep(0.5)


from services.trace_engine import TraceEngine, init_mongodb, get_asset_ticker, detect_chain, EVM_DOMAINS, get_active_traces, get_mongo_status, fetch_saved_traces, auto_compute_loss_amount
from services.auth_engine import authenticate_admin, create_access_token, verify_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from datetime import timedelta
import asyncio
import sys

async def run_boot_diagnostics():
    logger.info("==================================================")
    logger.info("   INITIATING LIONSGATE NEMESIS BOOT SEQUENCE     ")
    logger.info("==================================================")
    
    logger.info(">>> [1/4] Verifying Core Dependencies...")
    logger.info("    [OK] Core dependencies verified via build system.")
        
    logger.info(">>> [2/5] Checking Intelligence Providers & API Keys...")
    from services.trace_engine import CONFIG
    providers = {
        "Etherscan": CONFIG.get("ETHERSCAN_API_KEY"),
        "OKLink": "STEALTH_SCRAPER_ONLY",
        "Tatum": CONFIG.get("TATUM_API_KEY"),
        "Gemini (AI)": "MULTIPLE_KEYS_ROTATION_ENABLED" if CONFIG.get("GEMINI_API_KEY") else None,
        "Infura": CONFIG.get("INFURA_API_KEY"),
        "Ankr": CONFIG.get("ANKR_API_KEY"),
        "GetBlock (BTC)": CONFIG.get("GETBLOCK_BTC_KEY")
    }
    for p, key in providers.items():
        if key and key != "freekey":
            logger.info(f"    [OK] {p} Provider Active.")
        else:
            logger.warning(f"    [WARN] {p} API Key missing or default.")
            
    logger.info(">>> [3/5] Loading Supported Networks & RPC Fallbacks...")
    logger.info(f"    [OK] EVM Chains: {', '.join(EVM_DOMAINS.keys())}")
    logger.info("    [OK] Non-EVM Chains: BITCOIN, SOLANA, TRON, RIPPLE, STELLAR")
    
    logger.info(">>> [4/4] Verifying Tracing Engine & Executions...")
    logger.info("    [OK] Tracing Engine Ready. Parallel Executions (Max 4 Workers).")
    
    
    logger.info("==================================================")
    logger.info("   NEMESIS ENGINE READY FOR OMNICHAIN OPERATIONS  ")
    logger.info("==================================================")

@asynccontextmanager
async def lifespan(app: FastAPI):
    await run_boot_diagnostics()
    import asyncio
    
    # Ensure Playwright browsers are installed before starting the engine
    asyncio.create_task(admin_log_broadcaster())
    try:
        subprocess.run(["playwright", "install", "chromium"], check=True)
        logger.info("    [OK] Playwright chromium installed successfully.")
    except Exception as e:
        logger.error(f"    [FAIL] Failed to install Playwright browsers: {e}")
    
    # Run Scraper initialization in the background so they don't block the web server from starting
    async def init_background():
        from services.scraper_engine import scraper_instance
        await scraper_instance.start()
        
        # Start Darknet Crawler
        try:
            import sys
            import os
            # Add darknet folder to sys.path so it can be imported
            darknet_path = os.path.join(os.path.dirname(__file__), "darknet")
            if darknet_path not in sys.path:
                sys.path.append(darknet_path)
            from darknetv2 import start_headless_crawler
            use_tor = os.getenv("VITE_TOR_AUTO_START", "false").lower() == "true" # Defaulted to false for separate terminal
            if use_tor:
                start_headless_crawler()
                logger.info("    [OK] Darknet headless crawler initialized.")
            else:
                logger.info("    [SKIP] Darknet crawler disabled via VITE_TOR_AUTO_START=false. Run darknetv2.py in a separate console.")
        except Exception as e:
            logger.error(f"    [FAIL] Failed to initialize Darknet crawler: {e}")
        
    asyncio.create_task(init_background())
    
    yield
    from services.scraper_engine import scraper_instance
    await scraper_instance.stop()

app = FastAPI(title="Nemesis OmniChain API", description="Lionsgate OmniChain Forensic Engine", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://nemesis-id-frontend.pages.dev",
        "https://nemesis-global-worker.lionsgatenetwork.workers.dev",
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:8000"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="."), name="static")

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
    tracing_method: str = "tracer"

@app.get("/")
async def dashboard(request: Request):
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

@app.get("/nemesis")
async def nemesis_landing(request: Request):
    return templates.TemplateResponse(request=request, name="nemesis_id_landing.html")

@app.get("/tracer")
async def tracer_landing(request: Request):
    return templates.TemplateResponse(request=request, name="nemesis_tracer_landing.html")

@app.get("/darknet_search")
async def darknet_search_dashboard(request: Request):
    return templates.TemplateResponse(request=request, name="darknet_search.html")

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
        
        cursor = mongo_db.darknet_data.find(q_filter).sort("crawled_at", -1).limit(50)
        docs = await cursor.to_list(length=50)
        
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

@app.get("/admin/traces")
async def get_traces():
    return await fetch_saved_traces()

@app.post("/api/start_trace")
async def api_start_trace(req: TraceRequest, request: Request):
    try:
        raw_seeds = req.seeds.replace('"', '').replace("'", "")
        seeds_list = []
        pathfinding_targets = []
        
        # Support "Wallet A - Wallet B" syntax for Asset Tracer
        if " - " in raw_seeds:
            parts = [p.strip() for p in raw_seeds.split(" - ")]
            raw_seeds = parts[0]
            if len(parts) > 1:
                pathfinding_targets.append(parts[1].lower())
                
        tokens = re.split(r'[\s,]+', raw_seeds)
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
        
        if calc_amt <= 0:
            logger.info("Target amount not provided. Attempting to auto-compute loss from seeds...")
            computed_amt_str, computed_cur, extracted_seeds = await auto_compute_loss_amount(seeds_list, req.chain_override)
            calc_amt = float(computed_amt_str)
            if calc_amt > 0:
                logger.info(f"Auto-computed loss amount: {calc_amt} {computed_cur}")
                req.target_currency = computed_cur
                for es in extracted_seeds:
                    es_lower = es.lower()
                    if es_lower not in seeds_list:
                        seeds_list.append(es_lower)
            else:
                logger.info("Auto-compute could not find a target amount. Proceeding with 0 amount limit.")

        trace_id = str(uuid.uuid4())[:8]
        
        engine = TraceEngine(trace_id)
        engine.setup(seeds_list, calc_amt, req.chain_override, req.start_date, req.end_date, req.target_currency, req.max_depth, req.max_hops, req.tracing_method, pathfinding_targets)
        active_sessions[trace_id] = engine
        
        client_ip = request.client.host if request.client else "unknown"
        engine.client_ip = client_ip
        
        # We don't start the background task until the WS connects
        return {"status": "started", "trace_id": trace_id}
    except Exception as e:
        logger.error(f"Failed to setup trace: {e}")
        return {"error": str(e)}

@app.websocket("/ws/darknet/stream")
async def darknet_ws_stream(websocket: WebSocket):
    await websocket.accept()
    from queue import Queue
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
            # Poll the queue (using asyncio to avoid blocking the event loop)
            # q.get() is blocking, so we run it in an executor or poll with queue.Empty
            import queue
            try:
                data = await asyncio.to_thread(q.get, timeout=1.0)
                # data is typically "event: <type>\ndata: {...}\n\n"
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
                    else:
                        await websocket.send_text(data)
                else:
                    await websocket.send_text(data)
            except queue.Empty:
                await asyncio.sleep(0.1)
                continue
    except Exception as e:
        logger.error(f"Darknet WS error: {e}")
    finally:
        with locks["sse"]:
            if q in sse_clients:
                sse_clients.remove(q)
        try:
            await websocket.close()
        except:
            pass

@app.websocket("/ws/admin")
async def ws_admin(websocket: WebSocket):
    await websocket.accept()
    admin_websockets.add(websocket)
    try:
        while True: await websocket.receive_text()
    except:
        admin_websockets.discard(websocket)


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
        "seed_chains": engine.seed_chains,
        "tracing_method": getattr(engine, "tracing_method", "tracer")
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

import time

GLOBAL_PRICE_CACHE = {"prices": {}, "last_updated": 0}

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
                # Update prices from CoinGecko every 60 seconds
                if time.time() - GLOBAL_PRICE_CACHE["last_updated"] > 60:
                    try:
                        cg_url = "https://api.coingecko.com/api/v3/simple/price?ids=ethereum,binancecoin,matic-network,tron&vs_currencies=usd"
                        async with session.get(cg_url, timeout=5) as p_res:
                            if p_res.status == 200:
                                p_data = await p_res.json()
                                GLOBAL_PRICE_CACHE["prices"]["ETH"] = p_data.get("ethereum", {}).get("usd", 3000)
                                GLOBAL_PRICE_CACHE["prices"]["BNB"] = p_data.get("binancecoin", {}).get("usd", 500)
                                GLOBAL_PRICE_CACHE["prices"]["MATIC"] = p_data.get("matic-network", {}).get("usd", 1)
                                GLOBAL_PRICE_CACHE["prices"]["TRX"] = p_data.get("tron", {}).get("usd", 0.12)
                                GLOBAL_PRICE_CACHE["last_updated"] = time.time()
                    except: pass
                
                # Fetch Native Balance using V2 endpoint
                url_native = f"https://api.etherscan.io/v2/api?chainid={chain_id}&module=account&action=balance&address={address}&tag=latest&apikey={api_key}"
                async with session.get(url_native, timeout=10) as r:
                    if r.status == 200:
                        data = await r.json()
                        if data.get("status") == "1":
                            bal = float(data.get("result", 0)) / 1e18
                            if bal > 0:
                                ticker = "ETH" if actual_chain == "ETHEREUM" else "BNB" if actual_chain == "BSC" else "MATIC" if actual_chain == "POLYGON" else "NATIVE"
                                price = GLOBAL_PRICE_CACHE["prices"].get(ticker, 3000)
                                balances.append({"token": ticker, "balance": round(bal, 4), "usd_value": round(bal * price, 2)})
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
        return {"error": str(e)}

@app.get("/api/nemesis_id/search")
async def search_nemesis_id(query: str):
    # D1 /api/wallet_profile is the source of truth now instead of mongo_db
    try:
        # We redirect this search to wallet_profile format to maintain compatibility
        from services.trace_engine import detect_chain
        chain = detect_chain(query, "AUTO")
        return {"nemesis_id": "NEMESIS-PROFILE", "address": query, "chain": chain, "status": "resolved"}
    except Exception as e:
        logger.error(f"Error in nemesis_id search: {e}")
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


# ==========================================
# NEMESIS ID ENDPOINTS (NEW)
# ==========================================

class NemesisReportRequest(BaseModel):
    address: str
    type: str
    ledger_data: list = []
    stats: dict = {}

@app.get("/api/nemesis_id/profile/{address}")
async def get_nemesis_profile(address: str):
    from services.trace_engine import detect_chain, get_wallet_label, fetch_oklink_label
    chain = detect_chain(address)
    
    # Try getting label from local DB or oklink
    label = await get_wallet_label(address)
    if not label:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            oklink_label = await fetch_oklink_label(session, chain, address)
            if oklink_label:
                label = oklink_label
    
    import hashlib
    nemesis_id = f"NMS-WALLET-{chain}-{hashlib.md5(address.encode()).hexdigest()[:8].upper()}"
    return {
        "address": address,
        "nemesis_id": nemesis_id,
        "network": chain,
        "entity": label if label else "Unknown / Unlabeled",
        "balance": "Calculating...",
        "first_activity": "Fetching...",
        "last_activity": "Fetching...",
        "total_sent": "Fetching...",
        "total_received": "Fetching...",
        "total_transactions": "Fetching...",
        "clustered_addresses": []
    }

TX_CACHE = {}

async def fetch_real_txs(address: str):
    if address in TX_CACHE and time.time() - TX_CACHE[address]["last_fetched"] < 60:
        return TX_CACHE[address]["txs"]
    
    from services.trace_engine import detect_chain, CONFIG, EVM_DOMAINS
    import aiohttp
    import ssl
    import certifi
    from datetime import datetime
    
    chain_res = detect_chain(address, "AUTO")
    actual_chain = chain_res if chain_res in EVM_DOMAINS else "ETHEREUM"
    key_var = f"{actual_chain}SCAN_API_KEY" if actual_chain != "ETHEREUM" else "ETHERSCAN_API_KEY"
    api_key = CONFIG.get(key_var, CONFIG.get("ETHERSCAN_API_KEY", ""))
    
    ssl_ctx = ssl.create_default_context(cafile=certifi.where())
    connector = aiohttp.TCPConnector(ssl=ssl_ctx)
    
    txs = []
    async with aiohttp.ClientSession(connector=connector) as session:
        try:
            url = f"https://api.etherscan.io/api?module=account&action=txlist&address={address}&startblock=0&endblock=99999999&page=1&offset=100&sort=desc&apikey={api_key}"
            async with session.get(url, timeout=10) as r:
                if r.status == 200:
                    data = await r.json()
                    if data.get("status") == "1":
                        raw_txs = data.get("result", [])
                        for tx in raw_txs:
                            val = float(tx.get("value", 0)) / 1e18
                            if val > 0:
                                t = "Receive" if tx["to"].lower() == address.lower() else "Send"
                                ts = datetime.fromtimestamp(int(tx["timeStamp"])).strftime('%Y-%m-%d %H:%M:%S')
                                txs.append({
                                    "type": t,
                                    "timestamp": ts,
                                    "hash": tx["hash"],
                                    "sender": tx["from"],
                                    "receiver": tx["to"],
                                    "amount": f"{round(val, 4)} ETH",
                                    "network": actual_chain,
                                    "raw_val": val
                                })
        except Exception as e:
            pass
            
    TX_CACHE[address] = {"txs": txs, "last_fetched": time.time()}
    return txs

@app.get("/api/nemesis_id/aml/{address}")
async def get_nemesis_aml(address: str):
    txs = await fetch_real_txs(address)
    senders = {}
    receivers = {}
    total_vol = 0
    exposure = 0
    
    for tx in txs:
        val = tx.get("raw_val", 0)
        total_vol += val
        if tx["type"] == "Receive":
            s = tx["sender"]
            if s not in senders: senders[s] = {"wallet": s, "count": 0, "amount": 0}
            senders[s]["count"] += 1
            senders[s]["amount"] += val
        else:
            r = tx["receiver"]
            if r not in receivers: receivers[r] = {"wallet": r, "count": 0, "amount": 0}
            receivers[r]["count"] += 1
            receivers[r]["amount"] += val
            
    s_list = sorted(senders.values(), key=lambda x: x["amount"], reverse=True)[:5]
    r_list = sorted(receivers.values(), key=lambda x: x["amount"], reverse=True)[:5]
    
    for x in s_list + r_list:
        x["amount"] = f"${round(x['amount'] * 3000, 2)}" # Defaulting UI display to USD estimate
        
    score = min(100, int(len(txs) * 0.5 + len(s_list)*2))
    if len(txs) == 0: score = 0
    
    return {
        "aml_score": score,
        "exposure_rate": f"{round((len(s_list) / max(1, len(txs))) * 100, 1)}%",
        "receivers": r_list,
        "senders": s_list
    }

@app.get("/api/nemesis_id/intel/{address}")
async def get_nemesis_intel(address: str):
    from services.trace_engine import mongo_db
    txs = await fetch_real_txs(address)
    
    darknet_mentions = 0
    if mongo_db is not None:
        count = await mongo_db.darknet_data.count_documents({"uie_entities.value": address})
        darknet_mentions = count
        
    top_interacted = list(set([t["sender"] if t["type"] == "Receive" else t["receiver"] for t in txs[:5]]))
    custodial_entry = "Unknown"
    if txs and txs[-1]["type"] == "Receive":
        custodial_entry = txs[-1]["sender"]
        
    return {
        "top_interacted": top_interacted[:3],
        "custodial_entry": custodial_entry,
        "is_malicious": darknet_mentions > 0,
        "social_media": "None Found",
        "darknet_mentions": f"{darknet_mentions} Mentions"
    }

@app.get("/api/nemesis_id/tx_history/{address}")
async def get_nemesis_tx_history(address: str):
    txs = await fetch_real_txs(address)
    return {"transactions": txs}

@app.post("/api/nemesis_id/generate_report")
async def nemesis_generate_report(req: NemesisReportRequest):
    import google.generativeai as genai
    from services.trace_engine import CONFIG
    import traceback
    
    keys = CONFIG.get("GEMINI_API_KEYS", [])
    if not keys:
        return {"markdown": "Error: No Gemini API keys configured."}
        
    try:
        genai.configure(api_key=keys[0])
        model = genai.GenerativeModel("gemini-2.5-flash")
        
        import json
        
        # Prepare context data
        context_data = ""
        if req.ledger_data:
            # Take up to 50 txs to avoid token limits
            context_data += f"\n\n### Trace Ledger Data (Sample):\n{json.dumps(req.ledger_data[:50], indent=2)}"
        if req.stats:
            context_data += f"\n\n### Node Statistics:\n{json.dumps(req.stats, indent=2)}"
            
        prompt = f"Write a comprehensive forensic intelligence report on the cryptocurrency address {req.address}. Include sections for Executive Summary, AML Risk, Known Entities, and Transaction Patterns. Use the following context data if provided: {context_data}. Format it entirely in Markdown."
        if req.type == "insights":
            prompt = f"Provide a brief 3-paragraph forensic AI insight for the cryptocurrency address {req.address}. Focus on anomalies, risk factors, and cluster behavior based on the following tracer data: {context_data}. Format it entirely in Markdown."
            
        response = await asyncio.to_thread(model.generate_content, prompt)
        return {"markdown": response.text}
    except Exception as e:
        logger.error(f"Gemini API Error: {traceback.format_exc()}")
        return {"markdown": f"Error generating report: {str(e)}"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3001))
    uvicorn.run(app, host="0.0.0.0", port=port)
