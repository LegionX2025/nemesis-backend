import os
import json
import subprocess
import shutil

# Fix rogue wrangler files causing conflict
rogue1 = r"c:\Users\LEGIONX\Downloads\cases\local_deploy\wrangler.json"
rogue2 = r"c:\Users\LEGIONX\Downloads\cases\wrangler.jsonc"

if os.path.exists(rogue1):
    shutil.move(rogue1, rogue1 + ".disabled")
if os.path.exists(rogue2):
    shutil.move(rogue2, rogue2 + ".disabled")

env_file = r"c:\Users\LEGIONX\Downloads\cases\local_deploy\.env"
worker_dir = r"c:\Users\LEGIONX\Downloads\cases\local_deploy\frontend\nemesis-global-worker"

def read_env(filepath):
    vars_dict = {}
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'): continue
            if '=' in line:
                key, val = line.split('=', 1)
                val = val.strip().strip('"').strip("'")
                val = val.split(' #')[0].strip()
                if key not in ["PYTHON_BACKEND_URL", "NODE_ENV", "APP_NAME", "APP_MODE"]:
                    vars_dict[key] = val
    return vars_dict

print("🔐 Generating secure Cloudflare secrets payload in batches...")
secrets = read_env(env_file)
items = list(secrets.items())

chunk_size = 90
batches = [items[i:i + chunk_size] for i in range(0, len(items), chunk_size)]

success = True

for idx, batch in enumerate(batches):
    batch_dict = dict(batch)
    chunk_file = os.path.join(worker_dir, f"secrets_batch_{idx}.json")
    with open(chunk_file, 'w', encoding='utf-8') as f:
        json.dump(batch_dict, f)
    
    print(f"🚀 Uploading batch {idx+1}/{len(batches)} ({len(batch_dict)} secrets) to Cloudflare...")
    
    # Force wrangler to use the correct config file using -c
    result = subprocess.run(
        f"cd {worker_dir} && npx wrangler secret bulk secrets_batch_{idx}.json -c wrangler.toml", 
        shell=True
    )
    
    if result.returncode != 0:
        print(f"❌ Failed to upload batch {idx+1}")
        success = False
    
    # Cleanup chunk file
    if os.path.exists(chunk_file):
        os.remove(chunk_file)

if success:
    print("✅ All secrets securely uploaded to Cloudflare Worker 'nemesis-api'!")
else:
    print("❌ Some secrets failed to upload.")
