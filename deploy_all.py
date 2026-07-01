import os
import subprocess
import re
import sys
import shutil

def patch_file_urls(filepath, hide_warning=False):
    if not os.path.exists(filepath):
        if not hide_warning:
            print(f"    -> WARNING: {filepath} not found.")
        return
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    # Replace localhost URLs with Cloudflare Native URLs
    content = re.sub(r'http://127\.0\.0\.1:5000', 'https://nemesis-api.legionxgaming2021.workers.dev', content)
    content = re.sub(r'http://127\.0\.0\.1:8000', 'https://nemesis-api.legionxgaming2021.workers.dev', content)
    content = re.sub(r'ws://127\.0\.0\.1:5000', 'wss://nemesis-api.legionxgaming2021.workers.dev', content)
    content = re.sub(r'ws://127\.0\.0\.1:8000', 'wss://nemesis-api.legionxgaming2021.workers.dev', content)
    
    # Patch old Render URLs if they exist
    content = re.sub(r'https://nemesis-backend-ymr5\.onrender\.com', 'https://nemesis-api.legionxgaming2021.workers.dev', content)
    content = re.sub(r'wss://nemesis-backend-ymr5\.onrender\.com', 'wss://nemesis-api.legionxgaming2021.workers.dev', content)
    
    # Also patch relative fetches for when it's deployed as a static site on Cloudflare Pages
    content = re.sub(r"fetch\('/api/", "fetch('https://nemesis-api.legionxgaming2021.workers.dev/api/", content)
    content = re.sub(r'fetch\("/api/', 'fetch("https://nemesis-api.legionxgaming2021.workers.dev/api/', content)
    content = re.sub(r"fetch\('/admin/", "fetch('https://nemesis-api.legionxgaming2021.workers.dev/admin/", content)
    content = re.sub(r'fetch\("/admin/', 'fetch("https://nemesis-api.legionxgaming2021.workers.dev/admin/', content)
    
    # Patch WebSocket dynamically generated host
    content = content.replace('protocol + window.location.host + "/ws/"', '"wss://nemesis-api.legionxgaming2021.workers.dev/ws/"')
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"    -> Production URLs injected in {os.path.basename(filepath)}.")

def clean_directory(dir_path, keep_files=None):
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
        return
    if keep_files is None:
        keep_files = []
    
    for item in os.listdir(dir_path):
        if item in keep_files:
            continue
        item_path = os.path.join(dir_path, item)
        try:
            if os.path.isdir(item_path):
                shutil.rmtree(item_path)
            else:
                os.remove(item_path)
        except Exception as e:
            print(f"    -> WARNING: Could not remove {item_path}: {e}")

def main():
    print("=== LIONSGATE NETWORK: FULL STACK DEPLOYMENT ===")
    
    print("\n[PRE-FLIGHT] Cleaning up old deployment folders...")
    clean_directory("render_backend", keep_files=[".git", ".env"])
    clean_directory("cloudflare_frontend", keep_files=[".git", "package.json", "node_modules", "tailwind.config.js"])
    print("    -> Cleanup complete.")
    
    # 0. Sync root backend files to render_backend/
    print("\n[0] Synchronizing Backend Files...")
    render_backend_dir = "render_backend"
    
    # Render uses main.py as the main script
    if os.path.exists("main.py"):
        shutil.copy2("main.py", os.path.join(render_backend_dir, "main.py"))
        print(f"    -> Copied main.py to {render_backend_dir}/main.py")
    else:
        print("    -> ERROR: main.py not found in root!")
        
    if os.path.exists("auto_backup.py"):
        shutil.copy2("auto_backup.py", os.path.join(render_backend_dir, "auto_backup.py"))
        print(f"    -> Copied auto_backup.py to {render_backend_dir}/auto_backup.py")
        
    # Sync directories needed by main.py
    for d in ["services", "intel", "darknet", "adapters"]:
        if os.path.exists(d):
            dst = os.path.join(render_backend_dir, d)
            if os.path.exists(dst):
                shutil.rmtree(dst)
            shutil.copytree(d, dst)
            print(f"    -> Copied {d}/ to {render_backend_dir}/{d}/")
            
    # Sync requirements
    if os.path.exists("requirements.txt"):
        shutil.copy2("requirements.txt", os.path.join(render_backend_dir, "requirements.txt"))
        print(f"    -> Copied requirements.txt to {render_backend_dir}/requirements.txt")
    else:
        print("    -> WARNING: requirements.txt not found in root! Render may fail without it.")
        
    # Sync logo_nemesis.jpeg into static/ so it serves correctly
    if os.path.exists("logo_nemesis.jpeg"):
        if not os.path.exists("static"):
            os.makedirs("static")
        shutil.copy2("logo_nemesis.jpeg", os.path.join("static", "logo_nemesis.jpeg"))
        print("    -> Synced logo_nemesis.jpeg into static/")

    # Generate nemesis_id.html
    if os.path.exists("build_nemesis_id.py"):
        try:
            subprocess.run([sys.executable, "build_nemesis_id.py"], check=True)
            print("    -> Built production NEMESIS ID (nemesis_id.html)")
        except subprocess.CalledProcessError as e:
            print(f"    -> ERROR: Failed to build NEMESIS ID: {e}")

    # 1. Sync frontend files
    print("\n[1] Synchronizing Frontend Files...")
    frontend_dir = "cloudflare_frontend"
    
    # Copy templates contents directly to frontend_dir root
    if os.path.exists("templates"):
        for file in os.listdir("templates"):
            src_path = os.path.join("templates", file)
            dst_path = os.path.join(frontend_dir, file)
            if os.path.isfile(src_path):
                shutil.copy2(src_path, dst_path)
            elif os.path.isdir(src_path):
                if os.path.exists(dst_path):
                    shutil.rmtree(dst_path)
                shutil.copytree(src_path, dst_path)
        print(f"    -> Copied templates contents to {frontend_dir}/")
        
    # Copy static directory as static
    if os.path.exists("static"):
        dst = os.path.join(frontend_dir, "static")
        if os.path.exists(dst):
            shutil.rmtree(dst)
        shutil.copytree("static", dst)
        print(f"    -> Copied static to {frontend_dir}/static")
            
    # Also copy HTML files in root just in case
    for item in os.listdir("."):
        if item.endswith(".html"):
            shutil.copy2(item, os.path.join(frontend_dir, item))

    # 1b. Update frontend URLs for production
    print("\n[1b] Configuring frontend for production...")
    files_to_patch = ["index.html", "admin.html", "audit.html", "nemesis_intelligence.html", "report_template.html", "nemesis_id.html", "darknet_search.html"]
    
    for filename in files_to_patch:
        patch_file_urls(os.path.join(frontend_dir, filename), hide_warning=False)
        # Some files might be in root too, but we hide warning if they aren't to avoid console spam
        patch_file_urls(filename, hide_warning=True)

    # 2. Deploy Frontend to Cloudflare R2
    print("\n[2] Deploying Frontend to Cloudflare R2...")
    r2_script = "deploy_to_r2.py"
    if os.path.exists(r2_script):
        try:
            subprocess.run([sys.executable, r2_script], check=True)
        except subprocess.CalledProcessError as e:
            print(f"    -> ERROR: Cloudflare R2 deployment failed: {e}")
    else:
        print("    -> WARNING: deploy_to_r2.py not found in current directory. Skipping R2 deployment.")

    print("\n[2b] Deploying Frontend to Cloudflare Pages (Production)...")
    try:
        subprocess.run("npx wrangler pages deploy . --project-name nemesis-id-frontend --branch main", cwd=frontend_dir, check=True, shell=True)
    except Exception as e:
        print(f"    -> WARNING: Cloudflare Pages deployment failed: {e}. Skipping.")

    # 3. Deploy Backend (Cloudflare Native Migration - Omni-Architecture)
    print("\n[3] Backend Deployment (Cloudflare Omni-Architecture)")
    omni_deploy_dir = "local_deploy"
    
    print(f"    -> Running Omni-Architecture Provisioner from {omni_deploy_dir}...")
    try:
        subprocess.run([sys.executable, "deploy_all.py"], cwd=omni_deploy_dir, check=True)
        print("    -> Successfully provisioned infrastructure!")
    except Exception as e:
        print(f"    -> ERROR: Omni-Architecture provisioning failed: {e}")
        
    worker_dir = os.path.join(omni_deploy_dir, "nemesis-global-worker")
    print(f"    -> Deploying edge worker from {worker_dir}...")
    try:
        subprocess.run("npx wrangler deploy -c wrangler.toml", cwd=worker_dir, check=True, shell=True)
        print("    -> Successfully deployed backend to Cloudflare Workers!")
    except Exception as e:
        print(f"    -> ERROR: Cloudflare backend deployment failed: {e}")
        print("       (Ensure you have run 'npx wrangler login'!)")

    print("\n=== DEPLOYMENT COMPLETE ===")
    print("-> Frontend is live on Cloudflare Pages / R2.")
    print("-> Backend is live on Cloudflare Workers.")

if __name__ == "__main__":
    main()
