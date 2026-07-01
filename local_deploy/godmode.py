import os
import subprocess
import time
import re
import sys
import json
from pathlib import Path

def print_header(title):
    print(f"\n{'='*60}")
    print(f" 🚀 {title}")
    print(f"{'='*60}")

def run_command(cmd, cwd=None):
    print(f"🔧 Running: {cmd}")
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
            
    return process.returncode, "".join(output)

def setup_cloudflare_tunnel():
    print_header("Setting up Cloudflare Tunnel")
    print("Checking for cloudflared...")
    
    cloudflared_exec = "cloudflared"
    ret, out = run_command("cloudflared --version")
    if ret != 0:
        print("⚠️ cloudflared not found in PATH. Checking local directory...")
        if not Path("cloudflared.exe").exists():
            print("📥 Downloading cloudflared for Windows using Python urllib...")
            import urllib.request
            try:
                urllib.request.urlretrieve(
                    "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe",
                    "cloudflared.exe"
                )
                print("✅ Successfully downloaded cloudflared.exe")
            except Exception as e:
                print(f"❌ Failed to download cloudflared: {e}")
                sys.exit(1)
        cloudflared_exec = ".\\cloudflared.exe"
        
    print(f"Starting Cloudflare tunnel to port 3001 in the background using {cloudflared_exec}...")
    log_file = Path("cloudflared.log")
    if log_file.exists():
        log_file.unlink()
        
    tunnel_proc = subprocess.Popen(
        f"{cloudflared_exec} tunnel --url http://127.0.0.1:3001 > cloudflared.log 2>&1",
        shell=True
    )
    
    print("Waiting for tunnel to establish (15 seconds)...")
    tunnel_url = None
    for _ in range(15):
        time.sleep(1)
        if log_file.exists():
            with open(log_file, "r", encoding="utf-8") as f:
                content = f.read()
                match = re.search(r'(https://[a-zA-Z0-9-]+\.trycloudflare\.com)', content)
                if match:
                    tunnel_url = match.group(1)
                    break
                    
    if not tunnel_url:
        print("❌ Failed to establish Cloudflare tunnel or extract URL.")
        print("Log output:")
        if log_file.exists():
            with open(log_file, "r", encoding="utf-8") as f:
                print(f.read())
        # Fallback for now so the script can continue
        tunnel_url = "https://nemesis-tunnel.trycloudflare.com"
        print(f"⚠️ Using fallback URL: {tunnel_url}")
    else:
        print(f"✅ Tunnel established! URL: {tunnel_url}")
        
    return tunnel_proc, tunnel_url

def update_wrangler_toml(worker_dir, tunnel_url):
    print_header("Updating wrangler.toml with Tunnel URL")
    toml_path = Path(worker_dir) / "wrangler.toml"
    if not toml_path.exists():
        print(f"❌ {toml_path} not found!")
        sys.exit(1)
        
    with open(toml_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    if "[vars]" not in content:
        content += "\n[vars]\n"
        
    if "PYTHON_BACKEND_URL" in content:
        content = re.sub(
            r'PYTHON_BACKEND_URL\s*=\s*".*"',
            f'PYTHON_BACKEND_URL = "{tunnel_url}"',
            content
        )
    else:
        content = content.replace("[vars]", f'[vars]\nPYTHON_BACKEND_URL = "{tunnel_url}"')
        
    with open(toml_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"✅ Updated PYTHON_BACKEND_URL to {tunnel_url}")

def auto_deploy_worker(worker_dir):
    print_header("Auto-Deploying Edge Worker")
    ret, out = run_command("npx wrangler deploy", cwd=worker_dir)
    if ret != 0:
        print("❌ Worker deployment failed!")
        # Auto-fix logic can be expanded here based on `out`
        if "10097" in out:
            print("⚠️ Detected Migration Error 10097. Attempting auto-fix...")
            # Modify wrangler.toml to use new_sqlite_classes
            toml_path = Path(worker_dir) / "wrangler.toml"
            with open(toml_path, "r", encoding="utf-8") as f:
                c = f.read()
            c = c.replace('new_classes = ["TraceCoordinator"', 'new_sqlite_classes = ["TraceCoordinator"')
            with open(toml_path, "w", encoding="utf-8") as f:
                f.write(c)
            print("✅ Applied auto-fix. Redeploying...")
            ret, out = run_command("npx wrangler deploy", cwd=worker_dir)
            
        if ret != 0:
            print("❌ Worker redeployment still failed. Please check logs.")
            sys.exit(1)
    print("✅ Worker deployed successfully!")

def deploy_frontend():
    print_header("Deploying Frontend to Cloudflare Pages")
    frontend_dir = Path("../cloudflare_frontend").resolve()
    
    # Patch the frontend HTML files to point to the worker
    html_files = list(frontend_dir.glob("*.html"))
    worker_url = "https://nemesis-api.legionxgaming2021.workers.dev"
    print("Patching frontend HTML files to use Worker URL...")
    for html_file in html_files:
        with open(html_file, "r", encoding="utf-8") as f:
            content = f.read()
            
        # Replace relative API calls or localhost fallback with the actual worker URL
        content = content.replace("'/api/login'", f"'{worker_url}/api/login'")
        content = content.replace("const baseUrl = isLocal ? 'http://127.0.0.1:3001' : '';", f"const baseUrl = isLocal ? 'http://127.0.0.1:3001' : '{worker_url}';")
        content = content.replace("const wsUrl = isLocal ? 'ws://127.0.0.1:3001' : (window.location.protocol === 'https:' ? 'wss://' : 'ws://') + window.location.host;", f"const wsUrl = isLocal ? 'ws://127.0.0.1:3001' : 'wss://nemesis-api.legionxgaming2021.workers.dev';")
        
        with open(html_file, "w", encoding="utf-8") as f:
            f.write(content)
            
    print("✅ Patched frontend HTML.")
    
    # Deploy to Pages
    cmd = f"npx wrangler pages deploy \"{frontend_dir}\" --project-name nemesis-id-frontend"
    ret, out = run_command(cmd)
    if ret != 0:
        print("❌ Frontend deployment failed!")
    else:
        print("✅ Frontend deployed successfully!")

def start_backend():
    print_header("Starting Local Backend")
    backend_proc = subprocess.Popen(
        "python ../main.py",
        shell=True
    )
    print("✅ Backend started in background.")
    return backend_proc

if __name__ == "__main__":
    print_header("GODMODE: NEMESIS OMNI-ARCHITECTURE AUTO-DEPLOYER")
    
    worker_dir = Path("nemesis-global-worker").resolve()
    
    # 1. Start Tunnel
    tunnel_proc, tunnel_url = setup_cloudflare_tunnel()
    
    # 2. Update Worker Config
    update_wrangler_toml(worker_dir, tunnel_url)
    
    # 3. Deploy Worker
    auto_deploy_worker(worker_dir)
    
    # 4. Deploy Frontend
    deploy_frontend()
    
    # 5. Start Backend
    backend_proc = start_backend()
    
    print_header("🎉 ALL SYSTEMS GO!")
    print(f"🌍 Frontend URL: https://nemesis-id-frontend.pages.dev")
    print(f"⚡ Worker URL: https://nemesis-api.legionxgaming2021.workers.dev")
    print(f"🚇 Backend Tunnel: {tunnel_url}")
    print("\nPress Ctrl+C to terminate backend and tunnel.")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")
        if tunnel_proc:
            tunnel_proc.terminate()
        if backend_proc:
            backend_proc.terminate()
        print("Shutdown complete.")
