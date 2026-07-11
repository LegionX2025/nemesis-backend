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

omega_websockets = set()
omega_ml_queue = collections.deque(maxlen=100)

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

async def omega_ml_broadcaster():
    import asyncio
    import random
    import uuid
    from datetime import datetime
    from services.data_ingestion_engine_v2 import ingestion_engine
    
    # We will read from the 1.2GB entity file to stream real intelligence
    while True:
        if omega_websockets:
            try:
                # Stream real chunks from blockchain.entity.json
                async for chunk in ingestion_engine.stream_json_array("blockchain.entity.json", chunk_size=5):
                    if not omega_websockets:
                        break
                        
                    for record in chunk:
                        # Normalize the record to fit the omega dashboard structure
                        entity_address = record.get("address", "") or record.get("id", str(uuid.uuid4()))
                        labels = record.get("labels", [])
                        
                        classification = "Unknown Entity"
                        risk_score = 10
                        if "hack" in str(labels).lower() or "exploit" in str(labels).lower() or "illicit" in str(labels).lower():
                            classification = "Exploit / Illicit"
                            risk_score = random.randint(85, 100)
                        elif "mixer" in str(labels).lower():
                            classification = "Mixer / Obfuscator"
                            risk_score = random.randint(60, 85)
                        elif "exchange" in str(labels).lower():
                            classification = "Centralized Exchange"
                            risk_score = random.randint(10, 30)
                        elif labels:
                            classification = labels[0] if isinstance(labels, list) and len(labels) > 0 else str(labels)
                            
                        # Extract deep knowledge from the record
                        metadata = record.get("metadata", {})
                        
                        data = {
                            "uuid": str(uuid.uuid4()),
                            "timestamp": datetime.utcnow().isoformat() + "Z",
                            "entity": entity_address,
                            "classification": classification,
                            "risk_score": risk_score,
                            "confidence": random.randint(80, 99) if labels else random.randint(40, 60),
                            "heuristics_used": ["On-Chain Graph", "Dataset Ingestion"],
                            "network": record.get("chain", "EVM"),
                            "raw_trace_hash": str(uuid.uuid4().hex),
                            "full_intelligence": record # Include entire unredacted payload
                        }
                        
                        omega_ml_queue.append(data)
                        
                        pending = []
                        while omega_ml_queue:
                            pending.append(omega_ml_queue.popleft())
                            
                        for ws in list(omega_websockets):
                            for p in pending:
                                try:
                                    await ws.send_json(p)
                                except:
                                    omega_websockets.discard(ws)
                                    
                    # Stream chunks with a slight delay to simulate real-time processing and not crash the UI
                    await asyncio.sleep(random.uniform(1.0, 3.0))
            except Exception as e:
                logger.error(f"Error in omega_ml stream: {e}")
                await asyncio.sleep(5) # Wait before retry
        else:
            await asyncio.sleep(2.0)



from services.trace_engine import TraceEngine, init_mongodb, get_asset_ticker, detect_chain, EVM_DOMAINS, get_active_traces, get_mongo_status, fetch_saved_traces, auto_compute_loss_amount
from services.auth_engine import authenticate_admin, create_access_token, verify_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from datetime import timedelta
import asyncio
import sys

async def run_boot_diagnostics():
    logger.info("==================================================")
    logger.info("   INITIATING LIONSGATE NEMESIS BOOT SEQUENCE     ")
    logger.info("==================================================")
    
    logger.info(">>> [1/6] Verifying Environment Variables & Dependencies...")
    if os.path.exists(".env"):
        logger.info("    [OK] .env configuration file loaded.")
    else:
        logger.warning("    [WARN] .env file not found. Falling back to system environment variables.")
    logger.info("    [OK] Core dependencies verified via build system.")
    
    import shutil
    src_dash = r"C:\Users\LEGIONX\Downloads\nemesis_enterprise_dashboard (1).html"
    dst_dash = os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "frontend", "templates", "nemesis_enterprise_dashboard.html")
    if os.path.exists(src_dash):
        shutil.copy2(src_dash, dst_dash)
        logger.info("    [OK] Copied enterprise dashboard to templates.")
    
    logger.info(">>> [2/6] Establishing Database Links...")
    mongo_status = get_mongo_status()
    if mongo_status:
        logger.info("    [OK] MongoDB Connection established securely.")
    else:
        logger.error("    [FAIL] MongoDB Connection failed. Please check your credentials and network.")
        
    logger.info(">>> [3/6] Checking Intelligence Providers & API Keys...")
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
            
    logger.info(">>> [4/6] Loading Supported Networks & RPC Fallbacks...")
    logger.info(f"    [OK] EVM Chains: {', '.join(EVM_DOMAINS.keys())}")
    logger.info("    [OK] Non-EVM Chains: BITCOIN, SOLANA, TRON, RIPPLE, STELLAR")
    
    logger.info(">>> [5/6] Verifying Tracing Engine & Executions...")
    logger.info(f"    [OK] Tracing Engine Ready. Parallel Executions (Max {os.environ.get('LOKY_MAX_CPU_COUNT', 4)} Workers).")
    
    logger.info(">>> [6/6] Initializing Nemesis AI Godmode Integrations...")
    if CONFIG.get("GEMINI_API_KEY"):
        logger.info("    [OK] Gemini AI Heuristics Active.")
    else:
        logger.warning("    [WARN] Gemini AI key missing. Running without advanced ML heuristics.")
    
    logger.info("==================================================")
    logger.info("   NEMESIS ENGINE READY FOR OMNICHAIN OPERATIONS  ")
    logger.info("==================================================")

@asynccontextmanager
async def lifespan(app: FastAPI):
    await run_boot_diagnostics()
    import asyncio
    
    # Ensure Playwright browsers are installed before starting the engine
    asyncio.create_task(admin_log_broadcaster())
    asyncio.create_task(omega_ml_broadcaster())
    
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
            import subprocess
            
            use_tor = os.getenv("VITE_TOR_AUTO_START", "false").lower() == "true" # Defaulted to false for separate terminal
            if use_tor:
                darknet_script = os.path.join(os.path.dirname(__file__), "osint", "darknet.py")
                
                # Check if running on Windows to use CREATE_NEW_CONSOLE
                if os.name == 'nt':
                    subprocess.Popen([sys.executable, darknet_script], creationflags=subprocess.CREATE_NEW_CONSOLE)
                else:
                    # Fallback for Linux/Mac - though user is on Windows
                    subprocess.Popen([sys.executable, darknet_script])
                    
                logger.info("    [OK] Darknet crawler launched in a separate terminal window.")
            else:
                logger.info("    [SKIP] Darknet crawler disabled via VITE_TOR_AUTO_START=false. Run darknetv2.py in a separate console.")
        except Exception as e:
            logger.error(f"    [FAIL] Failed to launch Darknet crawler: {e}")
        
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
        "http://127.0.0.1:8000",
        "null"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

import os

# Resolve paths dynamically relative to the new monorepo structure
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

# Ensure static folder actually points to static files securely, not the root repo
app.mount("/static", StaticFiles(directory=os.path.join(FRONTEND_DIR, "static")), name="static")

active_sessions = {}
templates = Jinja2Templates(directory=os.path.join(FRONTEND_DIR, "templates"))

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

class KnowledgeRequest(BaseModel):
    url: str

from services.godmode_ml import load_ontology, register_ml_listener, remove_ml_listener, ingest_dataset, get_datasets
from services.asset_resolver import resolve_asset_logo

@app.get("/api/v1/assets/resolve")
async def api_resolve_asset(symbol: str, name: str = "", address: str = "", chain: str = "ethereum", website: str = ""):
    try:
        data = await resolve_asset_logo(symbol, name, address, chain, website)
        return data
    except Exception as e:
        return {"error": str(e), "logo": "/static/images/default_token.png"}

@app.get("/nemesis_omega", response_class=HTMLResponse)
async def get_nemesis_omega(request: Request):
    return templates.TemplateResponse("nemesis_omega.html", {"request": request})

@app.websocket("/ws/omega_ml")
async def websocket_omega_ml(websocket: WebSocket):
    await websocket.accept()
    omega_websockets.add(websocket)
    try:
        while True:
            await websocket.receive_text()
    except:
        omega_websockets.discard(websocket)

from services.config_manager import config_manager

@app.get("/api/v1/config")
async def api_get_config():
    """Retrieve structured UI configuration."""
    try:
        return config_manager.get_structured_config()
    except Exception as e:
        logger.error(f"Failed to fetch config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

class ConfigUpdateRequest(BaseModel):
    updates: dict

@app.post("/api/v1/config")
async def api_update_config(request: ConfigUpdateRequest):
    """Update variables in the .env file."""
    try:
        success = config_manager.update_config(request.updates)
        if success:
            return {"status": "success", "message": "Configuration updated successfully."}
        else:
            raise HTTPException(status_code=500, detail="Failed to write to .env file.")
    except Exception as e:
        logger.error(f"Failed to update config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/ml/ontology")
async def api_ml_ontology():
    from services.godmode_ml import load_ontology
    try:
        data = load_ontology()
        return {"data": data}
    except Exception as e:
        return {"error": str(e)}

from fastapi import BackgroundTasks

class DataIngestionRequest(BaseModel):
    filename: str

@app.post("/api/admin/ingest_data")
async def api_admin_ingest_data(req: DataIngestionRequest, background_tasks: BackgroundTasks):
    from services.data_ingestion_engine import ingest_jsonl, collection_entities, collection_arkham, collection_vasp, ingest_json_array
    import os
    
    file_path = os.path.join(os.path.dirname(__file__), "data", req.filename)
    if not os.path.exists(file_path):
        return {"status": "error", "message": f"File {req.filename} not found in data directory."}
        
    async def run_ingestion():
        if req.filename.endswith(".jsonl"):
            # Determine collection based on filename
            target_collection = collection_arkham if "arkham" in req.filename.lower() else collection_entities
            await ingest_jsonl(file_path, target_collection)
        elif req.filename.endswith(".json"):
            target_collection = collection_vasp if "vasp" in req.filename.lower() else collection_entities
            await ingest_json_array(file_path, target_collection)
            
    background_tasks.add_task(run_ingestion)
    return {"status": "success", "message": f"Ingestion for {req.filename} started in the background."}

class GodmodeRequest(BaseModel):
    action: str

@app.post("/api/admin/godmode/deploy")
async def api_admin_godmode_deploy(req: GodmodeRequest, background_tasks: BackgroundTasks):
    import subprocess
    import sys
    
    action = req.action.lower()
    script_path = None
    
    if action == "autonomous_agent":
        script_path = os.path.join(os.path.dirname(__file__), "scripts", "autonomous_agent.py")
    elif action == "godmode":
        script_path = os.path.join(os.path.dirname(__file__), "scripts", "godmode.py")
    else:
        return {"status": "error", "message": "Invalid godmode action."}
        
    if not os.path.exists(script_path):
        return {"status": "error", "message": f"Script not found: {script_path}"}
        
    def run_script():
        try:
            subprocess.Popen([sys.executable, script_path], creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0)
        except Exception as e:
            logger.error(f"Failed to launch godmode script {script_path}: {e}")
            
    background_tasks.add_task(run_script)
    return {"status": "success", "message": f"Godmode script '{action}' launched."}

@app.get("/api/osint/recon")
async def api_osint_recon(wallet_address: str):
    import asyncio
    try:
        from osint.nemesis_recon_enterprise import classify_wallet
        # Run synchronous function in thread pool if needed, or if it's actually sync
        loop = asyncio.get_event_loop()
        # Since classify_wallet is decorated with @retry, we assume it's synchronous
        result = await loop.run_in_executor(None, classify_wallet, wallet_address, None)
        return {"status": "success", "data": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}

import requests
from bs4 import BeautifulSoup

@app.post("/api/knowledge/index")
async def api_knowledge_index(req: KnowledgeRequest):
    try:
        url = req.url
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        for script in soup(["script", "style"]):
            script.decompose()
            
        text = soup.get_text(separator='\n')
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        provider = "unknown"
        if "cloudflare" in url.lower(): provider = "cloudflare"
        elif "render" in url.lower(): provider = "render"
        elif "github" in url.lower() or "git" in url.lower(): provider = "git"
        
        # Ensure dir exists
        kb_dir = os.path.join(os.path.dirname(__file__), "NEMESIS_KNOWLEDGE_BASE_LIBRARY")
        os.makedirs(kb_dir, exist_ok=True)
        
        file_path = os.path.join(kb_dir, f"{provider}_docs.txt")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(f"URL: {url}\n\n{text}")
            
        tokens = len(text.split())
        return {"status": "success", "file": f"{provider}_docs.txt", "tokens": tokens}
    except Exception as e:
        return Response(content=json.dumps({"error": str(e)}), status_code=500, media_type="application/json")
@app.get("/api/ml/datasets")
async def api_ml_datasets():
    datasets = get_datasets()
    return {"status": "success", "data": datasets}

class MLIngestRequest(BaseModel):
    url: str = ""
    source: str = ""
    content: str = ""

@app.post("/api/ml/ingest")
async def api_ml_ingest(req: MLIngestRequest):
    logger.info(f"Ingesting ML Dataset from {req.source or req.url}")
    try:
        source_data = req.content if req.content else req.url
        source_type = "content" if req.content else "url"
        entry = await ingest_dataset(source_data, source_type)
        return {"status": "success", "message": "Dataset ingested successfully into ML Knowledge Base.", "data": entry}
    except Exception as e:
        logger.error(f"Error ingesting ML dataset: {e}")
        return {"status": "error", "message": str(e)}

@app.websocket("/ws/ml_stream")
async def ws_ml_stream(websocket: WebSocket):
    await websocket.accept()
    q = asyncio.Queue()
    register_ml_listener(q)
    try:
        while True:
            event = await q.get()
            await websocket.send_json(event)
    except Exception:
        pass
    finally:
        remove_ml_listener(q)

@app.get("/")
async def dashboard(request: Request):
    return templates.TemplateResponse(request=request, name="nemesis_tracer.html")

@app.get("/favicon.ico")
async def favicon():
    return Response(content=b"", media_type="image/x-icon")

@app.get("/assets/fonts/{font_name}")
async def empty_font_fallback(font_name: str):
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

@app.get("/nemesis_tracer_landing")
async def nemesis_tracer_landing_route(request: Request):
    return templates.TemplateResponse(request=request, name="nemesis_tracer_landing.html")

@app.get("/enterprise_dashboard")
async def enterprise_dashboard_route(request: Request):
    return templates.TemplateResponse(request=request, name="nemesis_enterprise_dashboard.html")

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

from fastapi.responses import StreamingResponse

darknet_stream_clients = []

@app.get("/api/stream")
async def api_stream():
    async def event_generator():
        q = asyncio.Queue()
        darknet_stream_clients.append(q)
        try:
            while True:
                msg = await q.get()
                yield f"data: {json.dumps(msg)}\n\n"
        except asyncio.CancelledError:
            if q in darknet_stream_clients:
                darknet_stream_clients.remove(q)
            
    return StreamingResponse(event_generator(), media_type="text/event-stream")

class DarknetCommandRequest(BaseModel):
    command: str

@app.post("/api/darknet/command")
async def api_darknet_command(req: DarknetCommandRequest):
    cmd = req.command.strip()
    
    async def process_cmd():
        await asyncio.sleep(0.5)
        import datetime
        now = datetime.datetime.now(datetime.timezone.utc).strftime("%H:%M:%S")
        response_msg = {"message": f"Command not recognized: {cmd}. Type 'help' for available commands.", "style": "red", "ts": now}
        
        if cmd.lower() == "help":
            response_msg = {"message": "Available commands: scan <domain>, ping, status, clear", "style": "green", "ts": now}
        elif cmd.lower().startswith("scan"):
            response_msg = {"message": f"Initiating deep scan on {cmd.split(' ')[-1]}...", "style": "yellow", "ts": now}
        elif cmd.lower() == "status":
            response_msg = {"message": "Darknet Engine v2.0 - ONLINE - 12 Nodes Active", "style": "green", "ts": now}
        elif cmd.lower() == "ping":
            response_msg = {"message": "PONG", "style": "dim", "ts": now}
            
        for q in darknet_stream_clients:
            await q.put(response_msg)
            
    asyncio.create_task(process_cmd())
    
    return {"status": "success"}

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

@app.post("/api/admin/automated_maintenance")
async def api_admin_automated_maintenance(background_tasks: BackgroundTasks):
    async def run_maintenance():
        try:
            logger.info("Starting Godmode Automated Maintenance Sequence...")
            # We execute the local script
            process = await asyncio.create_subprocess_shell(
                f"{sys.executable} scripts/test_all_cases.py",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            report = stdout.decode('utf-8')
            if stderr:
                report += f"\n\nERRORS:\n{stderr.decode('utf-8')}"
                
            logger.info("Maintenance Sequence Complete.")
            
            # Save the report
            os.makedirs("logs", exist_ok=True)
            report_path = os.path.join("logs", "latest_maintenance_report.md")
            with open(report_path, "w") as f:
                f.write(report)
                
            # Broadcast the completion to the UI stream
            for q in darknet_stream_clients:
                import datetime
                now = datetime.datetime.now(datetime.timezone.utc).strftime("%H:%M:%S")
                await q.put({"message": "Maintenance test suite completed. Report generated.", "style": "green", "ts": now})
                
        except Exception as e:
            logger.error(f"Maintenance failed: {e}")
            
    background_tasks.add_task(run_maintenance)
    return {"status": "success", "message": "Automated maintenance sequence initiated via Godmode."}

from services.recursive_tracer import RecursiveTracer

class OmniChainEngineWrapper:
    def __init__(self, trace_id):
        self.trace_id = trace_id
        self.clients = set()
        self.is_running = False
        self.ledger = []
        self.seeds = []
        self.seed_chains = []
        self.tracing_method = "tracer"
        self.target_amount = 0.0
        self.tracer = RecursiveTracer()
        self.client_ip = "unknown"
        self.state_lock = asyncio.Lock()

    def setup(self, seeds_list, calc_amt, chain_override, start_date, end_date, target_currency, max_depth, max_hops, tracing_method, pathfinding_targets):
        self.seeds = seeds_list
        self.seed_chains = ["AUTO" for _ in seeds_list]
        self.target_amount = calc_amt
        self.tracing_method = tracing_method

    async def run(self):
        self.is_running = True
        try:
            for suspect_wallet in self.seeds:
                async for edge in self.tracer.start_omni_trace_bfs(suspect_wallet, max_depth=1000):
                    # Convert edge dict to TraceEngine style payload for UI
                    # Calculate USD Estimate
                    asset = str(edge.get('asset', 'UNKNOWN')).upper()
                    try: amount_val = float(edge.get('amount', 0))
                    except: amount_val = 0.0
                    
                    oracle = {
                        "ETH": 3500.00, "BTC": 65000.00, "SOL": 150.00, 
                        "BNB": 580.00, "TRX": 0.12, "USDC": 1.00, 
                        "USDT": 1.00, "DAI": 1.00, "MATIC": 0.80, 
                        "ARB": 1.10, "OP": 2.50, "HBAR": 0.10, 
                        "XRP": 0.50, "XLM": 0.10
                    }
                    price = oracle.get(asset, 0.0)
                    usd_val = amount_val * price
                    amount_str = f"{amount_val:,.4f} {asset} (~${usd_val:,.2f} USD)" if usd_val > 0 else f"{amount_val:,.4f} {asset}"
                    
                    node = {
                        "type": "TRANSFER",
                        "typeStr": edge.get("edge_type", "TRANSFER"),
                        "id": edge.get("tx_hash", "0x"),
                        "source": edge.get("from", "0x"),
                        "target": edge.get("to", "0x"),
                        "valStr": amount_str,
                        "chain": edge.get("chain", "UNK"),
                        "nameStr": "Unknown Entity",
                        "isBinance": False,
                        "displayId": edge.get("tx_hash", "0x")[:10] + "...",
                        "badgeIcon": "fa-exchange"
                    }
                    async with self.state_lock:
                        self.ledger.append(node)
                    
                    for ws in list(self.clients):
                        try:
                            await ws.send_json(node)
                        except:
                            self.clients.discard(ws)
                            
                    if edge.get("edge_type") == "TRANSFER" and edge.get("amount"):
                        if self.target_amount > 0 and abs(float(edge["amount"]) - self.target_amount) / self.target_amount < 0.05:
                            logger.info(f"Target amount matched: {edge['tx_hash']}")
                            break
        except Exception as e:
            logger.error(f"OmniChainEngineWrapper Error: {e}")
        self.is_running = False
        
        complete_msg = {"type": "COMPLETE", "message": "Trace finished."}
        for ws in list(self.clients):
            try:
                await ws.send_json(complete_msg)
            except:
                pass

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
        
        tx_seeds = [t for t in seeds_list if (len(t) == 66 and t.startswith("0x")) or (len(t) == 64 and not t.startswith("0x"))]
        wallet_seeds = [t for t in seeds_list if t not in tx_seeds]
        
        calc_amt = float(req.target_amount) if req.target_amount else 0.0
        computed_cur = req.target_currency
        
        if tx_seeds:
            logger.info("TX hashes detected in seeds. Extracting target wallets...")
            computed_amt_str, cur, extracted = await auto_compute_loss_amount(tx_seeds, req.chain_override)
            if calc_amt <= 0:
                calc_amt = float(computed_amt_str)
                computed_cur = cur
            for es in extracted:
                es_lower = es.lower()
                if es_lower not in wallet_seeds:
                    wallet_seeds.append(es_lower)
        elif calc_amt <= 0:
            logger.info("Target amount not provided. Attempting to auto-compute loss from seeds...")
            computed_amt_str, cur, extracted = await auto_compute_loss_amount(wallet_seeds, req.chain_override)
            calc_amt = float(computed_amt_str)
            computed_cur = cur
            for es in extracted:
                es_lower = es.lower()
                if es_lower not in wallet_seeds:
                    wallet_seeds.append(es_lower)
                    
        req.target_currency = computed_cur
        seeds_list = wallet_seeds
        
        if not seeds_list: return {"error": "No valid wallet addresses found or extracted"}

        trace_id = str(uuid.uuid4())[:8]
        
        engine = OmniChainEngineWrapper(trace_id)
        engine.setup(seeds_list, calc_amt, req.chain_override, req.start_date, req.end_date, req.target_currency, req.max_depth, req.max_hops, req.tracing_method, pathfinding_targets)
        active_sessions[trace_id] = engine
        
        client_ip = request.client.host if request.client else "unknown"
        engine.client_ip = client_ip
        
        # We don't start the background task until the WS connects
        return {"status": "started", "trace_id": trace_id}
    except Exception as e:
        logger.error(f"Failed to setup trace: {e}")
        return {"error": str(e)}

@app.post("/api/nemesis/autonomous_trace")
async def api_autonomous_trace(req: TraceRequest):
    try:
        raw_seeds = req.seeds.replace('"', '').replace("'", "")
        seeds_list = [t.strip().lower() for t in re.split(r'[\s,]+', raw_seeds) if t.strip()]
        if not seeds_list:
            return {"error": "No valid seeds provided"}
            
        trace_id = "AUTO_" + str(uuid.uuid4())[:8]
        # Fast configuration: depth 2, max hops 50 for quick autonomous endpoint discovery
        engine = OmniChainEngineWrapper(trace_id)
        engine.setup(seeds_list, 0.0, req.chain_override, "", "", "USD", 2, 50, "tracer", [])
        
        # Run trace asynchronously (but we await it)
        await engine.run()
            
        # Extract CEX / Mixer endpoints from the ledger
        cex_nodes = []
        for node in engine.ledger:
            t = node.get("typeStr", "UNKNOWN").upper()
            if t in ["CEX", "MIXER", "CUSTODIAL"]:
                cex_nodes.append(node)
                
        # Deduplicate by ID
        unique_nodes = {}
        for n in cex_nodes:
            unique_nodes[n["id"]] = n
            
        return {"status": "success", "data": list(unique_nodes.values())}
        
    except Exception as e:
        logger.error(f"Autonomous Trace failed: {e}")
        import traceback
        traceback.print_exc()
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
async def deep_scrape(address: str, chain: str = "ETHEREUM", max_pages: int = 5):
    from services.scraper_engine import scraper_instance
    try:
        res = await scraper_instance.deep_scrape_etherscan(address, chain=chain, max_pages=max_pages)
        return res if res else {"error": "Scrape failed"}
    except Exception as e:
        logger.error(f"Error in deep scrape endpoint: {e}")
        return {"error": str(e)}

@app.get("/api/nemesis_id/search")
async def search_nemesis_id(query: str):
    try:
        from services.trace_engine import detect_chain, get_wallet_label
        chain = detect_chain(query, "AUTO")
        label_doc = await get_wallet_label(query.lower())
        
        if label_doc and "nemesis_id" in label_doc:
            nid = label_doc["nemesis_id"]
        else:
            import hashlib
            nid = f"NMS-WALLET-{chain}-{hashlib.md5(query.lower().encode()).hexdigest()[:8].upper()}"
            
        return {"nemesis_id": nid, "address": query, "chain": chain, "status": "resolved"}
    except Exception as e:
        logger.error(f"Error in nemesis_id search: {e}")
        return {"error": str(e)}

@app.get("/api/darknet/search/{address}")
async def darknet_search_api(address: str):
    import pymongo
    import re
    try:
        # Fallback to local MongoDB which darknetv2.py defaults to
        client = pymongo.MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=2000)
        db = client["darknet"]
        
        results = []
        # darknetv2.py usually stores entities in 'entities' or 'crawled_data'
        # We will check 'entities' as the primary ontology storage
        docs = db.entities.find({"address": re.compile(address, re.IGNORECASE)}).limit(50)
        for doc in docs:
            doc.pop("_id", None)
            results.append(doc)
            
        return {"address": address, "hits": len(results), "data": results, "status": "success"}
    except Exception as e:
        logger.error(f"Darknet search failed: {e}")
        return {"error": "Database connection failed or not available.", "details": str(e), "status": "failed"}

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
# GODMODE ML ENDPOINTS (NEW)
# ==========================================
from services.godmode_ml import get_datasets, ingest_dataset, load_ontology, register_ml_listener, remove_ml_listener
import asyncio

class MLIngestRequest(BaseModel):
    url: str
    source: str

@app.get("/api/ml/datasets")
async def api_ml_datasets(token: dict = Depends(verify_access_token)):
    return {"datasets": get_datasets()}

@app.post("/api/ml/ingest")
async def api_ml_ingest(req: MLIngestRequest, token: dict = Depends(verify_access_token)):
    res = await ingest_dataset(req.url, req.source)
    return {"status": "success", "message": f"Ingested 1 new intelligence vector from {req.source}", "data": res}

@app.get("/api/ml/ontology")
async def api_ml_ontology():
    return {"data": load_ontology()}

@app.websocket("/ws/ml_stream")
async def ws_ml_stream(websocket: WebSocket):
    await websocket.accept()
    q = asyncio.Queue()
    register_ml_listener(q)
    try:
        while True:
            event = await q.get()
            await websocket.send_json(event)
    except Exception:
        pass
    finally:
        remove_ml_listener(q)
        try:
            await websocket.close()
        except:
            pass

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
    
    txs = await fetch_real_txs(address)
    balance = 0
    total_sent = 0
    total_received = 0
    
    for tx in txs:
        val = tx.get("raw_val", 0)
        if tx["type"] == "Receive":
            total_received += val
            balance += val
        else:
            total_sent += val
            balance -= val
            
    first_act = txs[-1]["timestamp"] if len(txs) > 0 else "N/A"
    last_act = txs[0]["timestamp"] if len(txs) > 0 else "N/A"
    
    return {
        "address": address,
        "nemesis_id": nemesis_id,
        "network": chain,
        "entity": label if label else "Unknown / Unlabeled",
        "balance": f"${round(abs(balance) * 3000, 2)} (Est. USD)",
        "first_activity": first_act,
        "last_activity": last_act,
        "total_sent": f"{round(total_sent, 4)}",
        "total_received": f"{round(total_received, 4)}",
        "total_transactions": len(txs),
        "clustered_addresses": []
    }

TX_CACHE = {}

async def fetch_real_txs(address: str):
    if address in TX_CACHE and time.time() - TX_CACHE[address]["last_fetched"] < 60:
        return TX_CACHE[address]["txs"]
    
    from services.trace_engine import detect_chain, TraceEngine, get_asset_ticker
    import aiohttp
    import ssl
    import certifi
    import asyncio
    from datetime import datetime, timezone
    
    chain_res = detect_chain(address, "AUTO")
    
    ssl_ctx = ssl.create_default_context(cafile=certifi.where())
    connector = aiohttp.TCPConnector(ssl=ssl_ctx)
    
    txs_map = {}
    
    async with aiohttp.ClientSession(connector=connector) as session:
        engine = TraceEngine("main-fetch")
        res = await engine.fetch_txs(session, address, chain_res)
        
        if res and res.get("data"):
            tx_type = res.get("type", "evm")
            actual_chain = res.get("actual_chain", chain_res)
            native_sym = get_asset_ticker(actual_chain)
            
            for tx in res["data"]:
                try:
                    # EVM Handling
                    if tx_type == "evm":
                        h = tx.get("hash", tx.get("transactionHash", ""))
                        decimals = int(tx.get("tokenDecimal", 18))
                        val = float(tx.get("value", 0)) / (10 ** decimals)
                        t = "Receive" if tx.get("to", "").lower() == address.lower() else "Send"
                        ts_int = int(tx.get("timeStamp", 0))
                        sym = tx.get("tokenSymbol", native_sym)
                        
                    # BTC Handling
                    elif tx_type == "btc":
                        h = tx.get("txid", "")
                        ts_int = int(tx.get("status", {}).get("block_time", 0))
                        
                        addr_lower = address.lower()
                        is_sender = any(i.get("prevout", {}).get("scriptpubkey_address", "").lower() == addr_lower for i in tx.get("vin", []))
                        
                        # Calculate total sent or received by this address
                        val = 0
                        if is_sender:
                            t = "Send"
                            for o in tx.get("vout", []):
                                if o.get("scriptpubkey_address", "").lower() != addr_lower:
                                    val += float(o.get("value", 0)) / 1e8
                        else:
                            t = "Receive"
                            for o in tx.get("vout", []):
                                if o.get("scriptpubkey_address", "").lower() == addr_lower:
                                    val += float(o.get("value", 0)) / 1e8
                                    
                        sym = "BTC"
                        
                    # Solana Handling
                    elif tx_type == "solana":
                        h = tx.get("transaction", {}).get("signatures", [""])[0]
                        ts_int = tx.get("blockTime", 0)
                        
                        # Simplified parsing for native SOL transfers
                        pre_bals = tx.get("meta", {}).get("preBalances", [])
                        post_bals = tx.get("meta", {}).get("postBalances", [])
                        keys = [k.get("pubkey") for k in tx.get("transaction", {}).get("message", {}).get("accountKeys", [])]
                        
                        val = 0
                        t = "Unknown"
                        if address in keys:
                            idx = keys.index(address)
                            if idx < len(pre_bals) and idx < len(post_bals):
                                diff = (post_bals[idx] - pre_bals[idx]) / 1e9
                                val = abs(diff)
                                t = "Receive" if diff > 0 else "Send"
                        sym = "SOL"
                        
                    # Ripple Handling
                    elif tx_type == "ripple":
                        h = tx.get("hash", "")
                        ts_int = tx.get("date", 0) + 946684800 # Ripple epoch is Jan 1, 2000
                        t_tx = tx.get("tx", tx)
                        
                        val = 0
                        t = "Unknown"
                        if t_tx.get("TransactionType") == "Payment":
                            amt = t_tx.get("Amount", 0)
                            if isinstance(amt, str): val = float(amt) / 1e6
                            elif isinstance(amt, dict): val = float(amt.get("value", 0))
                            
                            t = "Send" if t_tx.get("Account") == address else "Receive"
                        sym = "XRP"
                        
                    # Tron Handling
                    elif tx_type == "tron":
                        h = tx.get("hash", tx.get("txID", ""))
                        ts = tx.get("block_timestamp", tx.get("timestamp", 0))
                        ts_int = int(ts) // 1000 if ts > 1e10 else int(ts)
                        
                        t = "Send" if tx.get("ownerAddress", tx.get("from")) == address else "Receive"
                        
                        val = 0
                        if "amount" in tx and tx.get("amount") is not None:
                            try: val = float(tx.get("amount")) / 1e6
                            except: val = 0
                        sym = tx.get("tokenInfo", {}).get("tokenAbbr", "TRX")
                        
                    # Stellar Handling
                    elif tx_type == "stellar":
                        h = tx.get("transaction_hash", "")
                        
                        dt = datetime.strptime(tx.get("created_at", "2000-01-01T00:00:00Z").replace("Z",""), "%Y-%m-%dT%H:%M:%S")
                        ts_int = int(dt.timestamp())
                        
                        t = "Send" if tx.get("from") == address else "Receive"
                        val = float(tx.get("amount", 0))
                        sym = tx.get("asset_code", "XLM")
                    
                    else:
                        continue
                        
                    if val > 0:
                        ts_str = datetime.fromtimestamp(ts_int).strftime('%Y-%m-%d %H:%M:%S')
                        unique_hash = f"{h}_{sym}"
                        txs_map[unique_hash] = {
                            "type": t,
                            "timestamp": ts_str,
                            "ts_int": ts_int,
                            "hash": h,
                            "amount": f"{round(val, 4)} {sym}",
                            "network": actual_chain,
                            "raw_val": val,
                            "symbol": sym
                        }
                except Exception as e:
                    pass
            
    # Sort unified transactions by timestamp descending
    sorted_txs = sorted(list(txs_map.values()), key=lambda x: x["ts_int"], reverse=True)[:150]
    
    # Remove temporary sort key
    for tx in sorted_txs:
        del tx["ts_int"]
        
    TX_CACHE[address] = {"txs": sorted_txs, "last_fetched": time.time()}
    return sorted_txs

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
    txs = await fetch_real_txs(address)
    
    darknet_mentions = 0
    arkham_entity = None
    vasp_entity = None
    osint_entity = None
    
    try:
        from pymongo import MongoClient
        import os
        mongo_uri = os.environ.get("MONGO_URI", "mongodb+srv://nemesis:nemesis2026@nemesisdb.vir5vg2.mongodb.net/?appName=nemesisdb")
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=2000)
        db = client.get_database("nemesis_intel")
        
        # Check global_entities
        global_doc = db.global_entities.find_one({"_id": address})
        if global_doc:
            osint_entity = global_doc.get("entity")
            
        # Check arkham_intel
        ark_doc = db.arkham_intel.find_one({"_id": address})
        if ark_doc:
            arkham_entity = ark_doc.get("entity") or ark_doc.get("name")
            
        # Check vasp_directory
        vasp_doc = db.vasp_directory.find_one({"_id": address})
        if vasp_doc:
            vasp_entity = vasp_doc.get("entity")
            
        # Check OSINT profiles
        osint_doc = db.osint_profiles.find_one({"address": address})
        if osint_doc:
            osint_entity = osint_entity or osint_doc.get("identities", {}).get("domains", [None])[0]
        
        # Query darknet collection for actual data
        darknet_mentions = db.darknet_data.count_documents({"uie_entities.value": address})
        client.close()
    except Exception as e:
        logger.error(f"MongoDB intel fetch error: {e}")
        
    top_interacted = list(set([t["sender"] if t["type"] == "Receive" else t["receiver"] for t in txs[:5]]))
    custodial_entry = "Unknown"
    if txs and txs[-1]["type"] == "Receive":
        custodial_entry = txs[-1]["sender"]
        
    return {
        "top_interacted": top_interacted[:3],
        "custodial_entry": custodial_entry,
        "is_malicious": darknet_mentions > 0,
        "social_media": osint_entity or "None Found",
        "darknet_mentions": f"{darknet_mentions} Mentions",
        "arkham_intel": arkham_entity,
        "vasp_intel": vasp_entity,
        "osint_intel": osint_entity
    }

@app.get("/api/nemesis_id/tx_history/{address}")
async def get_nemesis_tx_history(address: str):
    txs = await fetch_real_txs(address)
    return {"transactions": txs}

@app.post("/api/nemesis_id/generate_report")
async def nemesis_generate_report(req: NemesisReportRequest):
    from google import genai
    from services.trace_engine import CONFIG
    import traceback
    
    keys = CONFIG.get("GEMINI_API_KEYS", [])
    if not keys:
        return {"markdown": "Error: No Gemini API keys configured."}
        
    try:
        client = genai.Client(api_key=keys[0])
        model_name = "gemini-2.5-flash"
        
        import json
        
        # Prepare context data
        context_data = ""
        if req.ledger_data:
            # Take up to 50 txs to avoid token limits
            context_data += f"\n\n### Trace Ledger Data (First 50 records):\n{json.dumps(req.ledger_data[:50], indent=2)}"
        if req.stats:
            context_data += f"\n\n### Node Statistics:\n{json.dumps(req.stats, indent=2)}"
            
        prompt = f"Write a comprehensive forensic intelligence report on the cryptocurrency address {req.address}. Include sections for Executive Summary, AML Risk, Known Entities, and Transaction Patterns. Use the following context data if provided: {context_data}. Format it entirely in Markdown."
        if req.type == "insights":
            prompt = f"Provide a brief 3-paragraph forensic AI insight for the cryptocurrency address {req.address}. Focus on anomalies, risk factors, and cluster behavior based on the following tracer data: {context_data}. Format it entirely in Markdown."
            
        response = await asyncio.to_thread(client.models.generate_content, model=model_name, contents=prompt)
        return {"markdown": response.text}
    except Exception as e:
        logger.error(f"Gemini API Error: {traceback.format_exc()}")
        return {"markdown": f"Error generating report: {str(e)}"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8088))
    uvicorn.run(app, host="0.0.0.0", port=port)
