import os
import shutil
import subprocess

print("========================================================")
print("NEMESIS EDGE DEPLOYMENT PIPELINE (PYTHON FALLBACK)")
print("========================================================")

src = r"C:\Users\LEGIONX\Downloads\nemesis\tracer_scripts"
dst = r"c:\Users\LEGIONX\Downloads\cases\local_deploy\tracer_scripts"

print("\n[1] Copying tracer_scripts from Nemesis to local_deploy...")
if os.path.exists(dst):
    print("Destination already exists. Removing old folder...")
    shutil.rmtree(dst, ignore_errors=True)

try:
    shutil.copytree(src, dst)
    print("SUCCESS: tracer_scripts copied.")
except Exception as e:
    print(f"ERROR copying folder: {e}")

print("\n[2] Running Auto Deployer...")
deployer_path = r"c:\Users\LEGIONX\Downloads\cases\local_deploy\auto_deploy.py"
try:
    subprocess.run(["python", deployer_path], cwd=r"c:\Users\LEGIONX\Downloads\cases\local_deploy")
except Exception as e:
    print(f"ERROR running deployer: {e}")

print("\n========================================================")
print("Deployment process finished. Please review the output above.")
print("========================================================")
