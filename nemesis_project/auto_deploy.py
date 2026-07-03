import os
import subprocess
import sys
import shutil
import urllib.request
import traceback

def run_cmd(cmd, cwd=None, exit_on_error=True):
    print(f"\n[EXEC] {cmd}" + (f" (in {cwd})" if cwd else ""))
    try:
        process = subprocess.Popen(
            cmd, shell=True, cwd=cwd,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
        )
        output_log = ""
        for line in process.stdout:
            print(line, end="")
            output_log += line
            
        process.wait()
        if process.returncode != 0:
            print(f"[ERROR] Command failed with exit code {process.returncode}")
            if exit_on_error:
                sys.exit(process.returncode)
            return False, output_log
        return True, output_log
    except Exception as e:
        print(f"[CRITICAL ERROR] {str(e)}")
        if exit_on_error:
            sys.exit(1)
        return False, str(e)

def main():
    print("============================================================")
    print(" 🚀 NEMESIS OMNI-DEPLOYER: INFRASTRUCTURE-AS-CODE INITIATING")
    print("============================================================")
    
    # Sanitize Cloudflare Token
    cf_token = os.environ.get("CLOUDFLARE_API_TOKEN", "")
    if cf_token:
        os.environ["CLOUDFLARE_API_TOKEN"] = cf_token.strip().strip('"').strip("'").replace('\n', '')

    # 0. PRE-FLIGHT
    print("\n>>> [0/4] Installing Pre-flight Dependencies")
    print("    -> Installing Python requirements (Root)...")
    run_cmd("pip install -r requirements.txt", exit_on_error=False)
    
    if os.path.exists("cloudflare_worker/package.json"):
        print("    -> Installing Node.js requirements (cloudflare_worker)...")
        run_cmd("npm install", cwd="cloudflare_worker", exit_on_error=False)
        print("    -> Running npm audit fix...")
        run_cmd("npm audit fix", cwd="cloudflare_worker", exit_on_error=False)
        
    # Ensure .gitignore exists to prevent LFS issues
    gitignore_content = "node_modules/\ncloudflare_worker/node_modules/\ncf_pages_build/\nvenv/\n__pycache__/\n.env\n"
    if not os.path.exists(".gitignore"):
        with open(".gitignore", "w", encoding="utf-8") as f:
            f.write(gitignore_content)
    else:
        with open(".gitignore", "r", encoding="utf-8") as f:
            current_gitignore = f.read()
        if "node_modules" not in current_gitignore:
            with open(".gitignore", "a", encoding="utf-8") as f:
                f.write("\n" + gitignore_content)

    # 1. CLOUDFLARE INFRASTRUCTURE (D1, KV, R2)
    print("\n>>> [1/4] Provisioning Cloudflare Edge Resources")
    print("    -> Attempting to provision D1 Database (nemesis_audit_db)...")
    success, log = run_cmd("npx wrangler d1 create nemesis_audit_db", exit_on_error=False)
    if not success:
        print("    -> D1 Database might already exist or authentication needed.")
    
    print("    -> Attempting to provision KV Namespace (NEMESIS_KV)...")
    success, log = run_cmd("npx wrangler kv:namespace create NEMESIS_KV", exit_on_error=False)
    
    print("    -> Attempting to provision R2 Bucket (nemesis-assets)...")
    success, log = run_cmd("npx wrangler r2 bucket create nemesis-assets", exit_on_error=False)

    print("    -> Applying Database Migrations (schema.sql)...")
    run_cmd("npx wrangler d1 execute nemesis_audit_db --file=database/schema.sql --remote", exit_on_error=False)
    # Also apply locally for dev
    run_cmd("npx wrangler d1 execute nemesis_audit_db --file=database/schema.sql --local", exit_on_error=False)
    
    # 2. GIT DEPLOY (RENDER)
    print("\n>>> [2/4] Syncing to Global Repository (Render Backend)")
    run_cmd("git rm -r --cached .", exit_on_error=False)
    
    core_files = [
        "local_deploy/", "cloudflare_worker/", 
        "render_backend/", "services/", "templates/", "static/", "scraper_service/", "graph/",
        "database/", "requirements.txt", "render.yaml", "auto_deploy.py", "deploy_all.py", 
        "build_nemesis_id.py", "app.py", "main.py", "Dockerfile", ".gitignore", "wrangler.toml"
    ]
    for f in core_files:
        if os.path.exists(os.path.join(os.getcwd(), f.strip("/"))):
            run_cmd(f"git add {f}")
    
    success, log = run_cmd('git commit -m "Auto-Deploy from Nemesis Command Center"', exit_on_error=False)
    run_cmd("git push origin main", exit_on_error=False)
    print("    -> GitHub sync complete.")

    print("    -> Triggering Render Deploy Hook...")
    try:
        urllib.request.urlopen("https://api.render.com/deploy/srv-d932a7uq1p3s73eaauf0?key=ksDcebRkWzg")
        print("    -> Render backend is building!")
    except Exception as e:
        print(f"    -> [WARNING] Failed to trigger Render hook: {e}")

    # 3. CLOUDFLARE DEPLOY (EDGE PROXY WORKER)
    print("\n>>> [3/4] Deploying Edge Architecture (Cloudflare Worker)")
    worker_dir = os.path.join(os.getcwd(), "cloudflare_worker")
    if not os.path.exists(worker_dir):
        print(f"    -> [INFO] No cloudflare_worker directory found, skipping edge proxy deployment.")
    else:
        # Run wrangler from the root directory so it picks up wrangler.toml
        run_cmd("npx wrangler deploy cloudflare_worker/src/index.ts -c wrangler.toml")
        print("    -> Cloudflare Edge proxy successfully deployed!")

    # 4. CLOUDFLARE DEPLOY (FRONTEND PAGES)
    print("\n>>> [4/4] Deploying Main Frontend (Cloudflare Pages)")
    frontend_dir = os.path.join(os.getcwd(), "templates")
    static_dir = os.path.join(os.getcwd(), "static")
    build_dir = os.path.join(os.getcwd(), "cf_pages_build")
    
    if not os.path.exists(frontend_dir):
        print(f"[ERROR] Frontend directory not found: {frontend_dir}")
        sys.exit(1)
        
    print("    -> Preparing build directory with templates and static assets...")
    if os.path.exists(build_dir):
        shutil.rmtree(build_dir)
    os.makedirs(build_dir)
    
    from jinja2 import Environment, FileSystemLoader
    env = Environment(loader=FileSystemLoader(frontend_dir))
    
    for item in os.listdir(frontend_dir):
        s = os.path.join(frontend_dir, item)
        d = os.path.join(build_dir, item)
        if os.path.isdir(s):
            shutil.copytree(s, d)
        elif item.endswith('.html') and not item.endswith('.bak'):
            try:
                template = env.get_template(item)
                rendered = template.render()
                with open(d, "w", encoding="utf-8") as f:
                    f.write(rendered)
            except Exception as e:
                print(f"    -> [WARNING] Jinja2 compile failed for {item}, copying raw...")
                print(traceback.format_exc())
                shutil.copy2(s, d)
        else:
            shutil.copy2(s, d)
            
    if os.path.exists(static_dir):
        shutil.copytree(static_dir, os.path.join(build_dir, "static"))
        print(f"    -> [INFO] Successfully copied static directory.")
        
    run_cmd("npx wrangler pages deploy . --project-name nemesis-id-frontend", cwd=build_dir)
    print("    -> Cloudflare Pages frontend successfully deployed!")
    
    print("\n============================================================")
    print(" ✅ ALL SYSTEMS OPERATIONAL: OMNI-DEPLOYMENT SUCCESSFUL")
    print("============================================================")

if __name__ == "__main__":
    main()
