import os
import subprocess
import sys
import urllib.request

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
    print(" 🚀 NEMESIS OMNI-DEPLOYER (LOCAL_DEPLOY FOCUSED)")
    print("============================================================")
    
    # Ensure we are operating with relative paths correctly
    current_dir = os.getcwd()
    
    # 1. GIT DEPLOY (RENDER)
    print("\n>>> [1/3] Syncing to Global Repository (Render Backend)")
    print("    -> Restoring local_deploy files to git index...")
    run_cmd("git add .", cwd=current_dir)
    
    success, log = run_cmd('git commit -m "Auto-Deploy from Nemesis Command Center (local_deploy)"', cwd=current_dir, exit_on_error=False)
    if not success and "nothing to commit" in log.lower():
        print("    -> No new backend changes to commit. Proceeding to push...")
        
    run_cmd("git push origin main", cwd=current_dir)
    print("    -> GitHub sync complete.")

    print("    -> Triggering Render Deploy Hook...")
    try:
        urllib.request.urlopen("https://api.render.com/deploy/srv-d932a7uq1p3s73eaauf0?key=ksDcebRkWzg")
        print("    -> Render backend is building!")
    except Exception as e:
        print(f"    -> [WARNING] Failed to trigger Render hook: {e}")

    # 2. CLOUDFLARE DEPLOY (EDGE PROXY)
    print("\n>>> [2/3] Deploying Edge Architecture (Cloudflare Worker)")
    worker_dir = os.path.join(current_dir, "nemesis-global-worker")
    if os.path.exists(worker_dir):
        if os.path.exists(os.path.join(worker_dir, "package.json")):
            print("    -> Installing Node.js requirements...")
            run_cmd("npm install", cwd=worker_dir, exit_on_error=False)
        run_cmd("npx wrangler deploy src/index.ts -c wrangler.toml --compatibility-date 2024-12-01", cwd=worker_dir)
        print("    -> Cloudflare Edge proxy successfully deployed!")
    else:
        print(f"    -> [WARNING] Worker directory not found: {worker_dir}")

    # 3. CLOUDFLARE DEPLOY (FRONTEND)
    print("\n>>> [3/3] Deploying Main Frontend (Cloudflare Pages)")
    frontend_dir = os.path.join(current_dir, "templates")
    if os.path.exists(frontend_dir):
        run_cmd("npx wrangler pages deploy . --project-name nemesis-id-frontend", cwd=frontend_dir)
        print("    -> Cloudflare Pages frontend successfully deployed!")
    else:
        print(f"    -> [WARNING] Frontend directory not found: {frontend_dir}")
    
    print("\n============================================================")
    print(" ✅ ALL SYSTEMS OPERATIONAL: DEPLOYMENT SUCCESSFUL")
    print("============================================================")

if __name__ == "__main__":
    main()
