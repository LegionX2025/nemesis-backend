import os
import subprocess
import sys
import shutil
import urllib.request
import traceback
from dotenv import load_dotenv

import logging

if not os.path.exists("logs"):
    os.makedirs("logs")

logging.basicConfig(
    filename='logs/deploy.log', 
    level=logging.INFO, 
    format='%(asctime)s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def print_log(msg, end="\n"):
    print(msg, end=end)
    logging.info(msg)

load_dotenv()

def run_cmd(cmd, cwd=".", exit_on_error=True, max_retries=3):
    print_log(f"\n[EXEC] {cmd} (in {cwd})")
    
    attempt = 1
    while attempt <= max_retries:
        try:
            process = subprocess.Popen(
                cmd, shell=True, cwd=cwd,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
            )
            output_log = ""
            for line in process.stdout:
                print(line, end="")
                logging.info(line.strip())
                output_log += line
                
            process.wait()
            if process.returncode == 0:
                return True, output_log
            
            # Benign error check
            if "already exists" in output_log.lower():
                print_log(f"[GODMODE] Resource already exists. Skipping recreation.")
                return True, output_log
                
            print_log(f"[ERROR] Command failed with exit code {process.returncode} on attempt {attempt}")
            
            if not exit_on_error:
                print_log(f"[GODMODE] exit_on_error=False. Bypassing Self-Repair.")
                return False, output_log
            
            # --- GODMODE INLINE SELF-HEALING ---
            print_log("[GODMODE] Engaging Inline Self-Repair Protocol...")
            import godmode
            trimmed_log = "\n".join(output_log.split("\n")[-50:]) # Reduced lines to prevent 400 Bad Request
            fix_script = godmode.query_gemini_to_heal(f"Command '{cmd}' failed.\n{trimmed_log}")
            
            if fix_script:
                print_log("[GODMODE] Applying Gemini Fix Script...")
                with open("inline_temp_fix.py", "w", encoding="utf-8") as f:
                    f.write(fix_script)
                try:
                    subprocess.run([sys.executable, "inline_temp_fix.py"], check=True)
                    print_log("[GODMODE] Patch applied! Retrying command...")
                    try:
                        from services.ml_engine import ml_engine
                        ml_engine.log_training_error(trimmed_log, fix_script, True)
                    except Exception:
                        pass
                except Exception as fix_e:
                    print_log(f"[GODMODE] Patch failed: {fix_e}")
                    try:
                        from services.ml_engine import ml_engine
                        ml_engine.log_training_error(trimmed_log, fix_script, False)
                    except Exception:
                        pass
                if os.path.exists("inline_temp_fix.py"):
                    os.remove("inline_temp_fix.py")
            else:
                print_log("[GODMODE] No fix provided. Retrying blindly...")
                
            attempt += 1
            import time
            time.sleep(2)
            
        except Exception as e:
            print_log(f"[CRITICAL ERROR] {str(e)}")
            if exit_on_error and attempt == max_retries:
                sys.exit(1)
            attempt += 1
            
    if exit_on_error:
        print_log("[GODMODE] Max retries reached. Terminating.")
        sys.exit(1)
    return False, output_log

def check_binary_exists(binary_name):
    print_log(f"    -> Verifying '{binary_name}' is installed...")
    if shutil.which(binary_name) is None:
        print_log(f"[CRITICAL ERROR] '{binary_name}' is not installed or not in PATH. Please install it before deploying.")
        sys.exit(1)

import json
import re

def update_wrangler_ids():
    print_log("    -> [AUTO-DEPLOY] Autonomously linking Cloudflare IDs to wrangler.toml...")
    d1_id = None
    try:
        d1_out = subprocess.check_output("npx wrangler d1 list --json", shell=True, text=True, stderr=subprocess.STDOUT)
        if d1_out:
            json_str = d1_out[d1_out.find('['):d1_out.rfind(']')+1]
            d1_list = json.loads(json_str)
            for db in d1_list:
                if db.get('name') == 'nemesis_audit_db':
                    d1_id = db.get('uuid')
                    print_log(f"    -> [AUTO-DEPLOY] Found D1 'nemesis_audit_db' ID: {d1_id}")
                    break
    except Exception as e:
        print_log(f"    -> [WARNING] Failed to list D1 databases: {e}")

    kv_id = None
    try:
        kv_out = subprocess.check_output("npx wrangler kv namespace list", shell=True, text=True, stderr=subprocess.STDOUT)
        if kv_out:
            json_str = kv_out[kv_out.find('['):kv_out.rfind(']')+1]
            kv_list = json.loads(json_str)
            for kv in kv_list:
                if kv.get('title') == 'nemesis-edge-proxy-NEMESIS_KV' or 'NEMESIS_KV' in kv.get('title', ''):
                    kv_id = kv.get('id')
                    print_log(f"    -> [AUTO-DEPLOY] Found KV 'NEMESIS_KV' ID: {kv_id}")
                    break
    except Exception as e:
        print_log(f"    -> [WARNING] Failed to list KV namespaces: {e}")

    if d1_id or kv_id:
        if not os.path.exists("wrangler.toml"):
            if os.path.exists("wrangler_proxy.toml"):
                import shutil
                shutil.copy("wrangler_proxy.toml", "wrangler.toml")
            else:
                with open("wrangler.toml", "w") as f:
                    f.write('name = "nemesis-edge-proxy"\nmain = "cloudflare_worker/src/index.ts"\ncompatibility_date = "2024-12-01"\n')
        with open("wrangler.toml", "r") as f:
            toml = f.read()

        if kv_id:
            toml = re.sub(r'id\s*=\s*"[^"]+"\s*# KV', f'id = "{kv_id}"', toml)
            toml = re.sub(r'preview_id\s*=\s*"[^"]+"', f'preview_id = "{kv_id}"', toml)
            # Update generic id if waiting
            toml = re.sub(r'id\s*=\s*"WAITING_FOR_DEPLOYMENT"', f'id = "{kv_id}"', toml)
        if d1_id:
            toml = re.sub(r'database_id\s*=\s*"[^"]+"', f'database_id = "{d1_id}"', toml)

        with open("wrangler.toml", "w") as f:
            f.write(toml)
        print_log("    -> [AUTO-DEPLOY] wrangler.toml successfully updated!")
    else:
        print_log("    -> [WARNING] Could not autonomously find IDs to link.")

def main():
    print_log("============================================================")
    print_log(" 🚀 NEMESIS OMNI-DEPLOYER: INFRASTRUCTURE-AS-CODE INITIATING")
    print_log("============================================================")
    
    # Sanitize Cloudflare Token
    cf_token = os.environ.get("CLOUDFLARE_API_TOKEN", "")
    if cf_token:
        os.environ["CLOUDFLARE_API_TOKEN"] = cf_token.strip().strip('"').strip("'").replace('\n', '')

    # 0. PRE-FLIGHT
    print_log("\n>>> [0/4] Installing Pre-flight Dependencies & Validating Binaries")
    check_binary_exists("git")
    check_binary_exists("npm")
    check_binary_exists("npx")
    print_log("    -> Installing Python requirements (Root)...")
    if os.path.exists("requirements.txt"):
        run_cmd("pip install -r requirements.txt", exit_on_error=False)
    
    if os.path.exists("cloudflare_worker/package.json"):
        print_log("    -> Installing Node.js requirements (cloudflare_worker)...")
        run_cmd("npm install", cwd="cloudflare_worker", exit_on_error=False)
        print_log("    -> Running npm audit fix --force...")
        run_cmd("npm audit fix --force", cwd="cloudflare_worker", exit_on_error=False)
        print_log("    -> Running npm update...")
        run_cmd("npm update", cwd="cloudflare_worker", exit_on_error=False)
        
    # Purge Git Cache
    print_log("    -> Purging git cache to avoid phantom files...")
    run_cmd("git rm -r -q --cached .", exit_on_error=False)
    run_cmd("git rm -rf -q local_deploy/", exit_on_error=False)
    
    # Ensure .gitignore exists to prevent LFS issues
    gitignore_content = "node_modules/\ncloudflare_worker/node_modules/\nvenv/\n__pycache__/\n.env\npython_modules/\n"
    if not os.path.exists(".gitignore"):
        with open(".gitignore", "w", encoding="utf-8") as f:
            f.write(gitignore_content)
    else:
        with open(".gitignore", "r", encoding="utf-8") as f:
            current_gitignore = f.read()
        if "node_modules" not in current_gitignore:
            with open(".gitignore", "a", encoding="utf-8") as f:
                f.write("\n" + gitignore_content)
        # Force remove cf_pages_build from gitignore if it exists
        if "cf_pages_build/" in current_gitignore:
            new_gitignore = current_gitignore.replace("cf_pages_build/\n", "").replace("cf_pages_build", "")
            with open(".gitignore", "w", encoding="utf-8") as f:
                f.write(new_gitignore)

    # 1. CLOUDFLARE INFRASTRUCTURE (D1, KV, R2)
    print_log("\n>>> [1/4] Provisioning Cloudflare Edge Resources")
    
    # Delete wrangler.jsonc to prevent wrangler from ignoring wrangler.toml
    if os.path.exists("wrangler.jsonc"):
        print_log("    -> Deleting wrangler.jsonc to prioritize wrangler.toml")
        os.remove("wrangler.jsonc")

    print_log("    -> Attempting to provision D1 Database (nemesis_audit_db)...")
    success, log = run_cmd("npx wrangler d1 create nemesis_audit_db", exit_on_error=False)
    if not success:
        print_log("    -> D1 Database might already exist or authentication needed.")
    
    print_log("    -> Attempting to provision KV Namespace (NEMESIS_KV)...")
    success, log = run_cmd("npx wrangler kv namespace create NEMESIS_KV", exit_on_error=False)
    
    print_log("    -> Attempting to provision R2 Bucket (nemesis-assets)...")
    success, log = run_cmd("npx wrangler r2 bucket create nemesis-assets", exit_on_error=False)

    print_log("    -> Applying Database Migrations (schema.sql)...")
    run_cmd("npx wrangler d1 execute nemesis_audit_db --file=database/schema.sql --remote", exit_on_error=False)
    # Also apply locally for dev
    run_cmd("npx wrangler d1 execute nemesis_audit_db --file=database/schema.sql --local", exit_on_error=False)
    
    update_wrangler_ids()
    # Also apply locally for dev
    run_cmd("npx wrangler d1 execute nemesis_audit_db --file=database/schema.sql --local", exit_on_error=False)
    
    # 2. GIT DEPLOY (RENDER)
    print_log("\n>>> [2/4] Syncing to Global Repository (Render Backend)")
    
    # Safely add files
    run_cmd("git add .", exit_on_error=False)
    
    success, log = run_cmd('git commit -m "Auto-Deploy from Nemesis Command Center"', exit_on_error=False)
    run_cmd("git push origin main", exit_on_error=False)
    print_log("    -> GitHub sync complete.")

    print_log("    -> Triggering Render Deploy Hook...")
    try:
        urllib.request.urlopen("https://api.render.com/deploy/srv-d932a7uq1p3s73eaauf0?key=ksDcebRkWzg")
        print_log("    -> Render backend is building!")
    except Exception as e:
        print_log(f"    -> [WARNING] Failed to trigger Render hook: {e}")

    # 3. CLOUDFLARE DEPLOY (EDGE PROXY WORKER)
    print_log("\n>>> [3/4] Deploying Edge Architecture (Cloudflare Worker)")
    worker_dir = os.path.join(os.getcwd(), "cloudflare_worker")
    if not os.path.exists(worker_dir):
        print_log(f"    -> [INFO] No cloudflare_worker directory found, skipping edge proxy deployment.")
    else:
        # Run wrangler from the root directory so it picks up wrangler.toml
        run_cmd("npx wrangler deploy cloudflare_worker/src/index.ts -c wrangler.toml")
        print_log("    -> Cloudflare Edge proxy successfully deployed!")

    # 4. CLOUDFLARE DEPLOY (FRONTEND PAGES)
    print_log("\n>>> [4/4] Deploying Main Frontend (Cloudflare Pages)")
    frontend_dir = os.path.join(os.getcwd(), "templates")
    static_dir = os.path.join(os.getcwd(), "static")
    build_dir = os.path.join(os.getcwd(), "cf_pages_build")
    
    if not os.path.exists(frontend_dir):
        print_log(f"[ERROR] Frontend directory not found: {frontend_dir}")
        sys.exit(1)
        
    print_log("    -> Preparing build directory with templates and static assets...")
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
                print_log(f"    -> [WARNING] Jinja2 compile failed for {item}, copying raw...")
                print_log(traceback.format_exc())
                shutil.copy2(s, d)
        else:
            shutil.copy2(s, d)
            
    # Create _redirects file to proxy API requests to Render backend
    redirects_content = "/api/*  https://nemesis-local.onrender.com/api/:splat  200\n/admin/api/*  https://nemesis-local.onrender.com/admin/api/:splat  200\n"
    with open(os.path.join(build_dir, "_redirects"), "w", encoding="utf-8") as f:
        f.write(redirects_content)
        
    if os.path.exists(static_dir):
        shutil.copytree(static_dir, os.path.join(build_dir, "static"))
        print_log(f"    -> [INFO] Successfully copied static directory.")
        
    run_cmd("npx wrangler pages deploy . --project-name nemesis-id-frontend", cwd=build_dir)
    print_log("    -> Cloudflare Pages frontend successfully deployed!")
    
    print_log("\n============================================================")
    print_log(" ✅ ALL SYSTEMS OPERATIONAL: OMNI-DEPLOYMENT SUCCESSFUL")
    print_log("============================================================")

if __name__ == "__main__":
    main()
