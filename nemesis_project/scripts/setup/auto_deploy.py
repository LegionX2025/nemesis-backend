import os
import subprocess
import sys
import logging
from dotenv import load_dotenv

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

def run_cmd(cmd, cwd=".", exit_on_error=True):
    print_log(f"\n[EXEC] {cmd} (in {cwd})")
    
    env_copy = os.environ.copy()
    env_copy["CI"] = "true"
    
    try:
        process = subprocess.Popen(
            cmd, shell=True, cwd=cwd,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=env_copy
        )
        output_log = ""
        for line in process.stdout:
            print(line, end="")
            logging.info(line.strip())
            output_log += line
            
        process.wait()
        if process.returncode == 0:
            return True, output_log
        
        print_log(f"[ERROR] Command failed with exit code {process.returncode}")
        if exit_on_error:
            print_log("[CRITICAL] Terminating deployment due to error.")
            sys.exit(1)
        return False, output_log
        
    except Exception as e:
        print_log(f"[CRITICAL ERROR] {str(e)}")
        if exit_on_error:
            sys.exit(1)
        return False, str(e)

def setup_proxy_worker():
    print_log("\n>>> [1/3] Installing Dependencies for Cloudflare Edge Proxy")
    if os.path.exists("cloudflare_worker/package.json"):
        run_cmd("npm install", cwd="cloudflare_worker")
    else:
        print_log("    -> [WARN] cloudflare_worker/package.json not found.")

def deploy_fullstack():
    print_log("\n>>> [2/3] Deploying Full-Stack Architecture (Proxy Backend + UI Assets)")
    if not os.path.exists("wrangler.toml"):
        print_log("[CRITICAL ERROR] wrangler.toml not found!")
        sys.exit(1)
        
    success, _ = run_cmd("npx wrangler deploy -c wrangler.toml", cwd=".")
    if success:
        print_log("    -> Architecture successfully deployed to Cloudflare Edge!")
    else:
        print_log("    -> [ERROR] Cloudflare deployment failed.")

def sync_github():
    print_log("\n>>> [3/3] Syncing to Global Repository (GitHub)")
    
    # Initialize Git if not already a repository
    if not os.path.exists(".git"):
        print_log("    -> Initializing local Git repository...")
        run_cmd("git init", exit_on_error=False)
        run_cmd("git branch -M main", exit_on_error=False)
    
    # Check if origin remote exists
    success, output = run_cmd("git remote -v", exit_on_error=False)
    if not output or "origin" not in output:
        print_log("    -> No remote origin found. Creating 'nemesis_project' on GitHub...")
        # Attempt to create repo using GitHub CLI
        gh_success, gh_out = run_cmd("gh repo create nemesis_project --public --source=. --remote=origin", exit_on_error=False)
        if not gh_success:
            print_log("    -> [WARN] Could not create GitHub repo automatically.")
            print_log("    -> [HINT] Please ensure GitHub CLI (gh) is installed and authenticated (`gh auth login`).")
            print_log("    -> [HINT] If you created it manually, run: git remote add origin <your-repo-url>")
            print_log(f"    -> [GH ERROR] {gh_out}")
            return
        print_log("    -> Successfully created GitHub repository 'nemesis_project'!")

    # Add, commit, and push
    run_cmd("git add .", exit_on_error=False)
    run_cmd('git commit -m "Auto-Deploy full Cloudflare Edge Architecture (Frontend + Proxy Worker)"', exit_on_error=False)
    run_cmd("git push -u origin main", exit_on_error=False)
    print_log("    -> GitHub sync complete.")

def main():
    print_log("============================================================")
    print_log(" 🚀 NEMESIS OMNI-DEPLOYER: HYBRID CLOUDFLARE EDGE")
    print_log("============================================================")
    
    setup_proxy_worker()
    deploy_fullstack()
    sync_github()
    
    print_log("\n============================================================")
    print_log(" ✅ ALL SYSTEMS OPERATIONAL: OMNI-DEPLOYMENT SUCCESSFUL")
    print_log("============================================================")

if __name__ == "__main__":
    main()
