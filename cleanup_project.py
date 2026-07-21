import os
import shutil

def cleanup_project():
    project_dir = r"c:\Users\LEGIONX\Downloads\cases\nemesis_project"

    files_to_remove = [
        "app.py", "case.py", "index.py", "index - Copy.py",
        "test.py", "test_btc.py", "test_evm_apis.py", "test_evm_apis2.py",
        "search.py", "ml_clustering.py", "ontology_seeder.py",
        "LFR_b04e61a6.csv", "LFR_b04e61a6.json", "entities_export.csv",
        "Nemesis_OmniChain_Backup_20260701_114933.zip", "backups.zip", "productions.zip",
        "build.bat", "build_local.py", "build_nemesis_id.py", "build_v32.ps1",
        "start_darknet_ui.bat", "start_productions.bat",
        "auto_backup.py", "backup_project.py", "zipper.py",
        "patch_urls.py", "refactor.py", "extract_html.py", "sync_frontends.py", 
        "deploy_all.py", "create_architecture.py", "setup_cloudflare_mcp.py"
    ]

    print("Starting cleanup of non-core files...")
    
    # 1. Delete junk files
    deleted_count = 0
    for filename in files_to_remove:
        file_path = os.path.join(project_dir, filename)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"[DELETED] {filename}")
                deleted_count += 1
            except Exception as e:
                print(f"[ERROR] Failed to delete {filename}: {e}")
                
    # 2. Move logo to static if it's in the root
    logo_path = os.path.join(project_dir, "logo_nemesis.jpeg")
    static_dir = os.path.join(project_dir, "static")
    if os.path.exists(logo_path):
        if not os.path.exists(static_dir):
            os.makedirs(static_dir)
        try:
            shutil.move(logo_path, os.path.join(static_dir, "logo_nemesis.jpeg"))
            print("[MOVED] logo_nemesis.jpeg -> static/logo_nemesis.jpeg")
        except Exception as e:
            print(f"[ERROR] Failed to move logo: {e}")

    print(f"\nCleanup complete! Deleted {deleted_count} files.")

if __name__ == "__main__":
    cleanup_project()
