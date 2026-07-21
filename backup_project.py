import os
import zipfile
import datetime

def backup_project():
    source_dir = os.path.dirname(os.path.abspath(__file__))
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_name = f"Nemesis_OmniChain_Backup_{timestamp}.zip"
    
    # Directories and files to explicitly exclude from the backup to save space
    exclude_dirs = {'venv', 'node_modules', '__pycache__', '.git', '.agents', '.cursor', '.vscode', '.windsurf'}
    exclude_exts = {'.zip', '.log', '.pyc'}
    
    print(f"Creating backup: {zip_name}...")
    
    with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(source_dir):
            # Modify dirs in-place to prevent os.walk from traversing excluded directories
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            
            for file in files:
                if any(file.endswith(ext) for ext in exclude_exts):
                    continue
                if file == zip_name:
                    continue
                
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, source_dir)
                try:
                    zipf.write(file_path, arcname)
                except Exception as e:
                    print(f"Skipping {file}: {e}")
                    
    print(f"Backup successfully created at: {os.path.join(source_dir, zip_name)}")

if __name__ == "__main__":
    backup_project()
