import os
import subprocess

def run_git():
    print("Adding files to git...")
    subprocess.run("git add -f requirements.txt", shell=True)
    subprocess.run("git add main.py", shell=True)
    subprocess.run("git add -u", shell=True)
    
    print("Committing...")
    subprocess.run('git commit -m "Fix mock data and push requirements.txt"', shell=True)
    
    print("Pushing to origin main...")
    subprocess.run("git push origin main", shell=True)
    
    print("Done! Check your Render dashboard, it should be deploying automatically now.")

if __name__ == "__main__":
    run_git()
