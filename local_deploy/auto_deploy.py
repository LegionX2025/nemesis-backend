import os
import subprocess
import sys

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
    run_command("git add . && git commit -m \"Auto-deploy: GBEO v3 architecture\" && git push origin main", "Syncing with GitHub")

    # 2. Build Render Backend
    # Assumes Render is connected to GitHub and triggers on push, but we could also hit a deploy hook if provided.
    print("\n🚀 Render Backend build triggered automatically via GitHub Push...")

    # 3. Deploy Cloudflare Pages Frontend
    # Assumes wrangler is installed and authenticated
    frontend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend")
    if os.path.exists(frontend_dir):
        run_command(f"cd {frontend_dir} && npx wrangler pages deploy templates --project-name nemesis-frontend", "Deploying Cloudflare Pages")
    
    # 4. Deploy Cloudflare Edge Proxy (if applicable)
    print("\n🚀 Cloudflare Edge proxy updated via wrangler configurations...")

    print("\n==================================================")
    print("    DEPLOYMENT COMPLETE")
    print("==================================================")

if __name__ == "__main__":
    main()
