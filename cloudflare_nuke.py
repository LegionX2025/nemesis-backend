import subprocess
import sys
import time

def run_cmd(cmd):
    print(f"\n[RUNNING] {cmd}")
    try:
        # Use shell=True for npx on Windows
        process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in process.stdout:
            print(line.strip())
        process.wait()
        if process.returncode == 0:
            print("[SUCCESS]")
        else:
            print(f"[FAILED] Exit code {process.returncode} (This is normal if the resource doesn't exist).")
    except Exception as e:
        print(f"[ERROR] {e}")

def main():
    print("=====================================================================")
    print(" ⚠️  WARNING: CLOUDFLARE NUKE SCRIPT INITIATED ⚠️")
    print("=====================================================================")
    print("This script will DESTROY all Cloudflare Workers, Pages, D1 Databases,")
    print("KV Namespaces, R2 Buckets, and Queues associated with the NEMESIS project.")
    print("This action is IRREVERSIBLE.\n")
    
    confirm = input("Type 'NUKE' to proceed: ")
    if confirm != 'NUKE':
        print("Aborted.")
        sys.exit(0)
        
    print("\n>>> INITIATING DELETION SEQUENCE...\n")

    # 1. Cloudflare Pages
    pages = ["nemesis-id-frontend"]
    print("--- Deleting Cloudflare Pages ---")
    for p in pages:
        run_cmd(f"npx wrangler pages project delete {p} -y")

    # 2. Cloudflare Workers
    workers = ["nemesis-loc-backend", "nemesis-edge", "nemesis-global-worker"]
    print("\n--- Deleting Cloudflare Workers ---")
    for w in workers:
        run_cmd(f"npx wrangler delete --name {w} -y")

    # 3. D1 Databases
    databases = ["nemesis", "nemesis_audit_db", "nemesis-db"]
    print("\n--- Deleting D1 Databases ---")
    for db in databases:
        run_cmd(f"npx wrangler d1 delete {db} -y")

    # 4. KV Namespaces
    # These are the IDs extracted from your wrangler.toml files
    kv_ids = [
        "f4099ea1458e4e62ba838734f172846f", # NEMESIS_CACHE
        "817961173773498d9e4715b3479fc66d", # ENTITY_CACHE
        "7fbab659456242db8c27082fcdb0d4b1", # SESSION_CACHE
        "2c35b6ff21d14830b3ae93ee4e6006c2", # TOKEN_CACHE
        "5558ace53efa4a0aa37dc035b17c256a"  # OSINT_CACHE
    ]
    print("\n--- Deleting KV Namespaces ---")
    for kv in kv_ids:
        run_cmd(f"npx wrangler kv:namespace delete --namespace-id {kv}")

    # 5. R2 Buckets
    buckets = ["nemesis-reports", "nemesis-evidence", "nemesis-screenshots", "nemesis-exports"]
    print("\n--- Deleting R2 Buckets ---")
    for bucket in buckets:
        run_cmd(f"npx wrangler r2 bucket delete {bucket} -y")

    # 6. Queues
    queues = ["wallet-tracing", "entity-resolution", "gemini-analysis", "report-generation", "notifications"]
    print("\n--- Deleting Queues ---")
    for q in queues:
        run_cmd(f"npx wrangler queues delete {q} -y")

    print("\n=====================================================================")
    print(" ✅ DELETION SEQUENCE COMPLETE")
    print("=====================================================================")
    print("Check your Cloudflare Dashboard to ensure no ghost resources remain.")
    print("You are now ready for a fresh deployment.")

if __name__ == "__main__":
    main()
