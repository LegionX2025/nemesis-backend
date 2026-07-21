import os
import shutil

def revert_and_organize():
    base_dir = r"c:\Users\LEGIONX\Downloads\cases"
    nemesis_dir = os.path.join(base_dir, "nemesis_project")

    # 1. Revert: Move everything from nemesis_project back to cases
    if os.path.exists(nemesis_dir):
        print("Reverting files from nemesis_project back to root...")
        for item in os.listdir(nemesis_dir):
            if item == "cleanup_project.py": # don't need this anymore
                continue
            src = os.path.join(nemesis_dir, item)
            dst = os.path.join(base_dir, item)
            try:
                # If dst already exists, it might be due to a partial move. We'll try to move anyway or skip.
                if not os.path.exists(dst):
                    shutil.move(src, dst)
            except Exception as e:
                print(f"Error reverting {item}: {e}")

    # 2. Re-create clean nemesis_project folder
    if not os.path.exists(nemesis_dir):
        os.makedirs(nemesis_dir)

    # 3. Core Files List
    core_items = [
        "adapters",
        "services",
        "scraper_service",
        "darknet",
        "intel",
        "graph",
        "templates",
        "static",
        "data",
        "scripts",
        "main.py",
        "requirements.txt",
        "Dockerfile",
        "render.yaml",
        "wrangler.jsonc",
        "auto_deploy.py"
    ]

    print("\nMoving ONLY Core Project Files to nemesis_project...")
    moved_count = 0
    for item in core_items:
        src = os.path.join(base_dir, item)
        dst = os.path.join(nemesis_dir, item)
        if os.path.exists(src):
            try:
                shutil.move(src, dst)
                print(f"[MOVED] {item}")
                moved_count += 1
            except Exception as e:
                print(f"[ERROR] Could not move {item}: {e}")

    # Also move the logo directly into static if it's sitting in base_dir
    logo_src = os.path.join(base_dir, "logo_nemesis.jpeg")
    logo_dst = os.path.join(nemesis_dir, "static", "logo_nemesis.jpeg")
    if os.path.exists(logo_src):
        if not os.path.exists(os.path.dirname(logo_dst)):
            os.makedirs(os.path.dirname(logo_dst))
        shutil.move(logo_src, logo_dst)
        print("[MOVED] logo_nemesis.jpeg -> static/")

    print(f"\nDone! Only {moved_count} core components are now in nemesis_project.")
    print("All backups, tests, old scripts (app.py, index.py), and local scripts remain in the root 'cases' directory.")

if __name__ == "__main__":
    revert_and_organize()
