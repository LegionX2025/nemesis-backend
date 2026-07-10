import os
import json
import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.tracing_engine_v33 import NemesisV33Engine

app = FastAPI(title="NEMESIS v33 API", description="End-to-End Blockchain Forensic Tracing System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

engine = NemesisV33Engine()

class TraceRequest(BaseModel):
    address: str
    target_amount: float = None
    autonomous_mode: bool = False

@app.post("/api/trace")
async def trace_address(req: TraceRequest):
    try:
        # Executes the 15-stage pipeline
        result = await engine.execute_pipeline(req.address, target_amount=req.target_amount, autonomous=req.autonomous_mode)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/nemesis_id/{address}")
async def get_nemesis_id(address: str):
    try:
        profile = await engine.generate_nemesis_id(address)
        return profile
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Serve static frontend
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "cloudflare_frontend")
if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")

if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
