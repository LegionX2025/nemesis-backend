import os
import subprocess

def fix_git():
    print("Adding files to git...")
    
    core_files = [
        "cloudflare_worker", "cf_pages_build",
        "render_backend", "services", "templates", "static", "scraper_service", "graph",
        "database", "requirements.txt", "render.yaml", "auto_deploy.py", "deploy_all.py", 
        "build_nemesis_id.py", "app.py", "main.py", "Dockerfile", ".gitignore", "wrangler.toml", "vercel.json"
    ]
    
    for f in core_files:
        if os.path.exists(f):
            print(f"Adding {f}...")
            subprocess.run(f"git add -f {f}", shell=True)
            
    print("Committing...")
    subprocess.run('git commit -m "Restore all core files to repository"', shell=True)
    
    print("Pushing to origin main...")
    subprocess.run("git push origin main", shell=True)
    print("Done!")

if __name__ == "__main__":
    fix_git()
