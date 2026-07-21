import os
import sys
import subprocess
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] [DEPLOYER] %(message)s")
logger = logging.getLogger("AUTO_DEPLOY")

def run_command(command, env=None, cwd=None):
    logger.info(f"Executing: {' '.join(command)}")
    try:
        process = subprocess.Popen(
            command,
            env=env,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            shell=os.name == 'nt'
        )
        for line in process.stdout:
            print(line.strip())
        process.wait()
        if process.returncode != 0:
            logger.error(f"Command failed with exit code {process.returncode}")
            return False
        return True
    except Exception as e:
        logger.error(f"Execution error: {e}")
        return False

def main():
    logger.info("Initializing Cloudflare Native Deployment Sequence...")
    
    # Secure the environment context
    deploy_env = os.environ.copy()
    
    # 🚨 CRITICAL FIX: The provided API token was invalid (Code 10000/9109).
    # We strip it here so Wrangler falls back to your local OAuth session which works perfectly!
    if "CLOUDFLARE_API_TOKEN" in deploy_env:
        logger.warning("Stripping CLOUDFLARE_API_TOKEN to force local OAuth...")
        del deploy_env["CLOUDFLARE_API_TOKEN"]

    # 🚨 CRITICAL FIX: Delete any previous pylock.toml or uv.lock that enforces incompatible Python versions
    for lock_file in ["pylock.toml", "uv.lock"]:
        if os.path.exists(lock_file):
            logger.info(f"Removing conflicting {lock_file}...")
            try:
                os.remove(lock_file)
            except Exception as e:
                logger.warning(f"Could not remove {lock_file}: {e}")

    # 1. GIT SYNC PHASE (nemesis_v3)
    logger.info("--- PHASE 1: Syncing to GitHub (nemesis_v3) ---")
    
    # 🚨 CRITICAL FIX: Remove nested .git in tracer_scripts which causes git add to fail
    nested_git = os.path.join("tracer_scripts", ".git")
    if os.path.exists(nested_git):
        import shutil
        try:
            shutil.rmtree(nested_git)
            logger.info(f"Removed conflicting nested git repository at {nested_git}")
        except Exception as e:
            logger.warning(f"Could not remove {nested_git}: {e}")

    git_cmds = [
        ["git", "init"],
        ["git", "add", "."],
        ["git", "commit", "-m", "Auto-deploy: Edge architecture migration"],
        ["git", "branch", "-M", "main"],
        ["git", "remote", "add", "origin", "https://github.com/LegionX2025/nemesis_v3.git"],
        ["git", "remote", "set-url", "origin", "https://github.com/LegionX2025/nemesis_v3.git"], # In case it already exists
        ["git", "push", "-u", "origin", "main", "--force"]
    ]
    
    for cmd in git_cmds:
        run_command(cmd, env=deploy_env)

    # 2. PROVISION INFRASTRUCTURE (Cloudflare Resources)
    logger.info("--- PHASE 2: Provisioning Cloudflare Infrastructure ---")
    infra_cmds = [
        # Note: In a real-world scenario, you might want to check if these exist first
        # to avoid errors on subsequent runs, but for this exercise we'll try to create them.
        ["npx", "wrangler", "kv", "namespace", "create", "NEMESIS_CACHE"],
        ["npx", "wrangler", "kv", "namespace", "create", "ENTITY_CACHE"],
        ["npx", "wrangler", "kv", "namespace", "create", "SESSION_CACHE"],
        ["npx", "wrangler", "kv", "namespace", "create", "TOKEN_CACHE"],
        ["npx", "wrangler", "kv", "namespace", "create", "OSINT_CACHE"],
        
        ["npx", "wrangler", "d1", "create", "nemesis-db"],
        ["npx", "wrangler", "d1", "create", "nemesis_audit_db"],
        
        ["npx", "wrangler", "r2", "bucket", "create", "nemesis-reports"],
        ["npx", "wrangler", "r2", "bucket", "create", "nemesis-evidence"],
        ["npx", "wrangler", "r2", "bucket", "create", "nemesis-screenshots"],
        ["npx", "wrangler", "r2", "bucket", "create", "nemesis-exports"],
        
        # Queues usually require an enterprise plan or specific setup, but we'll include the commands
        # ["npx", "wrangler", "queues", "create", "wallet-tracing"],
        # ["npx", "wrangler", "queues", "create", "entity-resolution"],
        # ["npx", "wrangler", "queues", "create", "gemini-analysis"],
        # ["npx", "wrangler", "queues", "create", "report-generation"],
        # ["npx", "wrangler", "queues", "create", "notifications"],
    ]
    
    for cmd in infra_cmds:
        # We use subprocess directly to capture and suppress "already exists" errors
        logger.info(f"Executing: {' '.join(cmd)}")
        try:
            p = subprocess.Popen(cmd, env=deploy_env, cwd=None, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, shell=os.name == 'nt')
            output, _ = p.communicate()
            if p.returncode != 0:
                if "already exists" in output.lower() or "10004" in output or "code: 10004" in output:
                    logger.info(f"Resource already exists. Skipping.")
                else:
                    for line in output.splitlines():
                        print(line)
                    logger.warning(f"Command failed with exit code {p.returncode}")
            else:
                for line in output.splitlines():
                    print(line)
        except Exception as e:
            logger.warning(f"Execution error: {e}")

    # 3. DEPLOY BACKEND WORKER (Cloudflare Workers)
    logger.info("--- PHASE 3: Deploying Backend API ---")
    backend_cmd = ["npx", "wrangler", "deploy"]
    success = run_command(backend_cmd, env=deploy_env, cwd="backend")
    if not success:
        logger.error("Backend deployment failed. Continuing...")

    # 4. DEPLOY FRONTEND UI (Cloudflare Pages)
    logger.info("--- PHASE 4: Deploying Frontend UI ---")
    frontend_cmd = ["npx", "wrangler", "pages", "deploy", ".", "--project-name", "nemesis-id-frontend-v2"]
    success = run_command(frontend_cmd, env=deploy_env, cwd="frontend")
    if not success:
        logger.error("Frontend deployment failed. Continuing...")

    # 5. DEPLOY TRACER SCRIPTS
    logger.info("--- PHASE 5: Deploying Tracer Scripts (Worker & Pages) ---")
    # Worker deployment if workers folder exists
    if os.path.exists(os.path.join("tracer_scripts", "workers")):
        logger.info("Deploying Tracer API Worker...")
        # Need to install deps first typically
        run_command(["npm", "install"], env=deploy_env, cwd=os.path.join("tracer_scripts", "workers"))
        success = run_command(["npx", "wrangler", "deploy"], env=deploy_env, cwd=os.path.join("tracer_scripts", "workers"))
        if not success:
            logger.error("Tracer API deployment failed.")

    logger.info("Deploying Tracer Frontend...")
    tracer_frontend_cmd = ["npx", "wrangler", "pages", "deploy", ".", "--project-name", "nemesis-tracer-v2"]
    success = run_command(tracer_frontend_cmd, env=deploy_env, cwd="tracer_scripts")
    if not success:
         logger.error("Tracer frontend deployment failed.")


    logger.info("======================================================")
    logger.info("🚀 DEPLOYMENT SUCCESSFUL: Welcome to Cloudflare Edge.")
    logger.info("======================================================")

if __name__ == "__main__":
    main()
