import os
import shutil

def organize_project():
    source_dir = r"c:\Users\LEGIONX\Downloads\cases"
    dest_dir = os.path.join(source_dir, "nemesis_project")

    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)

    # Directories/files to exclude from moving
    exclude_list = {
        "nemesis_project",
        "local_deploy",
        "cloudflare_frontend",
        "cloudflare_worker",
        "render_backend",
        ".git",
        ".agents",
        ".cursor",
        ".vscode",
        ".windsurf",
        "venv",
        "backups",
        ".env",
        "nemesis_documents",
        "nemesis_vault",
        ".wrangler",
        "__pycache__",
        ".gitignore",
        "organize_project.py"
    }

    # Move files and folders
    moved_items = []
    for item in os.listdir(source_dir):
        if item in exclude_list:
            continue
            
        source_item = os.path.join(source_dir, item)
        dest_item = os.path.join(dest_dir, item)
        
        try:
            shutil.move(source_item, dest_item)
            moved_items.append(item)
        except Exception as e:
            print(f"Failed to move {item}: {e}")
            
    print(f"Successfully moved {len(moved_items)} items into 'nemesis_project'.")
    print("Moved items:", moved_items)

if __name__ == "__main__":
    organize_project()
