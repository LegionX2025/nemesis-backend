import os
import shutil
import glob

# Ensure we are in the local_deploy directory
TARGET_DIR = r"C:\Users\LEGIONX\Downloads\cases\local_deploy"

if not os.path.exists(TARGET_DIR):
    print(f"Error: Target directory not found: {TARGET_DIR}")
    exit(1)

os.chdir(TARGET_DIR)
print(f"--- INITIATING NEMESIS PROJECT CLEANUP ---")
print(f"Target Directory: {TARGET_DIR}\n")

DIRS_TO_DELETE = [
    "venv", ".venv", ".venv-workers", "python_modules",
    "__pycache__", ".pytest_cache", ".wrangler", "logs", 
    "scratch", "tracer_scripts", "data", "backups"
]

FILES_TO_DELETE = [
    "intelligence_lake.db", "Lionsgate_Forensic_Report.html",
    "custom_trace_report.csv", "custom_trace_report.json",
    "entities_export.csv", "export.jsonl", "state.json",
    "clean_mock.py", "cleanup_templates.py", "fix_moves.py", 
    "fix_root.py", "fix_tracer_js.py", "gen_enum.py", 
    "move_dirs.py", "reorganize.py", "theme_light.py", 
    "upload_cloudflare_secrets.py", "main.py", "cloudflared.exe", 
    "wrangler.json.disabled", "logo.jpeg"
]

deleted_dirs = 0
deleted_files = 0

# 1. Delete Directories
for d in DIRS_TO_DELETE:
    if os.path.isdir(d):
        try:
            shutil.rmtree(d)
            print(f"[DELETED DIR] {d}")
            deleted_dirs += 1
        except Exception as e:
            print(f"[ERROR] Failed to delete directory {d}: {e}")

# 2. Delete Specific Files
for f in FILES_TO_DELETE:
    if os.path.isfile(f):
        try:
            os.remove(f)
            print(f"[DELETED FILE] {f}")
            deleted_files += 1
        except Exception as e:
            print(f"[ERROR] Failed to delete file {f}: {e}")

# 3. Delete Loose test scripts (test_*.py) in the root
test_scripts = glob.glob("test_*.py")
for ts in test_scripts:
    try:
        os.remove(ts)
        print(f"[DELETED TEST SCRIPT] {ts}")
        deleted_files += 1
    except Exception as e:
        print(f"[ERROR] Failed to delete {ts}: {e}")

print("\n=======================================================")
print(f" Cleanup Complete! Removed {deleted_dirs} directories and {deleted_files} files.")
print("=======================================================")
