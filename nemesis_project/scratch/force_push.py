import os
import subprocess
import sys

def main():
    print("Trying to find git repo and push main.py...")
    
    # Check if git is installed
    try:
        subprocess.run(["git", "--version"], check=True, stdout=subprocess.PIPE)
    except FileNotFoundError:
        print("Git is not installed or not in PATH.")
        return

    # Find where the git repo is
    git_dir = None
    curr_dir = os.path.abspath(".")
    
    if os.path.exists(os.path.join(curr_dir, ".git")):
        git_dir = curr_dir
    else:
        # Check parents
        parent = os.path.dirname(curr_dir)
        while parent != curr_dir:
            if os.path.exists(os.path.join(parent, ".git")):
                git_dir = parent
                break
            curr_dir = parent
            parent = os.path.dirname(curr_dir)
            
    if not git_dir:
        print("Could not find a .git directory in the current path or parents.")
        
        # Look in subdirectories
        for d in os.listdir("."):
            if os.path.isdir(d) and os.path.exists(os.path.join(d, ".git")):
                print(f"Found .git in subdirectory: {d}")
                git_dir = os.path.abspath(d)
                break
                
    if not git_dir:
        print("No git repo found anywhere. Cannot push to GitHub.")
        return
        
    print(f"Found git repo at: {git_dir}")
    
    # Try to copy main.py to the git repo if it's not the same directory
    main_py_path = os.path.abspath("main.py")
    if not os.path.exists(main_py_path):
        print("main.py not found in current directory!")
        return
        
    target_main = os.path.join(git_dir, "main.py")
    if git_dir != os.path.abspath("."):
        import shutil
        print(f"Copying main.py to {target_main}")
        shutil.copy2(main_py_path, target_main)
        
        # Also copy requirements
        req_path = os.path.abspath("requirements.txt")
        if os.path.exists(req_path):
            shutil.copy2(req_path, os.path.join(git_dir, "requirements.txt"))
            
    # Add, commit, and push
    try:
        print("Adding files to git...")
        subprocess.run(["git", "add", "main.py", "requirements.txt", "render.yaml"], cwd=git_dir, check=True)
        
        print("Committing...")
        subprocess.run(["git", "commit", "-m", "Auto-fix: Add main.py to repository root"], cwd=git_dir, check=False)
        
        print("Pushing to origin...")
        subprocess.run(["git", "push", "origin", "main"], cwd=git_dir, check=True)
        print("Successfully pushed to GitHub! Render should now deploy successfully.")
    except Exception as e:
        print(f"Git operation failed: {e}")

if __name__ == "__main__":
    main()
