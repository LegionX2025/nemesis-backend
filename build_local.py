import os
import shutil

def main():
    print("=== LIONSGATE NETWORK: LOCAL BUILD ===")
    
    local_dir = "local_deploy"
    
    if os.path.exists(local_dir):
        print(f"[PRE-FLIGHT] Cleaning up old {local_dir} folder...")
        shutil.rmtree(local_dir)
    
    os.makedirs(local_dir)
    os.makedirs(os.path.join(local_dir, "templates"))
    os.makedirs(os.path.join(local_dir, "static"))
    
    # Copy backend and root files
    shutil.copy("main.py", os.path.join(local_dir, "main.py"))
    shutil.copy("auto_backup.py", os.path.join(local_dir, "auto_backup.py"))
    shutil.copy("requirements.txt", os.path.join(local_dir, "requirements.txt"))
    if os.path.exists(".env"):
        shutil.copy(".env", os.path.join(local_dir, ".env"))
        
    # Copy directories
    for d in ["services", "intel", "darknet"]:
        if os.path.exists(d):
            shutil.copytree(d, os.path.join(local_dir, d))
            
    # Copy templates (handles files and subdirs)
    if os.path.exists("templates"):
        shutil.copytree("templates", os.path.join(local_dir, "templates"), dirs_exist_ok=True)
        
    # Copy static (handles files and subdirs like css)
    if os.path.exists("static"):
        shutil.copytree("static", os.path.join(local_dir, "static"), dirs_exist_ok=True)
        
    print(f"-> Successfully built local environment in /{local_dir}/")
    print("-> To test, run: cd local_deploy && python main.py")

if __name__ == "__main__":
    main()
