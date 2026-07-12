import os
import subprocess
import sys
import shutil
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

def check_binary_exists(binary_name):
    print_log(f"    -> Verifying '{binary_name}' is installed...")
    if shutil.which(binary_name) is None:
        print_log(f"[CRITICAL ERROR] '{binary_name}' is not installed or not in PATH. Please install it before deploying.")
        sys.exit(1)

def cleanup_worker_env():
    print_log("\n>>> [1/5] Cleaning up Python Worker Environment")
    if os.path.exists("python_modules"):
        print_log("    -> Removing python_modules directory (forces Cloudflare to use Pyodide WASM binaries)")
        shutil.rmtree("python_modules")
    
    for f in ["pyproject.toml", "pylock.toml", "uv.lock"]:
        if os.path.exists(f):
            print_log(f"    -> Removing {f} to prioritize requirements.txt")
            os.remove(f)

def deploy_backend():
    print_log("\n>>> [2/5] Deploying Nemesis Backend (Cloudflare Python Worker)")
    if not os.path.exists("wrangler.toml"):
        print_log("[CRITICAL ERROR] wrangler.toml not found!")
        sys.exit(1)
        
    # Inject CI=true to prevent interactive prompts from hanging
    env_copy = os.environ.copy()
    env_copy["CI"] = "true"
    
    print_log(f"\n[EXEC] npx wrangler deploy -c wrangler.toml (in .)")
    try:
        process = subprocess.Popen(
            "npx wrangler deploy -c wrangler.toml", shell=True, cwd=".",
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=env_copy
        )
        output_log = ""
        for line in process.stdout:
            print(line, end="")
            logging.info(line.strip())
            output_log += line
        process.wait()
        success = process.returncode == 0
    except Exception as e:
        success = False
        output_log = str(e)
        
    if success:
        print_log("    -> Backend successfully deployed to Cloudflare Edge!")
    else:
        print_log("    -> [ERROR] Backend deployment failed.")
        print_log("\n--- DEPLOYMENT LOG ---")
        print_log(output_log)
        print_log("----------------------\n")

def deploy_global_worker():
    print_log("\n>>> [3/6] Deploying Nemesis Global Worker (Orchestrator)")
    global_worker_dir = os.path.abspath(os.path.join("..", "local_deploy", "frontend", "nemesis-global-worker"))
    if not os.path.exists(global_worker_dir):
        print_log(f"    -> [WARN] Global worker directory not found at {global_worker_dir}. Skipping.")
        return
        
    env_copy = os.environ.copy()
    env_copy["CI"] = "true"
    
    print_log(f"\n[EXEC] npx wrangler deploy (in {global_worker_dir})")
    try:
        process = subprocess.Popen(
            "npx wrangler deploy", shell=True, cwd=global_worker_dir,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=env_copy
        )
        output_log = ""
        for line in process.stdout:
            print(line, end="")
            logging.info(line.strip())
            output_log += line
        process.wait()
        success = process.returncode == 0
    except Exception as e:
        success = False
        output_log = str(e)
        
    if success:
        print_log("    -> Global Worker successfully deployed to Cloudflare Edge!")
    else:
        print_log("    -> [ERROR] Global Worker deployment failed.")
        print_log("\n--- DEPLOYMENT LOG ---")
        print_log(output_log)
        print_log("----------------------\n")

def compile_and_deploy_frontend():
    print_log("\n>>> [4/6] Compiling Frontend (Resolving Jinja Tags)")
    success, _ = run_cmd("python compile_html.py")
    
    if not success:
        print_log("    -> [ERROR] Frontend compilation failed.")
        sys.exit(1)
        
    print_log("\n>>> [5/6] Deploying Nemesis Frontend (Cloudflare Pages)")
    success, _ = run_cmd("npx wrangler pages deploy frontend/ --project-name nemesis-id-frontend")
    if success:
        print_log("    -> Frontend successfully deployed to Cloudflare Pages!")
    else:
        print_log("    -> [ERROR] Frontend deployment failed.")

def sync_github():
    print_log("\n>>> [6/6] Syncing to Global Repository (GitHub)")
    run_cmd("git add .", exit_on_error=False)
    run_cmd('git commit -m "Auto-Deploy full Cloudflare Edge Architecture (Frontend + Backend + Global Worker)"', exit_on_error=False)
    run_cmd("git push origin main", exit_on_error=False)
    print_log("    -> GitHub sync complete.")

def main():
    print_log("============================================================")
    print_log(" 🚀 NEMESIS OMNI-DEPLOYER: 100% NATIVE CLOUDFLARE EDGE")
    print_log("============================================================")
    
    print_log("\n>>> [0/6] Validating Binaries")
    check_binary_exists("git")
    check_binary_exists("npm")
    check_binary_exists("npx")
    check_binary_exists("python")

    # Wipe Render references from Git if they somehow persist
    if os.path.exists("cf_pages_build/_redirects"):
        os.remove("cf_pages_build/_redirects")
        
    cleanup_worker_env()
    deploy_backend()
    deploy_global_worker()
    compile_and_deploy_frontend()
    sync_github()
    
    print_log("\n============================================================")
    print_log(" ✅ ALL SYSTEMS OPERATIONAL: OMNI-DEPLOYMENT SUCCESSFUL")
    print_log("============================================================")

if __name__ == "__main__":
    main()
