import os
import shutil

base_dir = r"C:\Users\LEGIONX\Downloads\cases\local_deploy"
archive_dir = os.path.join(base_dir, "_archive_temp")

if not os.path.exists(archive_dir):
    os.makedirs(archive_dir)

folders_to_move = [
    ".venv",
    ".venv-workers",
    "nemesis_full",
    "tracer_scripts",
    "nemesis_documents",
    "NEMESIS_KNOWLEDGE_BASE_LIBRARY",
    "python_modules",
    "ops"
]

files_to_move = [
    "auto_deploy.py",
    "cleanup_project.py",
    "copy_dashboard.py",
    "deploy_all.bat",
    "deploy_all.py",
    "deploy_edge_api.py",
    "deploy_fixed.bat",
    "fix_and_deploy.py",
    "run_all.bat",
    "start_local_test.py",
    "sync_secrets.py",
    "test_all.ps1",
    "test_deploy.py",
    "test_targets.py",
    "DEPLOY_CLOUDFLARE_NATIVE.bat",
    "RUN_ME.bat",
    "do_cleanup.py"
]

print(f"Archiving to {archive_dir}...")

for item in folders_to_move:
    src = os.path.join(base_dir, item)
    dst = os.path.join(archive_dir, item)
    if os.path.exists(src):
        try:
            shutil.move(src, dst)
            print(f"[OK] Moved folder: {item}")
        except Exception as e:
            print(f"[FAIL] Failed to move folder {item}: {e}")

for item in files_to_move:
    src = os.path.join(base_dir, item)
    dst = os.path.join(archive_dir, item)
    if os.path.exists(src):
        try:
            shutil.move(src, dst)
            print(f"[OK] Moved file: {item}")
        except Exception as e:
            print(f"[FAIL] Failed to move file {item}: {e}")

print("Cleanup complete!")
