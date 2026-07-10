import os
import sys
import subprocess
import time
import json
import hashlib
from datetime import datetime
from threading import Thread

# ==========================================
# LEVEL 1: SELF-BOOTSTRAPPING SUBSYSTEM
# ==========================================
def bootstrap_environment():
    print("[LEVEL 1] Self-Bootstrapping Subsystem Active.")
    required_packages = {
        "google-genai": "google.genai",
        "psutil": "psutil",
        "python-dotenv": "dotenv",
        "fastapi": "fastapi",
        "uvicorn": "uvicorn",
        "motor": "motor",
        "pymongo": "pymongo",
        "passlib[bcrypt]": "passlib"
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

bootstrap_environment()

import psutil
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Load Environment and Keys
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("CRITICAL: GEMINI_API_KEY is missing from .env. The Self-Programming Engine cannot function.")
    sys.exit(1)

# Handle comma-separated keys or single quotes
clean_key = GEMINI_API_KEY.replace("'", "").replace('"', '').split(",")[0].strip()
client = genai.Client(api_key=clean_key)

# ==========================================
# CORE CONFIGURATIONS
# ==========================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
COGNITION_DB = os.path.join(BASE_DIR, "nemesis_cognition.json")
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
APP_SCRIPT = os.path.join(BACKEND_DIR, "app.py")

# ==========================================
# LEVEL 4: SELF-SECURITY SUBSYSTEM
# ==========================================
class SelfSecuritySubsystem:
    PROTECTED_FILES = [
        "autonomous_agent.py",
        ".env",
        ".git",
        "run_nemesis.py"
    ]
    
    @staticmethod
    def is_modification_allowed(file_path: str) -> bool:
        """Acts as an interceptor. Rejects patches to critical infrastructure files."""
        normalized_path = os.path.normpath(file_path).lower()
        for protected in SelfSecuritySubsystem.PROTECTED_FILES:
            if protected.lower() in normalized_path:
                print(f"[SECURITY] BLOCKED: LLM attempted to modify protected file: {file_path}")
                return False
        return True

    @staticmethod
    def monitor_resources():
        """Monitors system resources. If RAM > 90%, issues a restart signal."""
        ram_percent = psutil.virtual_memory().percent
        if ram_percent > 90:
            print(f"[SECURITY] CRITICAL: Memory usage at {ram_percent}%. Potential leak. Triggering autonomous restart.")
            return True
        return False

# ==========================================
# LEVEL 2: SELF-LEARNING MEMORY MATRIX
# ==========================================
class SelfLearningMemoryMatrix:
    @staticmethod
    def _load_db():
        if not os.path.exists(COGNITION_DB):
            return {}
        try:
            with open(COGNITION_DB, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}

    @staticmethod
    def _save_db(data):
        with open(COGNITION_DB, "w") as f:
            json.dump(data, f, indent=4)

    @staticmethod
    def hash_error(stderr_trace: str) -> str:
        """Creates a stable SHA-256 hash of the crash signature."""
        lines = [line.strip() for line in stderr_trace.split('\n') if "File" in line or "Error:" in line]
        signature = "\n".join(lines[-5:]) # Focus on the actual final traceback lines
        return hashlib.sha256(signature.encode()).hexdigest()

    @staticmethod
    def lookup_resolution(crash_hash: str):
        db = SelfLearningMemoryMatrix._load_db()
        return db.get(crash_hash)

    @staticmethod
    def store_resolution(crash_hash: str, patch_data: list, description: str):
        db = SelfLearningMemoryMatrix._load_db()
        db[crash_hash] = {
            "resolved_at": datetime.utcnow().isoformat(),
            "description": description,
            "patch": patch_data
        }
        SelfLearningMemoryMatrix._save_db(db)
        print(f"[LEVEL 2] Learned & Cached resolution for crash signature {crash_hash[:8]}")

# ==========================================
# LEVEL 3: SELF-PROGRAMMING ENGINE
# ==========================================
class SelfProgrammingEngine:
    @staticmethod
    def map_project_context() -> str:
        """Gathers the current codebase context for the LLM to understand the architecture."""
        context = []
        ignore_dirs = {".git", "__pycache__", "venv", "node_modules", "archive", "data"}
        
        for root, dirs, files in os.walk(BASE_DIR):
            dirs[:] = [d for d in dirs if d not in ignore_dirs]
            for file in files:
                if file.endswith(".py") or file.endswith(".html"):
                    filepath = os.path.join(root, file)
                    rel_path = os.path.relpath(filepath, BASE_DIR)
                    try:
                        with open(filepath, "r", encoding="utf-8") as f:
                            content = f.read()
                            # Limit file context to 1500 lines per file to save tokens
                            lines = content.split('\n')
                            if len(lines) > 1500:
                                content = "\n".join(lines[:1500]) + "\n...[TRUNCATED]..."
                            context.append(f"--- FILE: {rel_path} ---\n{content}\n")
                    except Exception:
                        pass
        return "\n".join(context)

    @staticmethod
    def diagnose_and_patch(stderr: str) -> list:
        print("[LEVEL 3] Self-Programming Engine: Analyzing crash dump...")
        
        context = SelfProgrammingEngine.map_project_context()
        
        prompt = f"""You are the NEMESIS Autonomous OS Self-Programming Engine.
The master application has crashed. You must analyze the traceback, identify the faulty Python code, and output a strict JSON patch to fix it.

CRASH TRACEBACK:
{stderr}

SYSTEM CODEBASE CONTEXT:
{context}

RULES:
1. Provide the fix as a JSON array of file modifications.
2. Output ONLY the raw JSON array. Do not wrap it in markdown code blocks (no ```json). Do not include any conversational text.
3. Use absolute paths or paths relative to the project root for 'file_path'.
4. Ensure 'new_content' contains the FULL updated code for that file. DO NOT output partial snippets. Output the entire rewritten file content.

EXPECTED JSON FORMAT:
[
  {{
    "file_path": "backend/app.py",
    "new_content": "import os\\nfrom fastapi import FastAPI..."
  }}
]
"""
        
        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt
            )
            json_text = response.text.strip()
            if json_text.startswith("```json"):
                json_text = json_text.replace("```json", "", 1)
            if json_text.endswith("```"):
                json_text = json_text[:-3]
            
            patches = json.loads(json_text.strip())
            return patches
        except Exception as e:
            print(f"[!] AI Patch Generation Failed: {e}")
            return None

    @staticmethod
    def apply_patch(patches: list) -> bool:
        if not patches:
            return False
            
        success = True
        for patch in patches:
            file_path = patch.get("file_path", "")
            new_content = patch.get("new_content", "")
            
            abs_path = os.path.abspath(os.path.join(BASE_DIR, file_path))
            
            if not SelfSecuritySubsystem.is_modification_allowed(abs_path):
                success = False
                continue
                
            try:
                # Backup original
                if os.path.exists(abs_path):
                    with open(abs_path + ".bak", "w", encoding="utf-8") as f:
                        with open(abs_path, "r", encoding="utf-8") as orig:
                            f.write(orig.read())
                
                # Write patch
                with open(abs_path, "w", encoding="utf-8") as f:
                    f.write(new_content)
                print(f"[+] Autonomous Patch Applied successfully to: {file_path}")
            except Exception as e:
                print(f"[!] Failed to write patch to {file_path}: {e}")
                success = False
        return success

# ==========================================
# LEVEL 5: NEMESIS AUTONOMOUS ORCHESTRATOR
# ==========================================
class NemesisAutonomousOrchestrator:
    def __init__(self):
        self.running = True
        self.process = None

    def stream_output(self, pipe, prefix):
        try:
            for line in iter(pipe.readline, ''):
                if line:
                    print(f"[{prefix}] {line.strip()}")
        except Exception:
            pass

    def boot_sequence(self):
        print("\n=====================================================")
        print(" 🧠 NEMESIS AUTONOMOUS OS INITIALIZING")
        print("=====================================================\n")
        
        while self.running:
            if SelfSecuritySubsystem.monitor_resources():
                print("[*] Triggering preventative restart due to resource exhaustion...")
                time.sleep(2)
                continue
                
            print("[LEVEL 5] Booting Execution Layer (backend/app.py)...")
            self.process = subprocess.Popen(
                [sys.executable, APP_SCRIPT],
                cwd=BACKEND_DIR,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            
            # Stream stdout in background
            Thread(target=self.stream_output, args=(self.process.stdout, "APP-STDOUT"), daemon=True).start()
            
            # Capture stderr for analysis
            stderr_capture = []
            def capture_stderr(pipe, storage):
                for line in iter(pipe.readline, ''):
                    if line:
                        print(f"[APP-STDERR] {line.strip()}")
                        storage.append(line)
            
            err_thread = Thread(target=capture_stderr, args=(self.process.stderr, stderr_capture), daemon=True)
            err_thread.start()
            
            self.process.wait()
            err_thread.join()
            
            exit_code = self.process.returncode
            if exit_code != 0:
                print(f"\n[CRITICAL] Application crashed with exit code {exit_code}.")
                full_stderr = "".join(stderr_capture)
                
                if not full_stderr.strip():
                    print("[!] Process exited abnormally but no stderr was captured. Retrying in 5 seconds...")
                    time.sleep(5)
                    continue

                crash_hash = SelfLearningMemoryMatrix.hash_error(full_stderr)
                print(f"[LEVEL 5] Crash Signature Hash: {crash_hash[:8]}")
                
                # Memory Lookup
                cached_resolution = SelfLearningMemoryMatrix.lookup_resolution(crash_hash)
                if cached_resolution:
                    print("[LEVEL 2] Known crash detected! Pulling fix from Self-Learning Memory...")
                    SelfProgrammingEngine.apply_patch(cached_resolution["patch"])
                    print("[*] Restarting system in 3 seconds...")
                    time.sleep(3)
                    continue
                
                # Unknown Crash -> Trigger AI Programming
                print("[LEVEL 3] Unknown crash detected. Engaging Self-Programming Engine (LLM)...")
                patch_data = SelfProgrammingEngine.diagnose_and_patch(full_stderr)
                
                if patch_data:
                    success = SelfProgrammingEngine.apply_patch(patch_data)
                    if success:
                        SelfLearningMemoryMatrix.store_resolution(crash_hash, patch_data, "Autonomous bug fix applied.")
                    else:
                        print("[!] Patch execution failed or blocked by Security Subsystem.")
                else:
                    print("[!] AI failed to generate a valid patch.")
                
                print("[*] Restarting system in 5 seconds...")
                time.sleep(5)
            else:
                print("[*] Application exited gracefully. Shutting down Autonomous Orchestrator.")
                self.running = False

if __name__ == "__main__":
    try:
        orchestrator = NemesisAutonomousOrchestrator()
        orchestrator.boot_sequence()
    except KeyboardInterrupt:
        print("\n[*] Manual Override Detected. Shutting down NEMESIS Autonomous OS.")
        sys.exit(0)
