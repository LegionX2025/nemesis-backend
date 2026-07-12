import os
import subprocess

# Expanded list of sensitive keys covering all Data Providers, APIs, and Infrastructure
CLASSIFIED_KEYS = [
    # Core DBs & Auth
    "FLASK_SECRET_KEY", "ADMIN_USERNAME", "ADMIN_PASSWORD", "GENEZIO_LOGIN_TOKEN",
    "DATABASE_MONGO_URL", "POSTGRES_URI", 
    "NEO4J_URI", "NEO4J_USERNAME", "NEO4J_PASSWORD", "NEO4J_DATABASE", "AURA_INSTANCEID", "AURA_INSTANCENAME",
    
    # Kafka Streams
    "KAFKA_BOOTSTRAP_SERVERS", "KAFKA_CLIENT_ID", "KAFKA_PRODUCER_RETRIES", "KAFKA_CONSUMER_GROUP",
    
    # Cloudflare Admin
    "CLOUDFLARE_ACCOUNT_ID", "CLOUDFLARE_API_TOKEN",
    
    # AI Models
    "GEMINI_API_KEY", "GEMINI_API_KEYS",
    "AIML_API_KEY_LLAMA", "AIML_API_KEY_DEEPSEEK", "AIML_API_KEY_CHATGPT", "AIML_API_KEY_BAGOODEX",
    
    # OSINT & Recon
    "CENSYS_API_KEY", "SHODAN_API_KEY", "HUNTER_API_KEY",
    
    # On-Chain Analytics & Scanners
    "BITQUERY_API_TOKEN", "BITQUERY_APIV2_TOKEN",
    "ETHERSCAN_API_KEY", "BSCSCAN_API_KEY", "POLYGONSCAN_API_KEY", "SNOWTRACE_API_KEY", 
    "ARBISCAN_API_KEY", "OPTIMISMSCAN_API_KEY", "BASESCAN_API_KEY", "CELOSCAN_API_KEY", 
    "LINEASCAN_API_KEY", "TRONSCAN_API_KEY", "ETHPLORER_API_KEY", "OKLINK_API_KEY",
    
    # RPC Gateways
    "INFURA_API_KEY", "ANKR_API_KEY", "TATUM_API_KEY",
    "GETBLOCK_BTC_KEY", "GETBLOCK_ETH_KEY", "GETBLOCK_SOL_KEY", "GETBLOCK_TRON_KEY", "GETBLOCK_XRP_KEY",
    "VALIDATION_BTC", "VALIDATION_ETH", "VALIDATION_SOL",
    
    # Exchanges
    "BINANCE_API_KEY", "BINANCE_API_SECRET",
    
    # Communications & Billing
    "SMTP_SERVER", "SMTP_PORT", "SMTP_USER", "SMTP_PASS", "REPORT_EMAIL",
    "TELEGRAM_BOT_TOKEN", "WHATSAPP_API_KEY", "STRIPE_SECRET_KEY"
]

def upload_secrets():
    print("🛡️ INITIATING SECURE UPLOAD TO CLOUDFLARE VAULT (EXTENDED MATRIX)...")
    
    env_path = os.path.join("frontend", ".env")
    if not os.path.exists(env_path):
        print(f"[!] Error: {env_path} file not found.")
        return

    with open(env_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Track what we uploaded so we can report missing ones
    uploaded_keys = set()

    for line in lines:
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
            
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        
        # Strip quotes if they exist (e.g. GEMINI_API_KEYS="...")
        if value.startswith('"') and value.endswith('"'):
            value = value[1:-1]
        elif value.startswith("'") and value.endswith("'"):
            value = value[1:-1]
        
        if key in CLASSIFIED_KEYS:
            print(f"[*] Encrypting and uploading: {key}...")
            try:
                process = subprocess.Popen(
                    ["npx", "wrangler", "secret", "put", key, "--name", "nemesis-python-worker"],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    cwd="./nemesis_python_worker" 
                )
                stdout, stderr = process.communicate(input=value)
                if process.returncode == 0:
                    print(f"    [+] Success: {key} secured.")
                    uploaded_keys.add(key)
                else:
                    print(f"    [!] Failed to upload {key}. Error: {stderr.strip()}")
            except Exception as e:
                print(f"    [!] Execution error on {key}: {e}")

    # Final Audit
    missing = set(CLASSIFIED_KEYS) - uploaded_keys
    if missing:
        print(f"\n[!] AUDIT WARNING: The following expected classified keys were missing from .env or failed to upload:")
        for m in missing:
            print(f"  - {m}")

if __name__ == "__main__":
    upload_secrets()
    print("✅ CLOUDFLARE SECRETS SYNCHRONIZATION COMPLETE.")
