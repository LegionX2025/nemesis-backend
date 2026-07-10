import os
import shutil
import datetime

def backup_project():
    source_dir = r"C:\Users\LEGIONX\downloads\cases"
    backup_dir = os.path.join(source_dir, "backups")
    
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
        
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_name = os.path.join(backup_dir, f"nemesis_backup_{timestamp}")
    
    def ignore_patterns(path, names):
        return [n for n in names if n in ('__pycache__', 'node_modules', '.git', 'backups', 'venv', '.env')]
    
    # Create a temporary directory to copy files to
    temp_dir = os.path.join(source_dir, f"temp_backup_{timestamp}")
    shutil.copytree(source_dir, temp_dir, ignore=ignore_patterns)
    
    # Create the archive from the temp directory
    shutil.make_archive(archive_name, 'zip', temp_dir)
    
    # Clean up the temp directory
    shutil.rmtree(temp_dir)
    print(f"Backup created successfully at: {archive_name}.zip")

if __name__ == "__main__":
    backup_project()
