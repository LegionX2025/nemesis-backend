import os
import re

def main():
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)
    os.makedirs('services', exist_ok=True)
    
    try:
        with open('index.py', 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print("index.py not found. Please ensure you are in the correct directory.")
        return

    # Extract HTML
    match = re.search(r'html_content\s*=\s*r"""(.*?)"""', content, re.DOTALL)
    if match:
        html = match.group(1)
        with open('templates/index.html', 'w', encoding='utf-8') as f:
            f.write(html)
        print("✅ Extracted templates/index.html")
    else:
        print("❌ Could not find html_content block.")

    # We will generate main.py
    main_code = """
import os
import json
import logging
from collections import defaultdict
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, Request, BackgroundTasks
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import uvicorn
import uuid

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("OmniChainEngine")

from services.trace_engine import TraceEngine, init_mongodb, get_asset_ticker, detect_chain, EVM_DOMAINS, get_active_traces, get_mongo_status, fetch_saved_traces

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_mongodb()
    yield

app = FastAPI(title="Nemesis OmniChain API", description="Lionsgate OmniChain Forensic Engine", lifespan=lifespan)
app.mount("/static", StaticFiles(directory="."), name="static")
templates = Jinja2Templates(directory="templates")

active_sessions = {}

class TraceRequest(BaseModel):
    seeds: str
    target_amount: str = ""
    start_date: str = ""
    end_date: str = ""
    chain_override: str = "AUTO"

@app.get("/")
async def dashboard(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/admin")
async def admin_dashboard(request: Request):
    return templates.TemplateResponse("admin.html", {"request": request})

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
        seeds_list = [s.strip().lower() if detect_chain(s, req.chain_override) in EVM_DOMAINS or detect_chain(s, req.chain_override) == "EVM_AUTO" else s.strip() for s in req.seeds.split('\\n') if s.strip()]
        if not seeds_list: return {"error": "No seeds provided"}
        
        calc_amt = float(req.target_amount) if req.target_amount else 80000.0
        trace_id = str(uuid.uuid4())[:8]
        
        engine = TraceEngine(trace_id)
        engine.setup(seeds_list, calc_amt, req.chain_override, req.start_date, req.end_date)
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
    
    # Start engine loop if not started
    if not engine.is_running:
        engine.is_running = True
        import asyncio
        asyncio.create_task(engine.run())
        
    try:
        while True: await websocket.receive_text()
    except:
        engine.clients.discard(websocket)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=3001)
"""
    with open('main.py', 'w', encoding='utf-8') as f:
        f.write(main_code)
    print("✅ Created main.py")

    # We will extract everything before `app = FastAPI(...)` and after the imports into trace_engine.py
    # This involves some regex to rip out the pure python logic.
    start_str = "import certifi"
    end_str = "@app.post"
    
    start_idx = content.find(start_str)
    end_idx = content.find(end_str)
    
    if start_idx != -1 and end_idx != -1:
        engine_logic = content[start_idx:end_idx]
        
        # We need to strip out `app = FastAPI(...)`, `state = SOCState()`, `active_engine_task`
        engine_logic = re.sub(r'app\s*=\s*FastAPI\(.*?\)', '', engine_logic, flags=re.DOTALL)
        engine_logic = re.sub(r'state\s*=\s*SOCState\(\)', '', engine_logic)
        engine_logic = re.sub(r'clients\s*=\s*set\(\)', '', engine_logic)
        engine_logic = re.sub(r'active_engine_task\s*=\s*None', '', engine_logic)
        
        # Replace global `state.` with `self.` inside a class, but it's simpler to pass `state` or wrap it.
        # Since I'm doing a quick extraction, let's wrap it in `TraceEngine` class or just modify SOCState to run it.
        # For simplicity, we will save the raw engine logic to trace_engine_raw.py and we will refactor it manually.
        
        with open('services/trace_engine_raw.py', 'w', encoding='utf-8') as f:
            f.write("import os\\nimport asyncio\\nimport json\\nimport csv\\nimport time\\nfrom datetime import datetime, timezone\\nfrom collections import defaultdict\\nimport certifi\\nimport aiohttp\\nimport logging\\nfrom motor.motor_asyncio import AsyncIOMotorClient\\nlogger = logging.getLogger('TraceEngine')\\n\\n")
            f.write(engine_logic)
            f.write("\\n\\n")
            
        print("✅ Extracted core logic to services/trace_engine_raw.py. Further manual refactoring of state is needed.")
    else:
        print("❌ Could not extract engine logic.")

if __name__ == "__main__":
    main()
