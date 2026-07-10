import shutil
import os
import datetime

def zip_project():
    source_dir = os.path.dirname(os.path.abspath(__file__))
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = os.path.join(source_dir, "backups")
    os.makedirs(backup_dir, exist_ok=True)
    
    zip_name = os.path.join(backup_dir, f"nemesis_backup_{timestamp}")
    
    def ignore_patterns(dirname, contents):
        return [c for c in contents if c in ['venv', '.venv', '__pycache__', 'node_modules', '.git', 'backups', '.gemini', 'render_backend', 'cloudflare_frontend']]
    
    # Create a temporary directory without ignored files
    temp_dir = os.path.join(source_dir, "temp_backup_staging")
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
        
    try:
        shutil.copytree(source_dir, temp_dir, ignore=ignore_patterns)
        print(f"Zipping contents to {zip_name}.zip...")
        shutil.make_archive(zip_name, 'zip', temp_dir)
        print(f"Successfully created backup {zip_name}.zip")
    except Exception as e:
        print(f"Error creating zip file: {e}")
    finally:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

if __name__ == "__main__":
    zip_project()
