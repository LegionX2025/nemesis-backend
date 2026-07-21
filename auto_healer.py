import os
import sys
import subprocess
import time
import threading
from google import genai

# Configuration
MAX_RETRIES = 3
APP_FILE = "app.py"

# Models configuration for rotation
MODELS = ["gemini-3.1-pro", "gemini-3.1-flash", "gemini-3.0-pro", "gemini-3.0-flash"]

def get_valid_keys():
    api_keys_str = os.getenv("GEMINI_API_KEYS", "")
    keys = [k.strip().replace('"', '').replace("'", "") for k in api_keys_str.split(",") if k.strip()]
    valid_keys = [k for k in keys if k.startswith("AIza") or k.startswith("AQ.")]
    if not valid_keys:
        print("[AUTO-HEALER] No valid GEMINI_API_KEYS found. Cannot auto-heal.")
        return []
    return valid_keys

def ask_gemini_for_fix(valid_keys, error_log, app_code):
    prompt = f"""
You are Antigravity, a powerful agentic AI coding assistant designed by the Google Deepmind team.
Your role here is to act as an autonomous AI self-healing bootstrapper for the NEMESIS platform.

The server `app.py` crashed with the following error log:

<ERROR_LOG>
{error_log}
</ERROR_LOG>

Here is the current source code of `app.py`:
<SOURCE_CODE>
{app_code}
</SOURCE_CODE>

Analyze the error. You must provide a fix using ONE of the two formats below. 

IF the error is a missing pip package (ModuleNotFoundError, ImportError), output exactly:
PIP_INSTALL: package_name

IF the error is a syntax error, type error, or other code bug, output exactly:
CODE_PATCH:
```python
<ENTIRE_REPLACEMENT_CODE_FOR_APP_PY>
```
Make sure to provide the full replacement code. Do not use markdown wrapping around the PIP_INSTALL response.
"""
    for model_name in MODELS:
        for api_key in valid_keys:
            try:
                print(f"[AUTO-HEALER] Attempting to heal using {model_name}...")
                client = genai.Client(api_key=api_key)
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt
                )
                if response and response.text:
                    return response.text
            except Exception as e:
                print(f"[AUTO-HEALER] Rotation: Failed with {model_name} -> {e}")
                continue
    
    print("[AUTO-HEALER] All models and keys exhausted. Self-healing failed.")
    return None

def apply_fix(fix_response):
    if "PIP_INSTALL:" in fix_response:
        pkg = fix_response.split("PIP_INSTALL:")[1].strip().split("\n")[0].strip()
        print(f"[AUTO-HEALER] Installing missing package: {pkg}")
        subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])
        return True
    
    if "CODE_PATCH:" in fix_response:
        print(f"[AUTO-HEALER] Applying code patch to {APP_FILE}")
        parts = fix_response.split("```python")
        if len(parts) > 1:
            code = parts[1].split("```")[0].strip()
        else:
            # fallback
            code = fix_response.split("CODE_PATCH:")[1].strip()
        
        with open(APP_FILE, "w", encoding="utf-8") as f:
            f.write(code)
        return True
        
    print("[AUTO-HEALER] Could not parse Gemini response for a valid fix.")
    print(f"Response was: {fix_response}")
    return False

def main():
    print("============================================================")
    print(" 🛡️ NEMESIS AUTO-HEALING BOOTSTRAPPER INITIATED")
    print("============================================================")
    
    from dotenv import load_dotenv
    load_dotenv()
    
    valid_keys = get_valid_keys()
    
    retry_count = 0
    while retry_count < MAX_RETRIES:
        print(f"[AUTO-HEALER] Starting {APP_FILE}... (Attempt {retry_count + 1}/{MAX_RETRIES})")
        
        process = subprocess.Popen(
            [sys.executable, APP_FILE],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        
        def stream_out(pipe, prefix=""):
            for line in iter(pipe.readline, ''):
                print(f"{prefix}{line}", end="")
                
        stdout_thread = threading.Thread(target=stream_out, args=(process.stdout,))
        stdout_thread.daemon = True
        stdout_thread.start()
        
        stderr_lines = []
        for line in iter(process.stderr.readline, ''):
            print(f"[APP-ERR] {line}", end="")
            stderr_lines.append(line)
            if len(stderr_lines) > 200:
                stderr_lines.pop(0)
                
        process.wait()
        
        if process.returncode == 0:
            print("[AUTO-HEALER] Server exited normally.")
            break
            
        print(f"\n[AUTO-HEALER] CRASH DETECTED! Exit code: {process.returncode}")
        
        if not valid_keys:
            print("[AUTO-HEALER] Gemini keys are not configured. Exiting.")
            sys.exit(process.returncode)
            
        retry_count += 1
        if retry_count >= MAX_RETRIES:
            print("[AUTO-HEALER] Maximum retry limit reached. Shutting down.")
            sys.exit(process.returncode)
            
        print("[AUTO-HEALER] Analyzing crash with Gemini AI...")
        
        error_log = "".join(stderr_lines)
        try:
            with open(APP_FILE, "r", encoding="utf-8") as f:
                app_code = f.read()
        except Exception as e:
            app_code = f"Error reading {APP_FILE}: {e}"
            
        fix_response = ask_gemini_for_fix(valid_keys, error_log, app_code)
        
        if fix_response:
            print("[AUTO-HEALER] Received fix plan from Gemini.")
            success = apply_fix(fix_response)
            if success:
                print("[AUTO-HEALER] Fix applied successfully. Restarting in 3 seconds...")
                time.sleep(3)
                continue
            else:
                print("[AUTO-HEALER] Failed to apply fix.")
        else:
            print("[AUTO-HEALER] No fix provided by Gemini.")
            
        print("[AUTO-HEALER] Auto-healing failed. Exiting.")
        sys.exit(process.returncode)

if __name__ == "__main__":
    main()
