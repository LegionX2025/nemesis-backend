import os
import sys
import time
import subprocess
import urllib.request
import urllib.error
import json
import re
from colorama import init, Fore, Style
from dotenv import load_dotenv

init(autoreset=True)
load_dotenv()

# We use google.generativeai for the AI Auto-Fixer
try:
    import google.generativeai as genai
except ImportError:
    print(f"{Fore.RED}[ERROR] google.generativeai is missing. Run: pip install google-generativeai")
    sys.exit(1)

# Configure Gemini
api_keys_raw = os.getenv("GEMINI_API_KEYS", "")
api_keys = [k.strip().replace('"', '').replace("'", "") for k in api_keys_raw.split(",") if k.strip()]
if not api_keys:
    print(f"{Fore.RED}[ERROR] No GEMINI_API_KEYS found in .env")
    sys.exit(1)
genai.configure(api_key=api_keys[0])

RENDER_HOOK = "https://api.render.com/deploy/srv-d9a6s967r5hc73c91250?key=UO6u1JaL-zk"

ENDPOINTS = [
    ("Render Tracer UI", "https://projectnemesis.onrender.com/tracer.html"),
    ("Render API Status", "https://projectnemesis.onrender.com/api/system/status"),
    ("Vercel Tracer UI", "https://nemesisfinal.vercel.app/tracer.html"),
    ("Vercel API Status", "https://nemesisfinal.vercel.app/api/system/status"),
    ("Cloudflare Tracer UI", "https://nemesis-frontend.pages.dev/tracer.html"),
    ("Cloudflare API Status", "https://nemesis-frontend.pages.dev/api/system/status"),
]

def trigger_deployments():
    print(f"\n{Fore.CYAN}{Style.BRIGHT}=== 1. INITIATING MULTI-CLOUD DEPLOYMENT ==={Style.RESET_ALL}")
    try:
        print("Fixing Git large file cache before pushing...")
        # Write .gitignore rules to exclude massive data, temp scripts, and unused archives
        with open(".gitignore", "a") as f:
            f.write("\ndata/*.json\ndata/*.jsonl\nworkers/node_modules/\nscripts/\narchive_unused/\n")
        
        # Untrack the massive files and temporary directories that are breaking GitHub push or shouldn't be deployed
        subprocess.run(["git", "rm", "-r", "--cached", "data/"], check=False, capture_output=True)
        subprocess.run(["git", "rm", "-r", "--cached", "workers/node_modules/"], check=False, capture_output=True)
        subprocess.run(["git", "rm", "-r", "--cached", "scripts/"], check=False, capture_output=True)
        subprocess.run(["git", "rm", "-r", "--cached", "archive_unused/"], check=False, capture_output=True)
        
        print("Pushing to GitHub (Triggers Vercel & Cloudflare)...")
        subprocess.run(["git", "add", "."], check=True)
        subprocess.run(["git", "commit", "-m", "Auto-Deploy: Self-Healing Pipeline Updates"], check=False)
        subprocess.run(["git", "push"], check=True)
        print(f"{Fore.GREEN}[SUCCESS] GitHub Push Complete.")
        
        print("Triggering Render Webhook...")
        req = urllib.request.Request(RENDER_HOOK, method="POST")
        with urllib.request.urlopen(req) as response:
            if response.status in [200, 201, 202]:
                print(f"{Fore.GREEN}[SUCCESS] Render Deployment Triggered.")
    except Exception as e:
        print(f"{Fore.RED}[ERROR] Deployment Trigger Failed: {e}")
        # Soft fail: continue trying

def auto_heal(endpoint_name, url, status_code, error_body):
    print(f"\n{Fore.MAGENTA}{Style.BRIGHT}=== 3. GEMINI AI AUTO-HEAL PROTOCOL ==={Style.RESET_ALL}")
    print(f"Analyzing {status_code} error from {endpoint_name}...")
    
    prompt = f"""
    You are an autonomous AI maintaining a FastAPI multi-cloud system (nemesis_core.py).
    The production endpoint {url} ({endpoint_name}) crashed with HTTP {status_code}.
    Here is the error body/logs:
    {error_body[:2000]}
    
    To auto-heal, output a JSON block with EXACTLY this schema:
    ```json
    {{
       "file_path": "nemesis_core.py",
       "full_content": "import sys..."
    }}
    ```
    You must output the ENTIRE updated file content in `full_content` so the system can blindly overwrite it.
    If you don't know the fix, output "NO_FIX_AVAILABLE".
    """
    try:
        print(f"{Fore.CYAN}[GEMINI OMEGA] Analyzing logs for Code Generation & Auto-Fix...")
        
        # Multi-Model Cascade
        # The legacy google.generativeai SDK throws 404 for deprecated or experimental models.
        # We must dynamically query `list_models()` and pick the most advanced stable model available.
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        priority_models = [
            'models/gemini-1.5-pro-latest',
            'models/gemini-1.5-pro',
            'models/gemini-1.5-flash',
            'models/gemini-pro'
        ]
        
        valid_model = "gemini-1.5-flash" # Safe fallback
        for pm in priority_models:
            if pm in available_models:
                valid_model = pm.replace("models/", "")
                break
            
        print(f"{Fore.MAGENTA}[GEMINI ENGINE] Engaging model: {valid_model}")
        model = genai.GenerativeModel(valid_model)
        
        print(f"{Fore.YELLOW}[GEMINI] Generating code fix and architecture patches...")
        response = model.generate_content(prompt)
        text = response.text
        
        if "NO_FIX_AVAILABLE" in text:
            print(f"{Fore.RED}[GEMINI] Unable to determine fix.")
            return False
            
        json_match = re.search(r'```json\n(.*?)\n```', text, re.DOTALL)
        if json_match:
            fix_data = json.loads(json_match.group(1))
            file_path = fix_data.get("file_path")
            content = fix_data.get("full_content")
            
            if file_path and content:
                print(f"{Fore.YELLOW}[GEMINI] Applying Auto-Heal patch to {file_path}...{Style.RESET_ALL}")
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                print(f"{Fore.GREEN}[SUCCESS] Patch applied! Restarting deployment loop.")
                return True
        else:
            print(f"{Fore.RED}[GEMINI] Response format invalid. Could not parse JSON.")
            print(text[:500])
            return False
            
    except Exception as e:
        print(f"{Fore.RED}Gemini AI Auto-Heal failed: {e}")
        return False

def monitor_deployments():
    print(f"\n{Fore.CYAN}{Style.BRIGHT}=== 2. MONITORING MULTI-CLOUD HEALTH ==={Style.RESET_ALL}")
    print("Waiting 20 seconds for initial container allocation...\n")
    time.sleep(20)
    
    max_retries = 20
    failed_endpoint = None
    
    for attempt in range(1, max_retries + 1):
        print(f"{Fore.MAGENTA}--- Health Check Attempt {attempt}/{max_retries} ---")
        all_online = True
        
        for name, url in ENDPOINTS:
            try:
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=10) as response:
                    print(f"{Fore.GREEN}[ONLINE] {name} (HTTP {response.status})")
            except urllib.error.HTTPError as e:
                print(f"{Fore.RED}[ERROR] {name} returned HTTP {e.code}")
                all_online = False
                failed_endpoint = (name, url, e.code, e.read().decode('utf-8', errors='ignore'))
            except urllib.error.URLError as e:
                print(f"{Fore.YELLOW}[BUILDING] {name} unreachable: {e.reason}")
                all_online = False
            except Exception as e:
                print(f"{Fore.RED}[OFFLINE] {name} error: {e}")
                all_online = False
                
        if all_online:
            print(f"\n{Fore.GREEN}{Style.BRIGHT}★ ALL CLOUDS FULLY DEPLOYED AND ONLINE! ★")
            
            print(f"\n{Fore.CYAN}{Style.BRIGHT}==========================================")
            print(f"{Fore.CYAN}       🚀 NEMESIS LIVE DEPLOYMENTS        ")
            print(f"{Fore.CYAN}=========================================={Style.RESET_ALL}")
            print(f"{Fore.MAGENTA}► CLOUDFLARE (Primary Frontend):{Style.RESET_ALL}")
            print(f"  Tracer UI:  {Fore.BLUE}https://nemesis-frontend.pages.dev/tracer.html{Style.RESET_ALL}")
            print(f"  Nemesis ID: {Fore.BLUE}https://nemesis-frontend.pages.dev/nemesis_id.html{Style.RESET_ALL}")
            
            print(f"\n{Fore.MAGENTA}► VERCEL (Primary Backend & Backup Frontend):{Style.RESET_ALL}")
            print(f"  Tracer UI:  {Fore.BLUE}https://nemesisfinal.vercel.app/tracer.html{Style.RESET_ALL}")
            print(f"  API Engine: {Fore.BLUE}https://nemesisfinal.vercel.app/api/system/status{Style.RESET_ALL}")

            print(f"\n{Fore.MAGENTA}► RENDER (Backup Backend):{Style.RESET_ALL}")
            print(f"  API Engine: {Fore.BLUE}https://projectnemesis.onrender.com/api/system/status{Style.RESET_ALL}")
            print(f"{Fore.CYAN}==========================================\n{Style.RESET_ALL}")
            
            sys.exit(0)
            
        if failed_endpoint and attempt > 12:
            print(f"{Fore.RED}Persistent error detected. Engaging Auto-Heal...")
            return failed_endpoint # Return the failure to the main loop
            
        if attempt < max_retries:
            time.sleep(15)
            
    print(f"\n{Fore.RED}{Style.BRIGHT}TIMEOUT: Deployments failed to come online.")
    sys.exit(1)

if __name__ == "__main__":
    max_heal_loops = 3
    for heal_loop in range(max_heal_loops):
        print(f"\n{Fore.YELLOW}{Style.BRIGHT}=== LIFECYCLE LOOP {heal_loop+1}/{max_heal_loops} ==={Style.RESET_ALL}")
        trigger_deployments()
        
        failure = monitor_deployments()
        if failure:
            # If monitor returns a failure, it needs auto-healing
            healed = auto_heal(*failure)
            if not healed:
                print(f"{Fore.RED}Auto-Heal failed to generate a viable patch. Halting.")
                sys.exit(1)
            # If healed = True, the loop will restart and trigger deployment again!
            
    print(f"{Fore.RED}Max auto-heal loops reached without achieving stability. Halting.")
