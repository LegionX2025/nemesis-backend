import os
import sys
import subprocess
import time
import requests
import json
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEYS = os.environ.get("GEMINI_API_KEYS", os.environ.get("GEMINI_API_KEY", ""))
gemini_keys = [k.strip() for k in GEMINI_API_KEYS.split(",") if k.strip()]

AIML_KEY = os.environ.get("AIML_API_KEY_BAGOODEX", os.environ.get("AIML_API_KEY_CHATGPT"))

def query_gemini_to_heal(error_log):
    prompt = f"""
You are the Godmode Self-Healing Agent. 
A deployment process (auto_deploy.py) just failed.
Here is the error log:

```text
{error_log}
```

Write a python script that will automatically fix this issue in the codebase.
For example, if it's a missing dependency, write a script to install it.
If it's a code error, write a script to read the file, string replace the error, and rewrite it.
If it's an API token error, write a script to fix the environment variables.

ONLY OUTPUT VALID PYTHON CODE. Do not include markdown code blocks (like ```python) in your response, just the raw python code. DO NOT OUTPUT ANYTHING ELSE.
    """
    
    # Try Gemini Keys first
    for key in gemini_keys:
        if not key.startswith("AIza"): continue
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={key}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.2}
        }
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=15)
            if response.status_code == 429:
                print(f"[GODMODE] Gemini key {key[:8]}... rate limited. Rotating...")
                continue
            response.raise_for_status()
            result = response.json()
            text = result["candidates"][0]["content"]["parts"][0]["text"]
            return _clean_script(text)
        except Exception as e:
            print(f"[GODMODE] Failed with Gemini key {key[:8]}... : {e}")
            continue

    # Fallback to AIML API
    if AIML_KEY:
        print("[GODMODE] Falling back to AIML API...")
        try:
            url = "https://api.aimlapi.com/v1/chat/completions"
            headers = {"Authorization": f"Bearer {AIML_KEY}", "Content-Type": "application/json"}
            payload = {
                "model": "gpt-4o",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.2
            }
            response = requests.post(url, headers=headers, json=payload, timeout=20)
            response.raise_for_status()
            result = response.json()
            text = result["choices"][0]["message"]["content"]
            return _clean_script(text)
        except Exception as e:
            print(f"[GODMODE] Failed to query AIML: {e}")

    print("[GODMODE] All AI healing models failed.")
    return None

def _clean_script(text):
    if text.startswith("```python"):
        text = text[9:]
    if text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()

def run_godmode_loop(max_retries=5):
    print("============================================================")
    print(" 🌟 NEMESIS GODMODE: AUTONOMOUS SELF-HEALING ENGINE STARTED")
    print("============================================================")
    
    # ML Knowledge Base Ingestion Pre-Flight
    print("[GODMODE] Triggering ML Knowledge Base Ingestion...")
    try:
        from services.ml_engine import ml_engine
        ingest_res = ml_engine.ingest_knowledge_base()
        print(f"[GODMODE] ML Engine: {ingest_res.get('message', 'Ingestion complete')}")
    except Exception as e:
        print(f"[GODMODE] ML Ingestion skipped: {e}")
        
    attempt = 1
    while attempt <= max_retries:
        print(f"\n[GODMODE] Attempt {attempt}/{max_retries} to deploy...")
        
        process = subprocess.Popen(
            [sys.executable, "auto_deploy.py"], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT, 
            text=True
        )
        
        output_log = ""
        has_error = False
        
        for line in process.stdout:
            print(line, end="")
            output_log += line
            if "[ERROR]" in line or "ERR!" in line or "failed" in line.lower():
                has_error = True
                
        process.wait()
        
        if process.returncode == 0 and not has_error:
            print("\n[GODMODE] Deployment Successful. All systems stable.")
            break
            
        print(f"\n[GODMODE] Deployment failed with exit code {process.returncode}. Engaging Self-Healing Protocol...")
        
        # Keep only the last 200 lines of log to avoid context limit
        trimmed_log = "\n".join(output_log.split("\n")[-200:])
        
        fix_script = query_gemini_to_heal(trimmed_log)
        
        if fix_script:
            print("[GODMODE] Gemini provided a healing script. Applying patch...")
            with open("godmode_temp_fix.py", "w", encoding="utf-8") as f:
                f.write(fix_script)
                
            try:
                subprocess.run([sys.executable, "godmode_temp_fix.py"], check=True)
                print("[GODMODE] Patch applied successfully.")
            except Exception as e:
                print(f"[GODMODE] The healing patch failed: {e}")
                
            if os.path.exists("godmode_temp_fix.py"):
                os.remove("godmode_temp_fix.py")
        else:
            print("[GODMODE] Gemini could not provide a fix. Retrying blindly...")
            
        attempt += 1
        time.sleep(2)

if __name__ == "__main__":
    if "--deploy-all" in sys.argv:
        # Just run the auto deploy once with full autonomy
        subprocess.run([sys.executable, "auto_deploy.py"])
    else:
        run_godmode_loop()
