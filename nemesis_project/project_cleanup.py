import os
import shutil

# Target directories
ROOT_DIR = "."
REPORTS_DIR = "reports"
SETUP_SCRIPTS_DIR = os.path.join("scripts", "setup")
DEBUG_SCRIPTS_DIR = os.path.join("scripts", "debug")

def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

# Directories to delete
dirs_to_delete = [
    ".venv-workers",
    ".venv2",
    "temp_fastapi",
    "scratch"
]

# Files to delete
files_to_delete = [
    "No"
]

# Files to move to reports/
reports_to_move = [
    "LFR_7c19ccf6.csv",
    "LFR_7c19ccf6.json",
    "LFR_88d3fd12.csv",
    "LFR_88d3fd12.json",
    "LFR_zeroShadow_01.csv",
    "LFR_zeroShadow_01.json",
    "LGN_Forensic_Report.html"
]

# Files to move to scripts/setup/
setup_scripts = [
    "auto_cloudflare.py",
    "auto_deploy.py",
    "build_v32.py",
    "compile_html.py",
    "deploy.bat",
    "deploy.py",
    "fix_deps.py",
    "fix_git.py",
    "fix_main.py",
    "fix_wrangler_ids.py",
    "setup_bitquery.py",
    "setup_bitquery_v2.py",
    "setup_cloudflare_all.py"
]

# Files to move to scripts/debug/
debug_scripts = [
    "debug_oklink.py",
    "search_exact.py",
    "test_trace.py",
    "godmode.py",
    "push_req.py"
]

def cleanup():
    print("🧹 Starting NEMESIS Project Cleanup...")
    
    # Create target directories
    ensure_dir(REPORTS_DIR)
    ensure_dir(SETUP_SCRIPTS_DIR)
    ensure_dir(DEBUG_SCRIPTS_DIR)
    print("📁 Created target directories.")

    # 1. Move Reports
    for file in reports_to_move:
        if os.path.exists(file):
            shutil.move(file, os.path.join(REPORTS_DIR, file))
            print(f"  [+] Moved {file} -> {REPORTS_DIR}/")

    # 2. Move Setup Scripts
    for file in setup_scripts:
        if os.path.exists(file):
            shutil.move(file, os.path.join(SETUP_SCRIPTS_DIR, file))
            print(f"  [+] Moved {file} -> {SETUP_SCRIPTS_DIR}/")

    # 3. Move Debug Scripts
    for file in debug_scripts:
        if os.path.exists(file):
            shutil.move(file, os.path.join(DEBUG_SCRIPTS_DIR, file))
            print(f"  [+] Moved {file} -> {DEBUG_SCRIPTS_DIR}/")

    # 4. Delete Unused Directories
    for d in dirs_to_delete:
        if os.path.exists(d):
            try:
                shutil.rmtree(d)
                print(f"  [-] Deleted directory: {d}")
            except Exception as e:
                print(f"  [!] Failed to delete {d}: {e}")

    # 5. Delete Unused Files
    for f in files_to_delete:
        if os.path.exists(f):
            try:
                os.remove(f)
                print(f"  [-] Deleted file: {f}")
            except Exception as e:
                print(f"  [!] Failed to delete {f}: {e}")
                
    print("✅ Project Cleanup Complete!")

if __name__ == "__main__":
    cleanup()
