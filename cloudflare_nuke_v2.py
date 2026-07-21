import subprocess
import sys

def run_interactive_cmd(cmd):
    print(f"\n[RUNNING] {cmd}")
    try:
        # We use subprocess.run with input="y\n" to automatically bypass the "Are you sure?" prompts
        result = subprocess.run(cmd, shell=True, input="y\ny\ny\n", text=True, capture_output=True)
        print(result.stdout)
        if result.returncode == 0:
            print(f"[SUCCESS] Command completed.")
        else:
            print(f"[FAILED] Exit code {result.returncode}. Output:\n{result.stderr}")
    except Exception as e:
        print(f"[ERROR] {e}")

def main():
    print("=====================================================================")
    print(" ⚠️ CLOUDFLARE FULL DASHBOARD NUKE INITIATED ⚠️")
    print("=====================================================================")
    print("Deleting all identified ghost projects from your Cloudflare account.\n")

    # Cloudflare Pages Projects from Dashboard
    pages = [
        "nemesis",
        "nemesis-final",
        "nemesis-tracer",
        "nemesis-ui",
        "nemesis-frontend",
        "nemesis-id-frontend"
    ]
    
    print("--- DELETING CLOUDFLARE PAGES ---")
    for p in pages:
        run_interactive_cmd(f"npx wrangler pages project delete {p}")

    # Cloudflare Workers from Dashboard
    workers = [
        "nemesisopenapi",
        "nemesisai",
        "nemesisapibackend",
        "nemesis-edge-proxy"
    ]
    
    print("\n--- DELETING CLOUDFLARE WORKERS ---")
    for w in workers:
        run_interactive_cmd(f"npx wrangler delete --name {w}")

    print("\n=====================================================================")
    print(" ✅ DELETION SEQUENCE COMPLETE")
    print("=====================================================================")
    print("Please refresh your Cloudflare Dashboard. If any projects remain, they")
    print("might be bound to a GitHub integration that requires manual deletion")
    print("from the Cloudflare web interface under Project -> Settings -> Delete.")

if __name__ == "__main__":
    main()
