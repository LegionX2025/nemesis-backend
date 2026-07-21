import os
import subprocess
import re

FRONTEND_DIR = r"c:\Users\LEGIONX\Downloads\cases\local_deploy\frontend"
TRACER_DIR = r"c:\Users\LEGIONX\Downloads\cases\local_deploy\tracer_scripts"
BACKEND_DIR = r"c:\Users\LEGIONX\Downloads\cases\local_deploy\backend"
BACKEND_WRANGLER = os.path.join(BACKEND_DIR, "wrangler.toml")

def replace_in_files(directory):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".html") or file.endswith(".js"):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        content = f.read()
                    
                    if "nemesis-api.legionxgaming2021.workers.dev" in content:
                        new_content = content.replace("nemesis-api.legionxgaming2021.workers.dev", "nemesis-backend.legionxgaming2021.workers.dev")
                        with open(filepath, "w", encoding="utf-8") as f:
                            f.write(new_content)
                        print(f"Updated URLs in: {filepath}")
                except Exception as e:
                    print(f"Failed to process {filepath}: {e}")

print("--- FIXING FRONTEND URLs ---")
replace_in_files(FRONTEND_DIR)
if os.path.exists(TRACER_DIR):
    replace_in_files(TRACER_DIR)

print("\n--- UPDATING BACKEND WRANGLER ---")
if os.path.exists(BACKEND_WRANGLER):
    with open(BACKEND_WRANGLER, "r", encoding="utf-8") as f:
        w_content = f.read()
    if "nemesis-loc-backend" in w_content:
        w_content = w_content.replace('name = "nemesis-loc-backend"', 'name = "nemesis-backend"')
        with open(BACKEND_WRANGLER, "w", encoding="utf-8") as f:
            f.write(w_content)
        print("Updated backend wrangler.toml name to nemesis-backend")

def run_cmd(cmd, cwd):
    print(f"\n[RUNNING] {' '.join(cmd)} in {cwd}")
    process = subprocess.Popen(
        cmd,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        shell=os.name == 'nt'
    )
    for line in process.stdout:
        print(line.strip())
    process.wait()
    if process.returncode == 0:
        print(f"[SUCCESS] Command finished successfully.")
    else:
        print(f"[ERROR] Command failed with exit code {process.returncode}")

print("\n--- DEPLOYING BACKEND ---")
# Strip conflicting API token if any, to force OAuth
env = os.environ.copy()
if "CLOUDFLARE_API_TOKEN" in env:
    del env["CLOUDFLARE_API_TOKEN"]

subprocess.run(["npx", "wrangler", "deploy"], cwd=BACKEND_DIR, env=env, shell=True)

print("\n--- DEPLOYING FRONTEND ---")
subprocess.run(["npx", "wrangler", "pages", "deploy", ".", "--project-name", "nemesis-id-frontend"], cwd=FRONTEND_DIR, env=env, shell=True)

print("\n--- DEPLOYMENT FINISHED ---")
