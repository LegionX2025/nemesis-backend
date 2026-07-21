import subprocess
import os

cwd = r"c:\Users\LEGIONX\Downloads\cases\local_deploy\backend"
env = os.environ.copy()
if "CLOUDFLARE_API_TOKEN" in env:
    del env["CLOUDFLARE_API_TOKEN"]

print("--- WRANGLER DEPLOY BACKEND ---")
process = subprocess.Popen(
    "npx wrangler deploy",
    cwd=cwd,
    env=env,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    shell=True
)
for line in process.stdout:
    print(line, end="")
process.wait()
print(f"\nExit code: {process.returncode}")
