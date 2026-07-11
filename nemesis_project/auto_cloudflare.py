import os
import subprocess
import shutil

WORKER_DIR = "nemesis_python_worker"

print("============================================================")
print(" 🚀 AUTOMATING CLOUDFLARE PYTHON WORKER SETUP...")
print("============================================================")

# 1. Run the create-cloudflare non-interactive command
try:
    print(f"[*] Initializing {WORKER_DIR} without interactive prompts...")
    subprocess.run(
        ["npx", "--yes", "create-cloudflare@latest", WORKER_DIR, "--type", "hello-world", "--lang", "python", "--no-deploy", "--accept-defaults"],
        check=True,
        shell=True
    )
except subprocess.CalledProcessError:
    print("[!] Failed to run npx. Please ensure Node.js is installed.")
    exit(1)

# 2. Write the configured wrangler.toml
wrangler_config = """name = "nemesis-python-worker"
main = "src/index.py"
compatibility_date = "2024-12-01"
compatibility_flags = ["python_workers"]

[observability]
enabled = true

[[kv_namespaces]]
binding = "NEMESIS_KV"
id = "556aa273aeac4b009b559bb215346ce3"
preview_id = "556aa273aeac4b009b559bb215346ce3"

[[d1_databases]]
binding = "DB"
database_name = "nemesis_audit_db"
database_id = "80acedab-33c2-4637-bee7-6b9a1176a463"

[[r2_buckets]]
binding = "NEMESIS_STORAGE"
bucket_name = "nemesis-assets"

[vars]
BACKEND_API_URL = "https://nemesis-local.onrender.com"
"""

wrangler_path = os.path.join(WORKER_DIR, "wrangler.toml")
print(f"[*] Writing custom configuration to {wrangler_path}...")
with open(wrangler_path, "w", encoding="utf-8") as f:
    f.write(wrangler_config)

# 3. Write a default Python worker index.py
index_py_content = """from js import Response

async def on_fetch(request, env):
    # Example showing access to environment variables and bindings
    backend_url = env.BACKEND_API_URL
    
    return Response.new(f"Nemesis Python Worker Active! Backend set to: {backend_url}")
"""

src_dir = os.path.join(WORKER_DIR, "src")
os.makedirs(src_dir, exist_ok=True)
index_path = os.path.join(src_dir, "index.py")

print(f"[*] Writing Python worker logic to {index_path}...")
with open(index_path, "w", encoding="utf-8") as f:
    f.write(index_py_content)

print("============================================================")
print(f" ✅ SUCCESS! Cloudflare Python worker deployed in ./{WORKER_DIR}")
print(f" ➡️ To test locally: cd {WORKER_DIR} && npx wrangler dev")
print(f" ➡️ To deploy: cd {WORKER_DIR} && npx wrangler deploy")
print("============================================================")
