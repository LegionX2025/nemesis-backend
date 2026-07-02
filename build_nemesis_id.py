import os
import shutil

def build():
    # Nemesis ID is now a standalone template in templates/nemesis_id.html
    # We no longer generate it from index.html
    print("NEMESIS ID is now a standalone template. No build required.")
    
    # Just in case local_deploy needs it copied from root
    src = "templates/nemesis_id.html"
    dest = "local_deploy/templates/nemesis_id.html"
    if os.path.exists(src):
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        shutil.copy(src, dest)
        print(f"Copied {src} to {dest}")

if __name__ == "__main__":
    build()
