import os
import subprocess
import sys

def run_cmd(cmd, cwd=None, exit_on_error=True):
    print(f"\n[EXEC] {cmd}" + (f" (in {cwd})" if cwd else ""))
    try:
        # Use shell=True for windows convenience, stream output
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
    print(" 🚀 NEMESIS OMNI-DEPLOYER: INITIATING UPLINK")
    print("============================================================")
    
    # 1. GIT DEPLOY (RENDER)
    print("\n>>> [1/3] Syncing to Global Repository (Render Backend)")
    print("    -> Wiping git cache to ensure strict project-file-only deployment...")
    run_cmd("git rm -r --cached .", exit_on_error=False)
    
    print("    -> Adding strict core project files...")
    core_files = [
        "local_deploy/", "cloudflare_frontend/", "cloudflare_worker/", 
        "render_backend/", "services/", "templates/", "static/", "scraper_service/", "graph/",
        "requirements.txt", "render.yaml", "auto_deploy.py", "deploy_all.py", 
        "build_nemesis_id.py", "app.py", "main.py", "Dockerfile", ".gitignore"
    ]
    for f in core_files:
        if os.path.exists(os.path.join(os.getcwd(), f.strip("/"))):
            run_cmd(f"git add {f}")
    
    # Commit might fail if there are no changes, so we don't exit on error
    success, log = run_cmd('git commit -m "Auto-Deploy from Nemesis Command Center"', exit_on_error=False)
    if not success and "nothing to commit" in log.lower():
        print("    -> No new backend changes to commit. Proceeding to push...")
        
    run_cmd("git push origin main")
    print("    -> GitHub sync complete.")

    print("    -> Triggering Render Deploy Hook...")
    import urllib.request
    try:
        urllib.request.urlopen("https://api.render.com/deploy/srv-d932a7uq1p3s73eaauf0?key=ksDcebRkWzg")
        print("    -> Render backend is building!")
    except Exception as e:
        print(f"    -> [WARNING] Failed to trigger Render hook: {e}")

    # 2. CLOUDFLARE DEPLOY (EDGE PROXY)
    print("\n>>> [2/3] Deploying Edge Architecture (Cloudflare Worker)")
    worker_dir = os.path.join(os.getcwd(), "local_deploy", "nemesis-global-worker")
    if not os.path.exists(worker_dir):
        print(f"[ERROR] Worker directory not found: {worker_dir}")
        sys.exit(1)
        
    run_cmd("npx wrangler deploy src/index.ts -c wrangler.toml --compatibility-date 2024-12-01", cwd=worker_dir)
    print("    -> Cloudflare Edge proxy successfully deployed!")

    # 3. CLOUDFLARE DEPLOY (FRONTEND)
    print("\n>>> [3/3] Deploying Main Frontend (Cloudflare Pages)")
    frontend_dir = os.path.join(os.getcwd(), "cloudflare_frontend")
    if not os.path.exists(frontend_dir):
        print(f"[ERROR] Frontend directory not found: {frontend_dir}")
        sys.exit(1)
        
    run_cmd("npx wrangler pages deploy . --project-name nemesis-id-frontend", cwd=frontend_dir)
    print("    -> Cloudflare Pages frontend successfully deployed!")
    
    print("\n============================================================")
    print(" ✅ ALL SYSTEMS OPERATIONAL: DEPLOYMENT SUCCESSFUL")
    print("============================================================")

if __name__ == "__main__":
    main()
