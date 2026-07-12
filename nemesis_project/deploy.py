import subprocess
import os

print("🚀 Attempting deployment with standard npx wrangler...")

# Remove pylock.toml if it exists to prevent conflicts
if os.path.exists("pylock.toml"):
    os.remove("pylock.toml")

# Run native wrangler deploy specifying the entry point
try:
    process = subprocess.Popen("npx wrangler deploy main.py", shell=True)
    process.communicate()
except Exception as e:
    print(f"Error running wrangler: {e}")
