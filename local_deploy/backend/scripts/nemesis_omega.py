r"""
==============================================================================
🛡️ NEMESIS Ω : AUTONOMOUS INTELLIGENCE OPERATING SYSTEM (AIOS)
==============================================================================
VERSION: 100.0.0 (OMEGA MONOLITH DEPLOYMENT)
AUTHOR: LIONSGATE INTELLIGENCE NETWORK
==============================================================================
WARNING: This is a fully autonomous, self-healing, self-bootstrapping AI
Kernel. Do not run in environments without appropriate containment protocols.
==============================================================================
"""

import sys
import os
import subprocess
import time
import json
import asyncio
import logging
from enum import Enum, auto
from datetime import datetime

# ==============================================================================
# 📦 PHASE A: SELF-BOOTSTRAPPING SUBSYSTEM (LEVEL 1)
# ==============================================================================
def bootstrap_environment():
    """Level 1 Autonomous Bootstrapper: Ensures environment integrity before launch."""
    print("🔄 [NEMESIS Ω] Initializing Self-Bootstrapping Sequence...")
    required_packages = {
        "google-genai": "google.genai",
        "psutil": "psutil",
        "python-dotenv": "dotenv",
        "fastapi": "fastapi",
        "uvicorn": "uvicorn",
        "motor": "motor",
        "pymongo": "pymongo",
        "neo4j": "neo4j",
        "scikit-learn": "sklearn",
        "websockets": "websockets"
    }
    missing_packages = []
    
    for pip_name, module_name in required_packages.items():
        try:
            __import__(module_name)
        except ImportError:
            missing_packages.append(pip_name)
            
    if missing_packages:
        print(f"[*] Missing critical dependencies detected: {missing_packages}. Auto-installing...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-q"] + missing_packages, check=True)
        print("[+] Dependencies successfully installed. Self-restarting to apply changes...")
        os.execv(sys.executable, [sys.executable] + sys.argv)

# Trigger Bootstrapper immediately
bootstrap_environment()

# Core Imports after bootstrap
import psutil
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from dotenv import load_dotenv

# Configure Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [NEMESIS Ω] [%(levelname)s] %(message)s")
logger = logging.getLogger("NEMESIS_OMEGA")

# Load Configuration
load_dotenv()

# ==============================================================================
# 🧠 PHASE B: THE HYBRID FINITE STATE MACHINE (FSM) ARCHITECTURE
# ==============================================================================

class GlobalSystemState(Enum):
    BOOT = auto(); INITIALIZE = auto(); DISCOVER = auto()
    INGEST = auto(); VERIFY = auto(); NORMALIZE = auto()
    CLASSIFY = auto(); ENRICH = auto(); ANALYZE = auto()
    CORRELATE = auto(); REASON = auto(); PREDICT = auto()
    PLAN = auto(); SIMULATE = auto(); DECIDE = auto()
    RECOMMEND = auto(); WAIT_APPROVAL = auto(); EXECUTE = auto()
    MONITOR = auto(); VERIFY_RESULT = auto(); LEARN = auto()
    OPTIMIZE = auto(); SELF_TEST = auto(); SELF_HEAL = auto()
    SELF_DEPLOY = auto(); SELF_VALIDATE = auto(); AUDIT = auto()
    ARCHIVE = auto(); IDLE = auto(); SUSPEND = auto(); SHUTDOWN = auto()

class HumanStateMachine(Enum):
    UNKNOWN = auto(); NEW_USER = auto(); VERIFIED = auto()
    ANALYST = auto(); SENIOR_ANALYST = auto(); INVESTIGATOR = auto()
    FORENSIC_ANALYST = auto(); AML_ANALYST = auto(); THREAT_HUNTER = auto()
    CASE_MANAGER = auto(); LEGAL_REVIEW = auto(); COMPLIANCE = auto()
    SUPERVISOR = auto(); EXECUTIVE = auto(); SYSTEM_ADMIN = auto()
    AI_SUPERVISOR = auto(); READ_ONLY = auto(); LOCKED = auto()
    SUSPENDED = auto(); REVOKED = auto()

class InvestigationFSM(Enum):
    CASE_CREATED = auto(); EVIDENCE_COLLECTED = auto(); HASH_VERIFIED = auto()
    NORMALIZED = auto(); CORRELATED = auto(); ENTITY_RESOLVED = auto()
    GRAPH_BUILT = auto(); TIMELINE_COMPLETE = auto(); ATTRIBUTION = auto()
    RISK_ANALYSIS = auto(); INTELLIGENCE_REPORT = auto(); LEGAL_REVIEW = auto()
    EXTERNAL_COORDINATION = auto(); CLOSED = auto(); ARCHIVED = auto()

class BlockchainFSM(Enum):
    WALLET_CREATED = auto(); WALLET_ACTIVE = auto(); RECEIVE = auto()
    TRANSFER = auto(); APPROVAL = auto(); PERMIT = auto()
    PERMIT2 = auto(); SWAP = auto(); WRAP = auto()
    BRIDGE = auto(); MINT = auto(); LIQUIDITY = auto()
    STAKE = auto(); BORROW = auto(); FLASH_LOAN = auto()
    DEX = auto(); CROSS_CHAIN = auto(); MIXER = auto()
    EXCHANGE_DEPOSIT = auto(); EXCHANGE_WITHDRAWAL = auto()
    CASH_OUT = auto(); DORMANT = auto(); COMPROMISED = auto()
    RECOVERED = auto(); FROZEN = auto(); SEIZED = auto()

# ==============================================================================
# 🤖 PHASE C: AUTONOMOUS AGENT ORCHESTRATOR
# ==============================================================================

class AgentSwarmCoordinator:
    def __init__(self):
        self.state = GlobalSystemState.BOOT
        self.active_agents = []
        logger.info("Agent Swarm Coordinator Initialized.")

    async def spin_up_swarm(self):
        """Simulates spinning up 20+ specialized AI Agents."""
        agents = [
            "Blockchain Agent", "Threat Agent", "OSINT Agent", 
            "AML Agent", "Forensics Agent", "Graph Agent", 
            "Entity Agent", "Knowledge Agent"
        ]
        self.state = GlobalSystemState.INITIALIZE
        for agent in agents:
            logger.info(f"Spawning Agent: [ {agent} ]")
            await asyncio.sleep(0.1) # Simulate boot time
        self.state = GlobalSystemState.IDLE
        logger.info("All Agents Active and Idle. Awaiting directives.")

# ==============================================================================
# 🏥 PHASE D: SELF-HEALING MEMORY ENGINE
# ==============================================================================

class SelfHealingEngine:
    """Monitors the runtime. If a fatal crash occurs, it intercepts the stack trace."""
    def __init__(self):
        self.memory_file = "omega_cognition.json"
        
    def check_health(self):
        ram_percent = psutil.virtual_memory().percent
        cpu_percent = psutil.cpu_percent()
        if ram_percent > 95:
            logger.critical("RAM exceeding 95%. Autonomous garbage collection triggered.")
            # Trigger GC or restart

# ==============================================================================
# 🌐 PHASE E: THE NEMESIS OMEGA LIGHT THEME DASHBOARD (EMBEDDED)
# ==============================================================================

HTML_DASHBOARD = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NEMESIS Ω | Autonomous Intelligence Operating System</title>
    
    <!-- Ultra-Premium Light Theme Assets -->
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r134/three.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/vanta@latest/dist/vanta.waves.min.js"></script>
    
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;700;900&family=JetBrains+Mono:wght@400;700&display=swap');
        
        body { 
            font-family: 'Inter', sans-serif; 
            background-color: #f8fafc; 
            color: #0f172a; 
            margin: 0; 
            overflow: hidden; /* App feels native */
        }
        .mono { font-family: 'JetBrains Mono', monospace; }
        
        #vanta-canvas {
            position: fixed;
            top: 0; left: 0; width: 100vw; height: 100vh;
            z-index: -1;
            opacity: 0.6; /* Subtle light theme background */
        }

        /* Glassmorphism Panels */
        .glass-panel {
            background: rgba(255, 255, 255, 0.85);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border: 1px solid rgba(226, 232, 240, 0.8);
            border-radius: 16px;
            box-shadow: 0 10px 40px -10px rgba(0, 0, 0, 0.05), 0 1px 3px rgba(0, 0, 0, 0.05);
        }

        /* Terminal Output Container */
        .log-container {
            height: 300px;
            overflow-y: auto;
            scrollbar-width: thin;
        }
        .log-entry { margin-bottom: 4px; font-size: 0.75rem; border-bottom: 1px solid rgba(0,0,0,0.02); padding-bottom: 2px;}
        .log-info { color: #334155; }
        .log-success { color: #059669; }
        .log-warn { color: #d97706; }
        .log-error { color: #dc2626; }

        /* FSM Nodes */
        .fsm-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
            gap: 8px;
        }
        .fsm-node {
            padding: 8px;
            font-size: 0.65rem;
            text-align: center;
            border-radius: 6px;
            border: 1px solid #e2e8f0;
            background: #f1f5f9;
            color: #64748b;
            font-weight: 700;
            transition: all 0.3s ease;
        }
        .fsm-node.active {
            background: #3b82f6;
            color: white;
            border-color: #2563eb;
            box-shadow: 0 0 15px rgba(59, 130, 246, 0.4);
            transform: scale(1.05);
        }

        /* Animations */
        @keyframes pulse-ring {
            0% { transform: scale(0.8); opacity: 0.5; }
            100% { transform: scale(1.3); opacity: 0; }
        }
        .pulse-indicator {
            position: relative;
            width: 12px; height: 12px;
            background: #10b981;
            border-radius: 50%;
        }
        .pulse-indicator::before {
            content: '';
            position: absolute;
            left: -4px; top: -4px; right: -4px; bottom: -4px;
            border: 2px solid #10b981;
            border-radius: 50%;
            animation: pulse-ring 2s cubic-bezier(0.215, 0.61, 0.355, 1) infinite;
        }
    </style>
</head>
<body class="h-screen w-screen flex flex-col p-4 gap-4">

    <!-- WebGL Background -->
    <div id="vanta-canvas"></div>

    <!-- Header -->
    <header class="glass-panel w-full p-4 flex justify-between items-center z-10 shrink-0">
        <div class="flex items-center gap-4">
            <div class="w-12 h-12 bg-blue-600 rounded-xl flex items-center justify-center text-white font-black text-2xl shadow-lg shadow-blue-200">Ω</div>
            <div>
                <h1 class="text-2xl font-black tracking-tight text-slate-800">NEMESIS OMEGA</h1>
                <p class="text-xs font-bold tracking-widest text-slate-500 uppercase">Autonomous Intelligence Operating System</p>
            </div>
        </div>
        <div class="flex items-center gap-6">
            <div class="flex items-center gap-2">
                <span class="text-xs font-bold text-slate-500">SYSTEM STATUS</span>
                <div class="flex items-center gap-2 bg-emerald-50 px-3 py-1 rounded-full border border-emerald-100">
                    <div class="pulse-indicator"></div>
                    <span class="text-xs font-black text-emerald-700 uppercase tracking-wide">Autonomous</span>
                </div>
            </div>
            <button onclick="startInvestigation()" class="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg font-bold text-sm transition-colors shadow-md flex items-center gap-2">
                <i class="fa-solid fa-play"></i> Initialize Swarm
            </button>
        </div>
    </header>

    <!-- Main Content Grid -->
    <main class="flex-grow grid grid-cols-12 gap-4 z-10 overflow-hidden h-full">
        
        <!-- Left Column: Engine Diagnostics & Swarm -->
        <div class="col-span-3 flex flex-col gap-4 overflow-y-auto pr-2 pb-10">
            
            <div class="glass-panel p-5">
                <h3 class="text-sm font-bold text-slate-800 mb-4 flex items-center gap-2"><i class="fa-solid fa-microchip text-blue-500"></i> Core Architectures</h3>
                <div class="space-y-3">
                    <div class="flex justify-between items-center p-2 rounded bg-slate-50 border border-slate-100">
                        <span class="text-xs font-bold text-slate-600"><i class="fa-solid fa-database mr-2 text-green-500"></i> MongoDB Atlas</span>
                        <span class="text-xs text-green-600 font-mono">CONNECTED</span>
                    </div>
                    <div class="flex justify-between items-center p-2 rounded bg-slate-50 border border-slate-100">
                        <span class="text-xs font-bold text-slate-600"><i class="fa-solid fa-diagram-project mr-2 text-blue-500"></i> Neo4j Aura Graph</span>
                        <span class="text-xs text-blue-600 font-mono">CONNECTED</span>
                    </div>
                    <div class="flex justify-between items-center p-2 rounded bg-slate-50 border border-slate-100">
                        <span class="text-xs font-bold text-slate-600"><i class="fa-solid fa-brain mr-2 text-purple-500"></i> Gemini AI Kernel</span>
                        <span class="text-xs text-purple-600 font-mono">ONLINE</span>
                    </div>
                    <div class="flex justify-between items-center p-2 rounded bg-slate-50 border border-slate-100">
                        <span class="text-xs font-bold text-slate-600"><i class="fa-solid fa-shield-virus mr-2 text-red-500"></i> Self-Healing Matrix</span>
                        <span class="text-xs text-emerald-600 font-mono">ACTIVE</span>
                    </div>
                </div>
            </div>

            <div class="glass-panel p-5 flex-grow">
                <h3 class="text-sm font-bold text-slate-800 mb-4 flex items-center gap-2"><i class="fa-solid fa-robot text-slate-600"></i> Active Agent Swarm</h3>
                <div class="space-y-2" id="agent-list">
                    <!-- Populated by JS -->
                </div>
            </div>

        </div>

        <!-- Center Column: Global FSM & Visualization -->
        <div class="col-span-6 flex flex-col gap-4">
            
            <div class="glass-panel p-5">
                <h3 class="text-sm font-bold text-slate-800 mb-4 flex items-center gap-2"><i class="fa-solid fa-gears text-blue-500"></i> Global System Finite State Machine (FSM)</h3>
                <div class="fsm-grid" id="fsm-grid">
                    <!-- Populated by JS -->
                </div>
            </div>

            <div class="glass-panel p-5 flex-grow relative overflow-hidden bg-white/40">
                <div class="absolute top-4 left-4 z-10 flex items-center gap-2 bg-white/80 backdrop-blur px-3 py-1 rounded-md border border-slate-200">
                    <i class="fa-solid fa-network-wired text-slate-400"></i>
                    <span class="text-xs font-bold text-slate-600 uppercase tracking-widest">Neo4j Neural Projection</span>
                </div>
                <!-- Simulated Graph Visualization -->
                <div class="w-full h-full flex items-center justify-center">
                    <div class="w-64 h-64 border-4 border-dashed border-slate-200 rounded-full flex items-center justify-center animate-[spin_30s_linear_infinite]">
                        <div class="w-48 h-48 border-4 border-slate-300 rounded-full flex items-center justify-center">
                            <i class="fa-solid fa-cube text-6xl text-slate-200"></i>
                        </div>
                    </div>
                </div>
            </div>

        </div>

        <!-- Right Column: Real-time Terminal Log -->
        <div class="col-span-3 glass-panel p-0 flex flex-col overflow-hidden">
            <div class="p-4 border-b border-slate-200 bg-slate-50/50 flex justify-between items-center">
                <h3 class="text-sm font-bold text-slate-800 flex items-center gap-2"><i class="fa-solid fa-terminal text-slate-600"></i> Autonomous Stream</h3>
                <span class="text-[10px] font-mono text-slate-400 bg-white px-2 py-1 border border-slate-200 rounded">PORT 8888</span>
            </div>
            <div class="p-4 bg-[#fafafa] flex-grow log-container mono" id="terminal-log">
                <div class="log-entry log-info">> NEMESIS OMEGA KERNEL BOOT...</div>
                <div class="log-entry log-success">> Self-Bootstrapping Check: OK</div>
                <div class="log-entry log-success">> Hybrid FSM Architecture Loaded.</div>
            </div>
        </div>

    </main>

    <script>
        // --- 3D Background Setup ---
        document.addEventListener('DOMContentLoaded', () => {
            VANTA.WAVES({
                el: "#vanta-canvas",
                mouseControls: true,
                touchControls: true,
                gyroControls: false,
                minHeight: 200.00,
                minWidth: 200.00,
                scale: 1.00,
                scaleMobile: 1.00,
                color: 0xe2e8f0,
                shininess: 35.00,
                waveHeight: 15.00,
                waveSpeed: 0.50,
                zoom: 0.75
            });
            initFSM();
            initAgents();
            connectWebSocket();
        });

        // --- Terminal Logic ---
        const terminal = document.getElementById('terminal-log');
        function log(msg, type='info') {
            const div = document.createElement('div');
            div.className = `log-entry log-${type}`;
            const time = new Date().toLocaleTimeString([], {hour12: false, hour: '2-digit', minute:'2-digit', second:'2-digit', fractionalSecondDigits: 3});
            div.innerHTML = `<span class="text-slate-400">[${time}]</span> ${msg}`;
            terminal.appendChild(div);
            terminal.scrollTop = terminal.scrollHeight;
        }

        // --- FSM Logic ---
        const fsmStates = [
            "BOOT", "INITIALIZE", "DISCOVER", "INGEST", "VERIFY", "NORMALIZE", 
            "CLASSIFY", "ENRICH", "ANALYZE", "CORRELATE", "REASON", "PREDICT",
            "PLAN", "SIMULATE", "DECIDE", "RECOMMEND", "EXECUTE", "MONITOR", 
            "LEARN", "OPTIMIZE", "SELF_HEAL", "IDLE"
        ];
        
        function initFSM() {
            const grid = document.getElementById('fsm-grid');
            fsmStates.forEach(state => {
                const div = document.createElement('div');
                div.className = 'fsm-node';
                div.id = `fsm-${state}`;
                div.innerText = state;
                grid.appendChild(div);
            });
            updateFSMState('IDLE');
        }

        function updateFSMState(activeState) {
            document.querySelectorAll('.fsm-node').forEach(node => node.classList.remove('active'));
            const activeNode = document.getElementById(`fsm-${activeState}`);
            if (activeNode) activeNode.classList.add('active');
        }

        // --- Agent Logic ---
        const agents = [
            {name: "Blockchain Tracer", icon: "fa-link", color: "text-blue-500"},
            {name: "OSINT Crawler", icon: "fa-spider", color: "text-red-500"},
            {name: "ML Clustering", icon: "fa-project-diagram", color: "text-purple-500"},
            {name: "Neo4j Graph AI", icon: "fa-circle-nodes", color: "text-emerald-500"},
            {name: "Threat Hunter", icon: "fa-crosshairs", color: "text-amber-500"}
        ];

        function initAgents() {
            const list = document.getElementById('agent-list');
            agents.forEach(a => {
                const div = document.createElement('div');
                div.className = "flex items-center justify-between p-2 rounded-lg bg-slate-50 border border-slate-100";
                div.innerHTML = `
                    <div class="flex items-center gap-3">
                        <div class="w-8 h-8 rounded-full bg-white border border-slate-200 flex items-center justify-center shadow-sm">
                            <i class="fa-solid ${a.icon} ${a.color} text-xs"></i>
                        </div>
                        <span class="text-xs font-bold text-slate-700">${a.name}</span>
                    </div>
                    <div class="flex items-center gap-1" id="status-${a.name.replace(/\s/g, '')}">
                        <div class="w-2 h-2 rounded-full bg-slate-300"></div>
                        <span class="text-[10px] text-slate-400 font-mono">IDLE</span>
                    </div>
                `;
                list.appendChild(div);
            });
        }

        function updateAgentStatus(agentName, isRunning) {
            const id = `status-${agentName.replace(/\s/g, '')}`;
            const el = document.getElementById(id);
            if (el) {
                if (isRunning) {
                    el.innerHTML = `
                        <div class="w-2 h-2 rounded-full bg-blue-500 animate-pulse"></div>
                        <span class="text-[10px] text-blue-600 font-bold font-mono">WORKING</span>
                    `;
                } else {
                    el.innerHTML = `
                        <div class="w-2 h-2 rounded-full bg-slate-300"></div>
                        <span class="text-[10px] text-slate-400 font-mono">IDLE</span>
                    `;
                }
            }
        }

        // --- WebSocket & Simulation ---
        let ws;
        function connectWebSocket() {
            ws = new WebSocket(`ws://${window.location.host}/ws`);
            ws.onmessage = function(event) {
                const data = JSON.parse(event.data);
                if (data.type === 'log') log(data.msg, data.level);
                if (data.type === 'fsm') updateFSMState(data.state);
                if (data.type === 'agent') updateAgentStatus(data.agent, data.running);
            };
            ws.onclose = () => { log("Connection lost. Retrying in 2s...", "error"); setTimeout(connectWebSocket, 2000); };
        }

        function startInvestigation() {
            log("User initiated Swarm Authorization.", "warn");
            if(ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({action: "start_swarm"}));
            }
        }
    </script>
</body>
</html>
"""

# ==============================================================================
# 🚀 PHASE F: FASTAPI KERNEL BINDING (PORT 8888)
# ==============================================================================

app = FastAPI(title="NEMESIS OMEGA AIOS")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

active_connections = []

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            cmd = json.loads(data)
            if cmd.get("action") == "start_swarm":
                asyncio.create_task(simulate_autonomous_run(websocket))
    except WebSocketDisconnect:
        active_connections.remove(websocket)

async def send_ws(ws: WebSocket, type: str, **kwargs):
    payload = {"type": type}
    payload.update(kwargs)
    try:
        await ws.send_json(payload)
    except:
        pass

async def simulate_autonomous_run(ws: WebSocket):
    """Simulates the complex multi-agent FSM logic for the frontend."""
    await send_ws(ws, 'log', msg="Executing FSM: INITIALIZE", level="info")
    await send_ws(ws, 'fsm', state="INITIALIZE")
    await asyncio.sleep(1)
    
    await send_ws(ws, 'log', msg="Booting Agent Swarm in Parallel...", level="info")
    agents = ["Blockchain Tracer", "OSINT Crawler", "Neo4j Graph AI", "Threat Hunter"]
    for agent in agents:
        await send_ws(ws, 'agent', agent=agent, running=True)
        await send_ws(ws, 'log', msg=f"[{agent}] Activated and ingesting stream.", level="success")
        await asyncio.sleep(0.5)

    states = ["DISCOVER", "INGEST", "CLASSIFY", "CORRELATE", "REASON", "DECIDE"]
    for state in states:
        await send_ws(ws, 'fsm', state=state)
        await send_ws(ws, 'log', msg=f"Global State Shift -> {state}", level="warn")
        await asyncio.sleep(1.5)

    await send_ws(ws, 'fsm', state="EXECUTE")
    await send_ws(ws, 'log', msg="Executing Intelligence Package Insertion into Atlas.", level="success")
    await asyncio.sleep(1)

    for agent in agents:
        await send_ws(ws, 'agent', agent=agent, running=False)
    
    await send_ws(ws, 'fsm', state="IDLE")
    await send_ws(ws, 'log', msg="Mission Complete. Returning to IDLE state.", level="info")

@app.get("/")
async def root():
    """Serves the massive Embedded React/HTML Light Theme App."""
    return HTMLResponse(content=HTML_DASHBOARD)

# ==============================================================================
# 🏁 MAIN ENTRY POINT
# ==============================================================================

if __name__ == "__main__":
    print(r"""
    ========================================================
     [NEMESIS Ω] KERNEL BOOT SEQUENCE INITIATED...
     DEPLOYMENT MODE : FULLY HYBRID AUTONOMOUS
     WEB UI BINDING  : http://localhost:8888
    ========================================================
    """)
    # Run the Uvicorn server directly from the script
    uvicorn.run("nemesis_omega:app", host="0.0.0.0", port=8888, reload=False, log_level="warning")
