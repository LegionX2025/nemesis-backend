import os
import subprocess
import re
import sys
import time

def run_cmd(cmd, cwd=None, capture=True):
    print(f"\n[🚀] Executing: {cmd}")
    try:
        if capture:
            result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"[⚠️] Warning/Error:\n{result.stderr}\n{result.stdout}")
            return result.stdout, result.returncode
        else:
            subprocess.Popen(cmd, shell=True, cwd=cwd)
            return "", 0
    except Exception as e:
        print(f"[❌] Exception running command: {e}")
        return "", 1

def extract_id(text, regex):
    match = re.search(regex, text)
    if match:
        return match.group(1)
    return None

def main():
    print("=====================================================")
    print(" NEMESIS v3.1 Enterprise - CLOUDFLARE DEPLOYER ")
    print("=====================================================")
    
    # 1. Provision D1 Database
    print("\n--- 1. Provisioning D1 Serverless SQL ---")
    out, _ = run_cmd("npx wrangler d1 create nemesis_db")
    d1_id = extract_id(out, r'database_id\s*=\s*"([^"]+)"')
    if not d1_id:
        out_list, _ = run_cmd("npx wrangler d1 list")
        match = re.search(r'nemesis_db.*?([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})', out_list, re.DOTALL)
        if match: d1_id = match.group(1)
    print(f"[*] D1 ID: {d1_id}")

    # 2. Provision KV Namespace
    print("\n--- 2. Provisioning KV Global Cache ---")
    out, _ = run_cmd("npx wrangler kv namespace create NEMESIS_KV")
    kv_id = extract_id(out, r'id\s*=\s*"([^"]+)"')
    if not kv_id:
        out_list, _ = run_cmd("npx wrangler kv namespace list")
        kv_id = extract_id(out_list, r'"id":\s*"([^"]+)",\s*"title":\s*"[^"]*NEMESIS_KV"')
    print(f"[*] KV ID: {kv_id}")

    # 3. Provision R2 Bucket
    print("\n--- 3. Provisioning R2 Binary Storage ---")
    run_cmd("npx wrangler r2 bucket create nemesis-evidence")

    # 4. Provision Cloudflare Queues
    print("\n--- 4. Provisioning Job Queues ---")
    run_cmd("npx wrangler queues create nemesis-jobs")

    # 5. Inject IDs into wrangler.toml
    print("\n--- 5. Injecting Infrastructure Bindings into wrangler.toml ---")
    wrangler_path = "wrangler.toml"
    if os.path.exists(wrangler_path):
        with open(wrangler_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if d1_id:
            content = re.sub(r'database_id\s*=\s*"[^"]*"', f'database_id = "{d1_id}"', content)
        if kv_id:
            content = re.sub(r'\bid\s*=\s*"[^"]*"', f'id = "{kv_id}"', content)
            
        with open(wrangler_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print("[+] wrangler.toml dynamically updated with Cloudflare Resource IDs.")

    # 6. Deploy Cloudflare Pages (Frontend)
    print("\n--- 6. Deploying React/HTML Frontend to Cloudflare Pages ---")
    print("[*] Building Vite Production Bundle...")
    run_cmd("npm run build", cwd="frontend")
    run_cmd("npx wrangler pages deploy frontend/dist --project-name nemesis-frontend")

    # 7. Deploy Cloudflare Workers (Gateway, Queues, Durable Objects)
    print("\n--- 7. Deploying API Gateway, Durable Objects, and Queue Consumers ---")
    run_cmd("npx wrangler deploy")

    # 8. Start Named Tunnel for Local Python Backend
    print("\n--- 8. Bridging Local Python API via Cloudflare Tunnel ---")
    print("[*] Spawning cloudflared in the background...")
    # This runs asynchronously
    run_cmd("cloudflared tunnel run nemesis-tunnel", capture=False)

    # 9. Trigger Render Deployment
    print("\n--- 9. Triggering Render Production Deployment ---")
    try:
        import urllib.request
        render_hook_url = "https://api.render.com/deploy/srv-d99urs8k1i2s73eroij0?key=zZ7KkV_qUfA"
        print(f"[*] Calling Render Webhook: {render_hook_url}")
        req = urllib.request.Request(render_hook_url, method="POST")
        with urllib.request.urlopen(req) as response:
            if response.status == 200:
                print("[+] Render Deployment Triggered Successfully!")
            else:
                print(f"[!] Render Deployment returned status code {response.status}")
    except Exception as e:
        print(f"[❌] Failed to trigger Render deployment: {e}")

    print("\n=====================================================")
    print(" ✅ ENTERPRISE DEPLOYMENT COMPLETE")
    print("=====================================================")
    print(" 🌍 Frontend: https://nemesis-frontend.pages.dev")
    print(" ⚡ Gateway & DOs: Active on Cloudflare Global Edge")
    print(" 🐍 Python API: Bridged via Named Tunnel")

if __name__ == "__main__":
    main()
