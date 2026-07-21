import os
import subprocess
import re
import sys

# Hardcoded original IDs from the repo to replace
OLD_KV_ID = "556aa273aeac4b009b559bb215346ce3"
OLD_D1_AUDIT = "80acedab-33c2-4637-bee7-6b9a1176a463"
OLD_D1_PRIMARY = "73ef6e7d-9499-4d59-a190-ae7220873a71"
OLD_D1_SECONDARY = "860655f8-aa37-4d4f-92a9-b5ea49bc101a"

def run_cmd(cmd, cwd=None):
    print(f"\n[>] Running: {cmd}")
    result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[!] Error or Warning:\n{result.stderr}\n{result.stdout}")
    else:
        print(f"[+] Success")
        if result.stdout.strip():
            print(result.stdout.strip()[:200] + ("..." if len(result.stdout) > 200 else ""))
    return result.stdout, result.returncode

def extract_id(text, regex):
    match = re.search(regex, text)
    if match:
        return match.group(1)
    return None

def main():
    print("=====================================================")
    print(" NEMESIS OMNI-CHAIN - CLOUDFLARE SETUP & DEPLOYMENT  ")
    print("=====================================================")
    
    # 1. Create KV
    print("\n--- 1. Configuring KV Namespaces ---")
    out, code = run_cmd("npx wrangler kv:namespace create NEMESIS_KV")
    new_kv_id = extract_id(out, r'id\s*=\s*"([^"]+)"')
    if not new_kv_id:
        print("[!] Could not extract new KV ID. Assuming it might already exist.")
        # Try to get list
        out_list, _ = run_cmd("npx wrangler kv:namespace list")
        new_kv_id = extract_id(out_list, r'"id":\s*"([^"]+)",\s*"title":\s*"[^"]*NEMESIS_KV"')
    print(f"[*] NEMESIS_KV ID: {new_kv_id}")

    # 2. Create D1
    print("\n--- 2. Configuring D1 Databases ---")
    new_d1_audit = None
    new_d1_primary = None
    new_d1_sec = None
    
    for db_name in ["nemesis_audit_db", "nemesis", "nemesis-db"]:
        out, _ = run_cmd(f"npx wrangler d1 create {db_name}")
        db_id = extract_id(out, r'database_id\s*=\s*"([^"]+)"')
        if not db_id:
            out_list, _ = run_cmd("npx wrangler d1 list")
            # Parse table output (uuid format)
            match = re.search(rf'{db_name}.*?([0-9a-fA-F]{{8}}-[0-9a-fA-F]{{4}}-[0-9a-fA-F]{{4}}-[0-9a-fA-F]{{4}}-[0-9a-fA-F]{{12}})', out_list)
            if match:
                db_id = match.group(1)
        print(f"[*] {db_name} ID: {db_id}")
        
        if db_name == "nemesis_audit_db": new_d1_audit = db_id
        if db_name == "nemesis": new_d1_primary = db_id
        if db_name == "nemesis-db": new_d1_sec = db_id

    # 3. Create R2
    print("\n--- 3. Configuring R2 Buckets ---")
    run_cmd("npx wrangler r2 bucket create nemesis-assets")

    # 4. Update files
    print("\n--- 4. Updating configuration files with your Account IDs ---")
    files_to_update = [
        "wrangler.toml",
        "frontend/wrangler.toml",
        "nemesis_python_worker/wrangler.toml",
        "auto_cloudflare.py"
    ]
    
    for filepath in files_to_update:
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if new_kv_id: content = content.replace(OLD_KV_ID, new_kv_id)
            if new_d1_audit: content = content.replace(OLD_D1_AUDIT, new_d1_audit)
            if new_d1_primary: content = content.replace(OLD_D1_PRIMARY, new_d1_primary)
            if new_d1_sec: content = content.replace(OLD_D1_SECONDARY, new_d1_sec)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"[+] Updated {filepath}")

    # 5. Deploy Workers and Pages
    print("\n--- 5. Deploying Infrastructure to Edge ---")
    
    # Proxy Worker
    print("\n[*] Deploying Edge Proxy...")
    if os.path.exists("cloudflare_worker"):
        run_cmd("npm install", cwd="cloudflare_worker")
    run_cmd("npx wrangler deploy")
    
    # Python Worker
    print("\n[*] Deploying Python Worker...")
    if not os.path.exists("nemesis_python_worker/src"):
        run_cmd("python auto_cloudflare.py")
    else:
        run_cmd("npx wrangler deploy", cwd="nemesis_python_worker")
        
    # Frontend Pages
    print("\n[*] Deploying Frontend Pages...")
    if os.path.exists("frontend"):
        run_cmd("npx wrangler pages deploy . --project-name nemesis-frontend", cwd="frontend")
        
    print("\n=====================================================")
    print(" ✅ DEPLOYMENT SCRIPT FINISHED")
    print("=====================================================")

if __name__ == "__main__":
    main()
