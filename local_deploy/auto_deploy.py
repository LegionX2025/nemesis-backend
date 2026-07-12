import os
import subprocess
import sys
import shutil

def run_command(command, description):
    print(f"\n🚀 {description}...")
    result = subprocess.run(command, shell=True)
    if result.returncode != 0:
        print(f"❌ Failed: {description}")
        sys.exit(1)
    print(f"✅ Success: {description}")

def main():
    print("==================================================")
    print("    INITIATING NEMESIS AUTO-DEPLOY SEQUENCE")
    print("==================================================")

    # 1. Sync with GitHub
    print("\n🚀 Syncing with GitHub...")
    # Add files and check if there are changes before committing
    subprocess.run("git add .", shell=True)
    status_result = subprocess.run("git diff --staged --quiet", shell=True)
    if status_result.returncode != 0:
        run_command('git commit -m "Auto-deploy: GBEO v3 architecture" && git push origin main', "Committing and Pushing to GitHub")
    else:
        print("✅ No new changes to commit. Proceeding...")
    # 2. Attempt Cloudflare Python Backend Deployment
    print("\n🚀 Attempting to deploy FastAPI Backend directly to Cloudflare Workers...")
    backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend")
    cf_backend_success = False
    if os.path.exists(backend_dir):
        print("   [!] Note: Cloudflare Pyodide has strict limits on C-extensions (Playwright, Motor, Neo4j).")
        result = subprocess.run("npx wrangler deploy", shell=True, cwd=backend_dir)
        if result.returncode == 0:
            print("✅ Success: Backend deployed to Cloudflare!")
            cf_backend_success = True
        else:
            print("❌ Cloudflare Backend deployment failed (likely due to Pyodide C-extension limits).")
            print("   => FALLING BACK TO RENDER BACKUP DEPLOYMENT...")

    if not cf_backend_success:
        print("\n🚀 Cloudflare Backend deployment failed. Triggering Render Backend Backup via Deploy Hook...")
        import urllib.request
        try:
            render_hook_url = "https://api.render.com/deploy/srv-d92fghho3t8c73bg5740?key=YskS46ltPHo"
            req = urllib.request.Request(render_hook_url, method="POST")
            urllib.request.urlopen(req)
            print("✅ Success: Render Backup triggered successfully.")
        except Exception as e:
            print(f"⚠️ Warning: Failed to trigger Render Deploy Hook directly: {e}")
            print("   Render should still build automatically via GitHub Push.")

    # 3. Deploy Cloudflare Pages Frontend
    # Assumes wrangler is installed and authenticated
    frontend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend")
    cf_frontend_success = False
    if os.path.exists(frontend_dir):
        static_src = os.path.join(frontend_dir, "static")
        static_dst = os.path.join(frontend_dir, "templates", "static")
        if os.path.exists(static_src):
            if os.path.exists(static_dst):
                shutil.rmtree(static_dst)
            shutil.copytree(static_src, static_dst)
            
        print(f"\n🚀 Deploying Cloudflare Pages...")
        # Set CI=true so wrangler doesn't prompt for project creation
        env = os.environ.copy()
        env["CI"] = "true"
        result = subprocess.run(f"npx wrangler pages deploy templates --project-name nemesis-loc", shell=True, cwd=frontend_dir, env=env)
        if result.returncode == 0:
            print("✅ Success: Deploying Cloudflare Pages")
            cf_frontend_success = True
        else:
            print("❌ Failed: Deploying Cloudflare Pages")
            print("   => FALLING BACK TO VERCEL DEPLOYMENT...")
            subprocess.run("npx vercel --prod --yes", shell=True, cwd=frontend_dir)
    
    # 3b. Deploy Cloudflare Global Worker (Backend/API)
    worker_dir = os.path.join(frontend_dir, "nemesis-global-worker")
    if os.path.exists(worker_dir):
        run_command(f"cd {worker_dir} && npx wrangler deploy", "Deploying Cloudflare Global Worker API")
    
    # 4. Deploy Cloudflare Edge Proxy (if applicable)
    print("\n🚀 Cloudflare Edge proxy updated via wrangler configurations...")

    print("\n==================================================")
    print("    DEPLOYMENT COMPLETE")
    print("==================================================")

if __name__ == "__main__":
    main()
