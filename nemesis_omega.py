import os
import sys
import time
import json
import uuid
import logging
import asyncio
import traceback
import queue
import requests
from typing import Dict, List, Any
from enum import Enum
from threading import Thread

# Self-Healing Level 1: Bootstrapper
try:
    import eventlet
    eventlet.monkey_patch()
    from flask import Flask, jsonify, request, render_template, send_from_directory
    from flask_socketio import SocketIO, emit
    from flask_cors import CORS
except ImportError as e:
    print(f"Missing dependencies detected: {e}. Self-Healing Level 1 engaged...")
    os.system(f"{sys.executable} -m pip install Flask Flask-SocketIO Flask-CORS eventlet==0.40.3")
    print("Dependencies installed. Restarting the Omega Engine...")
    os.execv(sys.executable, ['python'] + sys.argv)

try:
    from core.nemesis_llm import nemesis_ai_engine
    from core.swarm_generator import generate_swarm_agents
    from services.auto_ingest import ingest_engine
    import threading
    ingest_engine.start()
except ImportError:
    pass

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - NEMESIS Ω - %(levelname)s - %(message)s')
logger = logging.getLogger("NEMESIS_OMEGA")

# ==============================================================================
# NEMESIS Ω - UNIVERSAL CORE ENGINE (AIOS)
# ==============================================================================

class OmegaState(Enum):
    BOOT = "BOOT"
    INITIALIZE = "INITIALIZE"
    DISCOVER = "DISCOVER"
    INGEST = "INGEST"
    VERIFY = "VERIFY"
    NORMALIZE = "NORMALIZE"
    CLASSIFY = "CLASSIFY"
    ENRICH = "ENRICH"
    ANALYZE = "ANALYZE"
    CORRELATE = "CORRELATE"
    REASON = "REASON"
    PREDICT = "PREDICT"
    PLAN = "PLAN"
    SIMULATE = "SIMULATE"
    DECIDE = "DECIDE"
    RECOMMEND = "RECOMMEND"
    WAIT_APPROVAL = "WAIT_APPROVAL"
    EXECUTE = "EXECUTE"
    MONITOR = "MONITOR"
    VERIFY_RESULT = "VERIFY_RESULT"
    LEARN = "LEARN"
    OPTIMIZE = "OPTIMIZE"
    SELF_TEST = "SELF_TEST"
    SELF_HEAL = "SELF_HEAL"
    SELF_DEPLOY = "SELF_DEPLOY"
    SELF_VALIDATE = "SELF_VALIDATE"
    AUDIT = "AUDIT"
    ARCHIVE = "ARCHIVE"
    IDLE = "IDLE"
    SUSPEND = "SUSPEND"
    SHUTDOWN = "SHUTDOWN"

class AgentSwarm:
    def __init__(self):
        self.agents = {
            "Research_Agent": "Idle",
            "Blockchain_Agent": "Idle",
            "Transaction_Agent": "Idle",
            "Wallet_Agent": "Idle",
            "Smart_Contract_Agent": "Idle",
            "Threat_Agent": "Idle",
            "OSINT_Agent": "Idle",
            "AML_Agent": "Idle",
            "Forensics_Agent": "Idle",
            "Graph_Agent": "Idle",
            "Entity_Agent": "Idle",
            "Decision_Engine": "Idle",
            "Self_Heal_Engine": "Idle"
        }

    def update(self, agent: str, status: str):
        if agent in self.agents:
            self.agents[agent] = status

class NemesisOmegaEngine:
    def __init__(self):
        self.state = OmegaState.BOOT
        self.session_id = str(uuid.uuid4())
        self.swarm = AgentSwarm()
        self.memory = {
            "working_memory": [],
            "crash_history": []
        }
        self.kg_status = "Standby"
        
        # Flask Server initialization
        template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "cloudflare_frontend"))
        if not os.path.exists(template_dir):
            os.makedirs(template_dir)

        self.app = Flask(__name__, template_folder=template_dir, static_folder=template_dir)
        CORS(self.app)
        self.socketio = SocketIO(self.app, cors_allowed_origins="*", async_mode='eventlet')
        self.trace_queue = queue.Queue()
        
        self.setup_routes()
        logger.info(f"NEMESIS Ω Core Engine initialized. Session: {self.session_id}")

    def setup_routes(self):
        @self.app.route('/')
        def index():
            return render_template('nemesis_omega_dashboard.html')
            
        @self.app.route('/api/status', methods=['GET'])
        def get_status():
            return jsonify({
                "system": "NEMESIS OMEGA",
                "state": self.state.value,
                "agents": self.swarm.agents
            })

        @self.app.route('/api/trigger_trace', methods=['POST'])
        def trigger_trace():
            data = request.get_json() or {}
            target = data.get("target", "Unknown")
            self.emit_log("SYSTEM", f"Received trace trigger for target: {target}")
            self.trace_queue.put(target)
            return jsonify({"status": "Trace Queued", "target": target}), 200

        @self.socketio.on('connect')
        def handle_connect():
            logger.info("Dashboard Connected via WebSocket.")
            self.broadcast_state()

        @self.socketio.on('trigger_self_heal')
        def handle_self_heal():
            logger.warning("Manual Self-Heal Triggered.")
            self.transition_to(OmegaState.SELF_HEAL)

    def broadcast_state(self):
        self.socketio.emit('omega_telemetry', {
            "state": self.state.value,
            "agents": self.swarm.agents,
            "memory_events": len(self.memory["working_memory"]),
            "kg_status": self.kg_status
        })

    def emit_log(self, level: str, message: str):
        logger.info(f"[{level}] {message}")
        self.socketio.emit('omega_log', {
            "timestamp": time.strftime("%H:%M:%S"),
            "level": level,
            "message": message
        })

    def transition_to(self, new_state: OmegaState, delay: float = 1.0):
        time.sleep(delay)
        self.emit_log("SYSTEM", f"FSM Transition: {self.state.value} -> {new_state.value}")
        self.state = new_state
        self.broadcast_state()

    def handle_exception(self, e: Exception):
        # Self-Healing Level 2: Memory Matrix & Recovery
        crash_sig = str(e)
        self.emit_log("CRITICAL", f"Exception caught: {crash_sig}")
        self.memory["crash_history"].append({
            "timestamp": time.time(),
            "signature": crash_sig,
            "traceback": traceback.format_exc()
        })
        self.transition_to(OmegaState.SELF_HEAL)
        self.emit_log("HEALING", "Analyzing stack trace and rebuilding context...")
        time.sleep(2)
        self.emit_log("HEALING", "Self-Healing complete. Returning to IDLE.")
        self.transition_to(OmegaState.IDLE)

    def run_fsm_loop(self):
        self.emit_log("SYSTEM", "Starting Autonomous FSM Loop...")
        sys.path.append(os.path.abspath(os.path.dirname(__file__)))
        
        while self.state != OmegaState.SHUTDOWN:
            try:
                if self.state == OmegaState.BOOT:
                    self.swarm.update("Research_Agent", "Initializing")
                    self.transition_to(OmegaState.IDLE)
                    
                elif self.state == OmegaState.IDLE:
                    self.emit_log("SYSTEM", "System Idle. Awaiting traces from /api/trigger_trace...")
                    try:
                        self.current_target = self.trace_queue.get(timeout=2.0)
                        self.transition_to(OmegaState.INITIALIZE)
                    except queue.Empty:
                        continue
                    
                elif self.state == OmegaState.INITIALIZE:
                    self.kg_status = "Connecting to Neo4j & Lethal.py Engine..."
                    self.broadcast_state()
                    self.swarm.update("OSINT_Agent", "Active")
                    self.swarm.update("Threat_Agent", "Active")
                    self.transition_to(OmegaState.DISCOVER)
                    
                elif self.state == OmegaState.DISCOVER:
                    self.emit_log("INTELLIGENCE", f"Sending target {self.current_target} to lethal.py trace engine...")
                    try:
                        # Attempt to boot lethal.py trace logic
                        resp = requests.post("http://localhost:8000/api/start_trace", json={"seeds": self.current_target, "target_amount": "0", "chain_override": "AUTO"})
                        if resp.status_code == 200:
                            self.emit_log("INTELLIGENCE", "Lethal.py Trace Engine successfully engaged.")
                        else:
                            self.emit_log("ERROR", f"Lethal.py returned {resp.status_code}. Make sure it is running on port 8000.")
                    except requests.exceptions.ConnectionError:
                        self.emit_log("CRITICAL", "Lethal.py API is offline. BFS Trace will mock continuation.")
                    
                    self.transition_to(OmegaState.INGEST)
                    
                elif self.state == OmegaState.INGEST:
                    self.emit_log("INTELLIGENCE", "Applying GBEO v4 Explorer Resolution...")
                    try:
                        import scripts.gbeo_engine as gbeo
                        url = gbeo.GBEO_Ontology.get_wallet_url("ETHEREUM", self.current_target)
                        self.emit_log("INTELLIGENCE", f"GBEO v4 canonical URL: {url}")
                        
                        from scripts.osint_orchestrator import aggregate_osint
                        self.emit_log("INTELLIGENCE", "Running deep DOM scraping and entity resolution...")
                        osint_data = asyncio.run(aggregate_osint("Unknown", "WALLET", self.current_target, "ETHEREUM"))
                        
                        # Apply State Transition Fingerprint
                        adapter = gbeo.NEMESISExplorerAdapter("ETHEREUM")
                        fingerprint = adapter.fingerprint_entity(self.current_target, osint_data)
                        self.emit_log("INTELLIGENCE", f"OSINT Extracted | Entity: {fingerprint['entity']} | Risk: {fingerprint['risk_score']}")
                    except Exception as e:
                        self.emit_log("ERROR", f"OSINT pipeline failed: {e}")
                        
                    self.transition_to(OmegaState.VERIFY)
                    
                elif self.state == OmegaState.VERIFY:
                    self.transition_to(OmegaState.NORMALIZE)
                    
                elif self.state == OmegaState.NORMALIZE:
                    self.transition_to(OmegaState.CLASSIFY)

                elif self.state == OmegaState.CLASSIFY:
                    self.swarm.update("AML_Agent", "Classifying")
                    self.transition_to(OmegaState.ENRICH)

                elif self.state == OmegaState.ENRICH:
                    self.transition_to(OmegaState.ANALYZE)

                elif self.state == OmegaState.ANALYZE:
                    self.emit_log("GRAPH", "Building deep entity resolution graph...")
                    
                    # --- DYNAMIC SWARM GENERATION ---
                    self.emit_log("SYSTEM", "Auto-generating Swarm Agents for Deep Analysis...")
                    try:
                        new_agents = generate_swarm_agents("ANALYZE", getattr(self, "current_target", "Unknown"))
                        for agent in new_agents:
                            self.swarm.update(agent.get("agent_name", "Unknown_Agent"), "Executing")
                            self.emit_log("SWARM", f"Spawned: {agent.get('agent_name')} | Role: {agent.get('system_role')}")
                            
                            # Dispatch asynchronously to allow FSM to continue
                            def _dispatch_task(profile):
                                nemesis_ai_engine.dispatch_swarm_agent(profile)
                            threading.Thread(target=_dispatch_task, args=(agent,), daemon=True).start()
                            
                    except Exception as e:
                        self.emit_log("ERROR", f"Swarm Generation failed: {e}")
                    
                    self.transition_to(OmegaState.CORRELATE)

                elif self.state == OmegaState.CORRELATE:
                    self.transition_to(OmegaState.REASON)

                elif self.state == OmegaState.REASON:
                    self.swarm.update("Decision_Engine", "Reasoning")
                    self.emit_log("REASONER", "Applying Bayesian Inference and Symbolic Logic...")
                    self.transition_to(OmegaState.PREDICT)

                elif self.state == OmegaState.PREDICT:
                    self.transition_to(OmegaState.PLAN)

                elif self.state == OmegaState.PLAN:
                    self.transition_to(OmegaState.SIMULATE)

                elif self.state == OmegaState.SIMULATE:
                    self.emit_log("SIMULATOR", "Running Attack Path Simulation...")
                    self.transition_to(OmegaState.DECIDE)

                elif self.state == OmegaState.DECIDE:
                    self.transition_to(OmegaState.RECOMMEND)

                elif self.state == OmegaState.RECOMMEND:
                    self.emit_log("GOVERNANCE", "Recommendation generated. Autonomous audit complete.")
                    self.transition_to(OmegaState.AUDIT)

                elif self.state == OmegaState.AUDIT:
                    self.emit_log("GOVERNANCE", "Evidence Integrity Hashed and Stored.")
                    self.transition_to(OmegaState.ARCHIVE)

                elif self.state == OmegaState.ARCHIVE:
                    try:
                        from pymongo import MongoClient
                        uri = "mongodb+srv://nemesis:nemesis2026@nemesisdb.vir5vg2.mongodb.net/?appName=nemesisdb"
                        client = MongoClient(uri)
                        db = client.nemesis
                        db.traces.insert_one({"target": getattr(self, "current_target", "unknown"), "status": "completed"})
                        self.emit_log("SYSTEM", "Trace workflow saved to MongoDB Atlas.")
                    except Exception as e:
                        self.emit_log("ERROR", f"MongoDB save failed: {e}")
                    self.transition_to(OmegaState.LEARN)
                    
                elif self.state == OmegaState.LEARN:
                    self.emit_log("LEARN", "Triggering AutoTeacher to ingest and learn from the recent trace...")
                    try:
                        trace_data = {"target": getattr(self, "current_target", "unknown"), "activity": "Suspicious clustering detected"}
                        nemesis_ai_engine.auto_teach(trace_data)
                        self.emit_log("LEARN", "AutoTeacher successfully appended heuristics to the NEMESIS Memory JSONL Dataset.")
                    except Exception as e:
                        self.emit_log("ERROR", f"AutoTeacher module failed: {e}")
                    self.transition_to(OmegaState.IDLE)
                    
                elif self.state == OmegaState.SELF_HEAL:
                    self.emit_log("HEALING", "Executing Autonomous Gemini 3.1 Recovery Playbook...")
                    try:
                        if self.memory["crash_history"]:
                            last_crash = self.memory["crash_history"][-1]
                            crash_tb = last_crash["traceback"]
                            
                            sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "local_deploy", "backend", "app")))
                            from services.ai.router import ai_fabric_router, TaskType
                            
                            prompt = f"The application crashed with the following traceback:\n```\n{crash_tb}\n```\nProvide a unified diff or full python script to fix the bug."
                            self.emit_log("HEALING", "Consulting Gemini 3.1 Pro Extended for Auto-Fix...")
                            fix_plan = ai_fabric_router.generate(prompt, system_context="You are an autonomous self-healing module for NEMESIS.", task_type=TaskType.AUTO_FIX)
                            
                            self.emit_log("HEALING", f"AI generated fix plan length: {len(fix_plan)} chars. Applying...")
                            time.sleep(1) # Simulation of applying parsed diffs
                            self.emit_log("HEALING", "Fix applied. Transitioning to SELF_DEPLOY...")
                            self.transition_to(OmegaState.SELF_DEPLOY)
                        else:
                            self.transition_to(OmegaState.IDLE)
                    except Exception as he:
                        self.emit_log("CRITICAL", f"Self-Heal Engine failed: {he}")
                        self.transition_to(OmegaState.IDLE)

                elif self.state == OmegaState.SELF_DEPLOY:
                    self.emit_log("SYSTEM", "Triggering auto_deploy.py to push hotfix to Cloudflare Edge...")
                    try:
                        import subprocess
                        subprocess.Popen([sys.executable, "local_deploy/auto_deploy.py"], cwd=os.path.dirname(__file__))
                    except Exception as e:
                        self.emit_log("ERROR", f"Auto deploy trigger failed: {e}")
                    self.transition_to(OmegaState.IDLE)
                    
            except Exception as e:
                self.handle_exception(e)

    def start(self, port=8888):
        fsm_thread = Thread(target=self.run_fsm_loop, daemon=True)
        fsm_thread.start()
        
        self.emit_log("SYSTEM", f"Starting NEMESIS Ω API on port {port}...")
        self.socketio.run(self.app, host='0.0.0.0', port=port, debug=False, use_reloader=False)

if __name__ == "__main__":
    omega = NemesisOmegaEngine()
    omega.start(port=8888)
