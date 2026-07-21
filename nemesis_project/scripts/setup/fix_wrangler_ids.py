import os
import re
import json
import subprocess

def run_cmd(cmd):
    try:
        # Use shell=True to support npx on Windows
        return subprocess.check_output(cmd, shell=True, text=True, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        print(f"Error running '{cmd}': {e.output}")
        return None

def main():
    print("🔍 Fetching Cloudflare D1 Databases...")
    d1_out = run_cmd("npx wrangler d1 list --json")
    d1_id = None
    if d1_out:
        try:
            # Sometime wrangler prints non-json warnings before the JSON array.
            json_str = d1_out[d1_out.find('['):d1_out.rfind(']')+1]
            d1_list = json.loads(json_str)
            for db in d1_list:
                if db.get('name') == 'nemesis_audit_db':
                    d1_id = db.get('uuid')
                    print(f"✅ Found D1 'nemesis_audit_db' ID: {d1_id}")
                    break
        except Exception as e:
            print("Could not parse D1 JSON output.", e)
            print("Raw:", d1_out)

    print("🔍 Fetching Cloudflare KV Namespaces...")
    kv_out = run_cmd("npx wrangler kv namespace list")
    kv_id = None
    if kv_out:
        try:
            json_str = kv_out[kv_out.find('['):kv_out.rfind(']')+1]
            kv_list = json.loads(json_str)
            for kv in kv_list:
                if kv.get('title') == 'nemesis-edge-proxy-NEMESIS_KV' or 'NEMESIS_KV' in kv.get('title', ''):
                    kv_id = kv.get('id')
                    print(f"✅ Found KV 'NEMESIS_KV' ID: {kv_id}")
                    break
        except Exception as e:
            print("Could not parse KV JSON output.", e)
            print("Raw:", kv_out)

    if not d1_id or not kv_id:
        print("❌ Could not find both IDs. Make sure 'auto_deploy.py' successfully created them.")
        return

    print("📝 Updating wrangler.toml...")
    with open("wrangler.toml", "r") as f:
        toml = f.read()

    # Replace waiting tags
    toml = re.sub(r'id\s*=\s*"WAITING_FOR_DEPLOYMENT"\s*# KV', f'id = "{kv_id}"', toml)
    toml = re.sub(r'id\s*=\s*"WAITING_FOR_DEPLOYMENT"', f'id = "{kv_id}"', toml)
    toml = re.sub(r'preview_id\s*=\s*"WAITING_FOR_DEPLOYMENT"', f'preview_id = "{kv_id}"', toml)
    toml = re.sub(r'database_id\s*=\s*"WAITING_FOR_DEPLOYMENT"', f'database_id = "{d1_id}"', toml)

    with open("wrangler.toml", "w") as f:
        f.write(toml)
    
    print("🚀 wrangler.toml updated successfully! You can now run 'python auto_deploy.py' again.")

if __name__ == "__main__":
    main()
