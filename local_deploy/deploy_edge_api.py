import os
import subprocess

FRONTEND_DIR = r"c:\Users\LEGIONX\Downloads\cases\local_deploy\frontend"
WORKER_DIR = os.path.join(FRONTEND_DIR, "nemesis-global-worker")

def replace_in_files(directory):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".html") or file.endswith(".js"):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        content = f.read()
                    
                    if "nemesis-backend.legionxgaming2021.workers.dev" in content:
                        new_content = content.replace("nemesis-backend.legionxgaming2021.workers.dev", "nemesis-api.legionxgaming2021.workers.dev")
                        with open(filepath, "w", encoding="utf-8") as f:
                            f.write(new_content)
                        print(f"Reverted URLs in: {filepath}")
                except Exception as e:
                    print(f"Failed to process {filepath}: {e}")

print("--- FIXING FRONTEND URLs ---")
replace_in_files(FRONTEND_DIR)

print("\n--- DEPLOYING TYPESCRIPT EDGE API (nemesis-api) ---")
env = os.environ.copy()
if "CLOUDFLARE_API_TOKEN" in env:
    del env["CLOUDFLARE_API_TOKEN"]

subprocess.run(["npm", "install"], cwd=WORKER_DIR, shell=True)
subprocess.run(["npx", "wrangler", "deploy"], cwd=WORKER_DIR, env=env, shell=True)

print("\n--- DEPLOYING FRONTEND PAGES ---")
subprocess.run(["npx", "wrangler", "pages", "deploy", ".", "--project-name", "nemesis-id-frontend"], cwd=FRONTEND_DIR, env=env, shell=True)

print("\n--- DEPLOYMENT FINISHED ---")
