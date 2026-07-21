import os
import subprocess

def main():
    env_file = ".env"
    if not os.path.exists(env_file):
        print(f"Error: {env_file} not found.")
        return

    # Keys that the edge worker needs
    required_keys = [
        "ETHERSCAN_API_KEY",
        "BSCSCAN_API_KEY",
        "POLYGONSCAN_API_KEY",
        "SNOWTRACE_API_KEY",
        "ARBISCAN_API_KEY",
        "OPTIMISMSCAN_API_KEY",
        "BASESCAN_API_KEY",
        "CELOSCAN_API_KEY",
        "LINEASCAN_API_KEY",
        "BITQUERY_API_KEY",
        "GEMINI_API_KEY",
        "OPENAI_API_KEY",
        "TATUM_API_KEY",
        "ANKR_API_KEY"
    ]

    secrets_to_put = {}

    with open(env_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, val = line.split("=", 1)
                key = key.strip()
                val = val.strip()
                if key in required_keys:
                    secrets_to_put[key] = val

    worker_dir = os.getcwd()

    for key, val in secrets_to_put.items():
        print(f"Pushing secret {key} to nemesis-api-v3 worker...")
        # Using echo to pipe the value into wrangler secret put
        cmd = f"echo {val} | npx wrangler secret put {key} --name nemesis-api-v3"
        try:
            subprocess.run(cmd, shell=True, cwd=worker_dir, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Failed to push {key}: {e}")

    print("All secrets synced successfully.")

if __name__ == "__main__":
    main()
