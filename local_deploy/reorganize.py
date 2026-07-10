import os
import shutil

root_dir = r"C:\Users\LEGIONX\Downloads\cases\local_deploy"

# Phase 1: Create Directories
dirs_to_create = [
    "frontend",
    "backend/app/modules",
    "backend/app/services",
    "backend/scripts",
    "backend/tests",
    "ops/database"
]

for d in dirs_to_create:
    path = os.path.join(root_dir, d)
    os.makedirs(path, exist_ok=True)
    print(f"Created: {path}")

def move_item(src, dst):
    src_path = os.path.join(root_dir, src)
    dst_path = os.path.join(root_dir, dst)
    if os.path.exists(src_path):
        try:
            # If destination already exists and is a directory, move into it
            if os.path.exists(dst_path) and os.path.isdir(dst_path):
                # Ensure we don't move a dir into itself
                if os.path.basename(src_path) == os.path.basename(dst_path):
                     print(f"Skipping {src_path} -> {dst_path} to avoid nesting.")
                     return
            shutil.move(src_path, dst_path)
            print(f"Moved: {src} -> {dst}")
        except Exception as e:
            print(f"Error moving {src} to {dst}: {e}")
    else:
        print(f"Skip (Not found): {src}")

# Phase 2: Move Frontend Files
move_item("templates", "frontend/")
move_item("static", "frontend/")
move_item("assets", "frontend/")
move_item("nemesis-global-worker", "frontend/")
move_item("nemesis_final_audit.html", "frontend/")

# Phase 3: Move Backend Files
move_item("main.py", "backend/app/")
move_item("services", "backend/app/")
move_item("osint", "backend/app/modules/")
move_item("darknet", "backend/app/modules/")
move_item("intel", "backend/app/modules/")
move_item("nemesis", "backend/app/modules/")
move_item("worker_consumer", "backend/app/modules/")
move_item("nemesis_vault", "backend/app/modules/")
move_item("oklink_scraper.py", "backend/app/services/")
move_item("scripts", "backend/")
move_item("tests", "backend/")
move_item("requirements.txt", "backend/")
move_item("render.yaml", "backend/")

# Phase 4: Move Ops/Deployment Files
move_item("auto_deploy.py", "ops/")
move_item("auto_backup.py", "ops/")
move_item("import_mongo.py", "ops/database/")
move_item("import_knowledge_base.py", "ops/database/")
move_item("migrate_mongo.py", "ops/database/")
move_item("boot.py", "ops/")
move_item("run_batch_tests.py", "ops/")
move_item("copy_icons.py", "ops/")

print("\nReorganization complete.")
