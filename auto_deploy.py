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
    print("\n>>> [1/2] Syncing to Global Repository (Render Backend)")
    run_cmd("git add .")
    
    # Commit might fail if there are no changes, so we don't exit on error
    success, log = run_cmd('git commit -m "Auto-Deploy from Nemesis Command Center"', exit_on_error=False)
    if not success and "nothing to commit" in log.lower():
        print("    -> No new backend changes to commit. Proceeding to push...")
        
    run_cmd("git push origin main")
    print("    -> GitHub sync complete. Render backend is building!")

    # 2. CLOUDFLARE DEPLOY (EDGE PROXY)
    print("\n>>> [2/2] Deploying Edge Architecture (Cloudflare Worker)")
    worker_dir = os.path.join(os.getcwd(), "local_deploy", "nemesis-global-worker")
    if not os.path.exists(worker_dir):
        print(f"[ERROR] Worker directory not found: {worker_dir}")
        sys.exit(1)
        
    run_cmd("npx wrangler deploy src/index.ts", cwd=worker_dir)
    print("    -> Cloudflare Edge proxy successfully deployed!")
    
    print("\n============================================================")
    print(" ✅ ALL SYSTEMS OPERATIONAL: DEPLOYMENT SUCCESSFUL")
    print("============================================================")

if __name__ == "__main__":
    main()
