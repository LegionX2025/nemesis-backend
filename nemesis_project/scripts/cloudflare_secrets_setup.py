import os
import subprocess
import time

def setup_cloudflare_secrets():
    print("==================================================")
    print(" 🔐 NEMESIS CLOUDFLARE SECRETS DEPLOYMENT MODULE 🔐")
    print("==================================================")
    
    if not os.path.exists(".env"):
        print("❌ Error: .env file not found!")
        return

    # List of highly sensitive enterprise keys to inject into Cloudflare Workers
    # We DO NOT put these in wrangler.toml to prevent exposure in git.
    sensitive_keys = [
        "GEMINI_API_KEYS",
        "ANKR_API_KEY",
        "TATUM_API_KEY",
        "INFURA_API_KEY",
        "ETHERSCAN_API_KEY",
        "BSCSCAN_API_KEY",
        "POLYGONSCAN_API_KEY",
        "SNOWTRACE_API_KEY",
        "ARBISCAN_API_KEY",
        "OPTIMISMSCAN_API_KEY",
        "BASESCAN_API_KEY",
        "CELOSCAN_API_KEY",
        "LINEASCAN_API_KEY",
        "GETBLOCK_BTC_KEY",
        "GETBLOCK_ETH_KEY",
        "GETBLOCK_SOL_KEY",
        "GETBLOCK_TRON_KEY",
        "GETBLOCK_XRP_KEY",
        "CENSYS_API_KEY",
        "SHODAN_API_KEY",
        "HUNTER_API_KEY"
    ]

    print(f"📦 Found {len(sensitive_keys)} critical API keys to synchronize with Cloudflare edge.")
    
    with open(".env", "r", encoding="utf-8") as f:
        env_lines = f.readlines()

    env_vars = {}
    for line in env_lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key, val = line.split("=", 1)
            env_vars[key.strip()] = val.strip()

    # Step 1: Create .dev.vars for local pywrangler simulation
    print("\n📝 Generating .dev.vars for local secure Pywrangler testing...")
    with open(".dev.vars", "w", encoding="utf-8") as f:
        for k, v in env_vars.items():
            if k in sensitive_keys or "API_KEY" in k or "SECRET" in k or "TOKEN" in k:
                f.write(f"{k}={v}\n")
    print("✅ .dev.vars created successfully.")

    # Step 2: Push to Production Cloudflare Secrets (Optional)
    print("\n🚀 Preparing to push secrets to Cloudflare Production...")
    push = input("Do you want to run 'wrangler secret put' for all sensitive keys now? (y/n): ")
    
    if push.lower() == 'y':
        for key in sensitive_keys:
            val = env_vars.get(key)
            if val:
                print(f"Pushing {key} to Cloudflare...")
                # Note: Windows uses shell=True
                try:
                    process = subprocess.Popen(
                        f"npx wrangler secret put {key}", 
                        shell=True, 
                        stdin=subprocess.PIPE, 
                        stdout=subprocess.PIPE, 
                        stderr=subprocess.PIPE, 
                        text=True
                    )
                    out, err = process.communicate(input=f"{val}\n")
                    if process.returncode == 0:
                        print(f"  ✅ Success: {key}")
                    else:
                        print(f"  ❌ Failed: {key} - {err.strip()}")
                except Exception as e:
                    print(f"  ❌ Crash: {e}")
                time.sleep(1) # Prevent rate limiting
        print("\n🎉 Cloudflare Secrets Synchronization Complete!")
    else:
        print("\n⏭️ Skipped production push. You can deploy locally using 'uv run pywrangler dev'.")

if __name__ == "__main__":
    setup_cloudflare_secrets()
