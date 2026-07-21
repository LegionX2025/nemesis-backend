import os
import sys
import subprocess
import time
import threading
import argparse
import re
from google import genai
from google.genai import types

MODELS = ["gemini-3.1-pro", "gemini-3.1-flash", "gemini-3.0-pro", "gemini-3.0-flash"]
APP_FILE = "app.py"

def get_valid_keys():
    api_keys_str = os.getenv("GEMINI_API_KEYS", "")
    keys = [k.strip().replace('"', '').replace("'", "") for k in api_keys_str.split(",") if k.strip()]
    valid_keys = [k for k in keys if k.startswith("AIza") or k.startswith("AQ.")]
    return valid_keys

# --- NATIVE TOOLS FOR LOCAL AGENT ---
def execute_tool(tool_name, args):
    try:
        if tool_name == "read_file":
            with open(args["path"], "r", encoding="utf-8") as f: return f.read()
        elif tool_name == "write_file":
            os.makedirs(os.path.dirname(os.path.abspath(args["path"])), exist_ok=True)
            with open(args["path"], "w", encoding="utf-8") as f: f.write(args["content"])
            return f"Successfully wrote {args['path']}"
        elif tool_name == "list_directory":
            return str(os.listdir(args["path"]))
        elif tool_name == "execute_command":
            process = subprocess.run(args["command"], shell=True, capture_output=True, text=True, timeout=120)
            return f"Exit Code: {process.returncode}\nSTDOUT:\n{process.stdout}\nSTDERR:\n{process.stderr}"
        else:
            return f"Unknown tool: {tool_name}"
    except Exception as e:
        return f"Tool Execution Error: {e}"

def parse_tool_calls(text):
    calls = []
    # Match <tool_call><name>...</name>...args...</tool_call>
    pattern = r"<tool_call>\s*<name>(.*?)</name>\s*(.*?)</tool_call>"
    matches = re.finditer(pattern, text, re.DOTALL)
    for match in matches:
        name = match.group(1).strip()
        args_text = match.group(2)
        args = {}
        if name in ["read_file", "list_directory"]:
            path_match = re.search(r"<path>(.*?)</path>", args_text, re.DOTALL)
            if path_match: args["path"] = path_match.group(1).strip()
        elif name == "write_file":
            path_match = re.search(r"<path>(.*?)</path>", args_text, re.DOTALL)
            content_match = re.search(r"<content>(.*?)</content>", args_text, re.DOTALL)
            if path_match: args["path"] = path_match.group(1).strip()
            if content_match: args["content"] = content_match.group(1)
        elif name == "execute_command":
            cmd_match = re.search(r"<command>(.*?)</command>", args_text, re.DOTALL)
            if cmd_match: args["command"] = cmd_match.group(1).strip()
        
        calls.append({"name": name, "args": args})
    return calls

# --- CORE AGENT ORCHESTRATION ---
def run_omni_agent(valid_keys, prompt):
    system_instruction = """
You are Omni-Engineer (Antigravity), an elite autonomous Multi-Agent orchestration system designed by Google Deepmind.
You have full access to the local machine to heal the system, redesign architecture, and execute deployments.

You have the following tools available. To use a tool, output exactly this XML format:
<tool_call>
<name>read_file</name>
<path>app.py</path>
</tool_call>

<tool_call>
<name>write_file</name>
<path>app.py</path>
<content>...code...</content>
</tool_call>

<tool_call>
<name>list_directory</name>
<path>cloudflare_frontend</path>
</tool_call>

<tool_call>
<name>execute_command</name>
<command>npm install</command>
</tool_call>

You can issue multiple tool calls in a single response.
Once you have fully completed the task and verified it, output:
<status>COMPLETE</status>
"""
    
    for model_name in MODELS:
        for api_key in valid_keys:
            try:
                client = genai.Client(api_key=api_key)
                print(f"\n[OMNI-ENGINEER] Spawning Agent logic on {model_name}...")
                
                messages = [
                    {"role": "user", "parts": [{"text": system_instruction + "\n\nTASK:\n" + prompt}]}
                ]
                
                max_turns = 15
                for turn in range(max_turns):
                    response = client.models.generate_content(
                        model=model_name,
                        contents=messages
                    )
                    
                    reply_text = response.text
                    
                    messages.append({"role": "model", "parts": [{"text": reply_text}]})
                    
                    if "<status>COMPLETE</status>" in reply_text:
                        print("[OMNI-ENGINEER] Task reported as COMPLETE.")
                        return True
                        
                    tool_calls = parse_tool_calls(reply_text)
                    if not tool_calls:
                        messages.append({"role": "user", "parts": [{"text": "You did not use any tools or output <status>COMPLETE</status>. Please proceed."}]})
                        continue
                        
                    tool_results_str = ""
                    for call in tool_calls:
                        print(f"[OMNI-ENGINEER] Executing {call['name']}...")
                        res = execute_tool(call["name"], call["args"])
                        tool_results_str += f"\nResult of {call['name']}:\n{res}\n"
                        
                    messages.append({"role": "user", "parts": [{"text": f"Tool Execution Results:\n{tool_results_str}"}]})
                
                print("[OMNI-ENGINEER] Max agent turns reached.")
                return False
                
            except Exception as e:
                print(f"[OMNI-ENGINEER] Model {model_name} failed: {e}. Rotating...")
                continue
                
    print("[OMNI-ENGINEER] All models exhausted.")
    return False

# --- DAEMON MONITOR ---
def monitor_backend(valid_keys):
    retry_count = 0
    MAX_RETRIES = 5
    while retry_count < MAX_RETRIES:
        print(f"[BACKEND-MONITOR] Starting {APP_FILE}... (Attempt {retry_count + 1}/{MAX_RETRIES})")
        process = subprocess.Popen(
            [sys.executable, APP_FILE],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8', errors='replace'
        )
        
        def stream_out(pipe, prefix=""):
            for line in iter(pipe.readline, ''):
                print(f"{prefix}{line}", end="")
                
        threading.Thread(target=stream_out, args=(process.stdout,), daemon=True).start()
        
        stderr_lines = []
        for line in iter(process.stderr.readline, ''):
            print(f"[APP-ERR] {line}", end="")
            stderr_lines.append(line)
            if len(stderr_lines) > 200: stderr_lines.pop(0)
                
        process.wait()
        if process.returncode == 0:
            print("[BACKEND-MONITOR] Server exited normally.")
            break
            
        print(f"\n[BACKEND-MONITOR] CRASH DETECTED! Exit code: {process.returncode}")
        
        retry_count += 1
        if retry_count >= MAX_RETRIES:
            print("[BACKEND-MONITOR] Maximum retry limit reached.")
            break
            
        print("[BACKEND-MONITOR] Dispatching crash log to Omni-Engineer...")
        error_log = "".join(stderr_lines)
        prompt = f"The backend server `app.py` crashed with the following stderr log:\n{error_log}\nInvestigate and fix the issue so the server can boot."
        success = run_omni_agent(valid_keys, prompt)
        
        if success:
            print("[BACKEND-MONITOR] Omni-Engineer resolved the issue. Restarting in 3 seconds...")
            time.sleep(3)
        else:
            print("[BACKEND-MONITOR] Omni-Engineer failed to resolve the crash.")
            break

def main():
    print("============================================================")
    print(" 👁️ NEMESIS OMNI-ENGINEER INITIATED (ANTIGRAVITY NODE)")
    print("============================================================")
    
    from dotenv import load_dotenv
    load_dotenv()
    
    valid_keys = get_valid_keys()
    if not valid_keys:
        print("[OMNI-ENGINEER] No valid GEMINI_API_KEYS found. Cannot proceed.")
        sys.exit(1)
        
    parser = argparse.ArgumentParser(description="Nemesis Omni-Engineer")
    parser.add_argument("--task", type=str, help="Specific task for the Omni-Engineer to execute (Auto-Design / Refactor).")
    args = parser.parse_args()
    
    if args.task:
        print(f"[OMNI-ENGINEER] Launching Task Mode: {args.task}")
        run_omni_agent(valid_keys, args.task)
        print("[OMNI-ENGINEER] Task execution completed.")
    else:
        print("[OMNI-ENGINEER] Launching Daemon Mode (Background Healing).")
        monitor_backend(valid_keys)

if __name__ == "__main__":
    main()
