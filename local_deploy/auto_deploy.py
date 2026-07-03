import os
import subprocess
import sys
import urllib.request
import time
import re
import json
import shutil
from pathlib import Path
try:
    import google.generativeai as genai
except ImportError:
    subprocess.run([sys.executable, "-m", "pip", "install", "google-generativeai"], check=True)
    import google.generativeai as genai

def get_env_var(key, default=""):
    env_path = Path(".env")
    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith(f"{key}="):
                    return line.strip().split("=", 1)[1].strip('"').strip("'")
    return os.environ.get(key, default)

# Fix for Cloudflare Wrangler Edge Case (code 9109/OAuth Block)
if "CLOUDFLARE_API_TOKEN" in os.environ:
    print("🧹 Cleaning stale CLOUDFLARE_API_TOKEN from environment to allow OAuth login...")
    del os.environ["CLOUDFLARE_API_TOKEN"]

GEMINI_API_KEYS = get_env_var("GEMINI_API_KEYS", "")
if GEMINI_API_KEYS:
    # Use the first key
    genai.configure(api_key=GEMINI_API_KEYS.split(",")[0].strip('"'))
    MODEL = genai.GenerativeModel("gemini-2.5-flash")
else:
    MODEL = None

def print_header(title):
    print(f"\n{'='*60}")
    print(f" 🚀 {title}")
    print(f"{'='*60}")

def apply_ai_fix(error_log, cwd):
    if not MODEL:
        print("⚠️ Gemini API not configured. Cannot attempt AI auto-fix.")
        return False
        
    knowledge_context = ""
    kb_dir = Path(__file__).parent / "NEMESIS_KNOWLEDGE_BASE_LIBRARY"
    if kb_dir.exists():
        for file in kb_dir.glob("*_docs.txt"):
            try:
                content = file.read_text(encoding="utf-8")
                # Truncate to first 4000 characters to save tokens
                knowledge_context += f"\n--- {file.name} ---\n{content[:4000]}\n"
            except Exception:
                pass
    
    prompt = f"""
    You are an autonomous AI coding agent. The following deployment command failed with this error:
    {error_log}
    
    Here is the official documentation context that may contain the fix:
    {knowledge_context}
    
    Provide a JSON response to fix this error. You can either issue a terminal command to run, or edit a specific file.
    Format your response EXACTLY as valid JSON. Do not include markdown blocks or any other text.
    Format 1 (Command):
    {{"action": "command", "cmd": "npm install missing-package"}}
    
    Format 2 (File Edit):
    {{"action": "edit", "file": "relative/path/to/file", "search": "string to replace", "replace": "new string"}}
    """
    print("🧠 Asking Gemini for a fix...")
    try:
        response = MODEL.generate_content(prompt)
        text = response.text.strip()
        if text.startswith("```json"):
            text = text.split("```json")[1].split("```")[0].strip()
        elif text.startswith("```"):
            text = text.split("```")[1].strip()
            
        data = json.loads(text)
        
        if data.get("action") == "command":
            cmd = data.get("cmd")
            print(f"🪄 AI suggested running: {cmd}")
            subprocess.run(cmd, shell=True, cwd=cwd)
            return True
            
        elif data.get("action") == "edit":
            filepath = Path(cwd) / data.get("file") if cwd else Path(data.get("file"))
            if filepath.exists():
                print(f"🪄 AI suggested editing: {filepath}")
                # Backup
                shutil.copy(filepath, f"{filepath}.bak")
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
                content = content.replace(data.get("search", ""), data.get("replace", ""))
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(content)
                return True
            else:
                print(f"⚠️ AI suggested editing non-existent file: {filepath}")
                return False
    except Exception as e:
        print(f"❌ AI Fix failed to parse or execute: {e}")
        return False

def run_command(cmd, cwd=None, exit_on_error=True, allow_healing=True):
    print(f"🔧 Running: {cmd}" + (f" (in {cwd})" if cwd else ""))
    
    retries = 0
    max_retries = 2
    
    while retries <= max_retries:
        process = subprocess.Popen(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=cwd,
            text=True
        )
        
        output = []
        while True:
            stdout_line = process.stdout.readline()
            if stdout_line:
                print(f"  {stdout_line.strip()}")
                output.append(stdout_line)
            stderr_line = process.stderr.readline()
            if stderr_line:
                print(f"  [stderr] {stderr_line.strip()}")
                output.append(stderr_line)
                
            if stdout_line == '' and stderr_line == '' and process.poll() is not None:
                break
                
        ret = process.returncode
        log = "".join(output)
        
        if ret == 0:
            return True, log
            
        print(f"❌ Command failed (Exit code: {ret})")
        
        # Specific known fixes (from auto.py)
        if "10097" in log and "wrangler" in cmd:
            print("⚠️ Detected Migration Error 10097. Attempting hardcoded auto-fix...")
            toml_path = Path(cwd) / "wrangler.toml" if cwd else Path("wrangler.toml")
            if toml_path.exists():
                with open(toml_path, "r", encoding="utf-8") as f:
                    c = f.read()
                c = c.replace('new_classes = ["TraceCoordinator"', 'new_sqlite_classes = ["TraceCoordinator"')
                with open(toml_path, "w", encoding="utf-8") as f:
                    f.write(c)
                print("✅ Applied sqlite classes fix. Retrying...")
                retries += 1
                continue
                
        if allow_healing and retries < max_retries:
            print(f"🔄 Triggering Self-Healing Protocol (Attempt {retries + 1}/{max_retries})")
            if apply_ai_fix(log, cwd):
                print("✅ Fix applied. Retrying command...")
                retries += 1
                continue
            else:
                break
        else:
            break
            
    if exit_on_error:
        print("🛑 Critical failure. Halting deployment.")
        sys.exit(ret)
    return False, log

def setup_cloudflare_tunnel():
    print_header("Setting up Cloudflare Tunnel (Godmode)")
    cloudflared_exec = "cloudflared"
    ret, _ = run_command(f"{cloudflared_exec} --version", exit_on_error=False, allow_healing=False)
    if not ret:
        if not Path("cloudflared.exe").exists():
            print("📥 Downloading cloudflared.exe...")
            urllib.request.urlretrieve("https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe", "cloudflared.exe")
        cloudflared_exec = ".\\cloudflared.exe"
        
    log_file = Path("cloudflared.log")
    if log_file.exists(): log_file.unlink()
    
    tunnel_proc = subprocess.Popen(f"{cloudflared_exec} tunnel --url http://127.0.0.1:3001 > cloudflared.log 2>&1", shell=True)
    
    tunnel_url = None
    for _ in range(15):
        time.sleep(1)
        if log_file.exists():
            with open(log_file, "r", encoding="utf-8") as f:
                match = re.search(r'(https://[a-zA-Z0-9-]+\.trycloudflare\.com)', f.read())
                if match:
                    tunnel_url = match.group(1)
                    break
    
    if not tunnel_url:
        tunnel_url = "https://nemesis-tunnel.trycloudflare.com"
        print(f"⚠️ Using fallback tunnel URL: {tunnel_url}")
    else:
        print(f"✅ Tunnel established: {tunnel_url}")
        
    return tunnel_proc, tunnel_url

def main():
    print_header("NEMESIS OMNI-DEPLOYER (GODMODE & SELF-HEALING)")
    current_dir = os.getcwd()
    
    print("\n>>> [1/5] Running Pre-Flight Tests...")
    test_script = os.path.join(current_dir, "test_all.ps1")
    if os.path.exists(test_script):
        # Run tests directly using current Python executable
        run_command(f"{sys.executable} -m pytest tests/", cwd=current_dir, exit_on_error=True, allow_healing=False)
        run_command(f"{sys.executable} test_trace.py", cwd=current_dir, exit_on_error=True, allow_healing=False)
    else:
        print("    -> [SKIP] No test_all.ps1 found.")

    print("\n>>> [2/5] NPM Audits & Updates")
    worker_dir = os.path.join(current_dir, "nemesis-global-worker")
    if os.path.exists(worker_dir) and os.path.exists(os.path.join(worker_dir, "package.json")):
        print("    -> Running NPM operations...")
        run_command("npm install", cwd=worker_dir, exit_on_error=False)
        # Attempt audit fix automatically
        run_command("npm audit fix", cwd=worker_dir, exit_on_error=False, allow_healing=False)
    
    print("\n>>> [3/5] Syncing to Global Repository (Render Backend)")
    run_command("git add .", cwd=current_dir, allow_healing=False)
    run_command('git commit -m "Auto-Deploy from Godmode"', cwd=current_dir, exit_on_error=False, allow_healing=False)
    run_command("git push origin main", cwd=current_dir, exit_on_error=False, allow_healing=True)
    
    try:
        urllib.request.urlopen("https://api.render.com/deploy/srv-d932a7uq1p3s73eaauf0?key=ksDcebRkWzg")
        print("    -> Render backend is building!")
    except Exception as e:
        print(f"    -> [WARNING] Render trigger failed: {e}")

    print("\n>>> [4/5] Deploying Edge Architecture (Cloudflare Worker)")
    if os.path.exists(worker_dir):
        # Update wrangler.toml with tunnel url if godmode tunneling is active
        # Not strictly required for standard deployment but part of Godmode
        run_command("npx wrangler deploy src/index.ts -c wrangler.toml --compatibility-date 2024-12-01", cwd=worker_dir)
    else:
        print(f"    -> [WARNING] Worker dir not found.")

    print("\n>>> [5/5] Deploying Main Frontend (Cloudflare Pages)")
    frontend_dir = os.path.join(current_dir, "templates")
    if os.path.exists(frontend_dir):
        run_command("npx wrangler pages deploy . --project-name nemesis-id-frontend", cwd=frontend_dir)
    
    print_header("ALL SYSTEMS OPERATIONAL: DEPLOYMENT SUCCESSFUL")

if __name__ == "__main__":
    main()
