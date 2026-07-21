import sys

TARGET = r"C:\Users\LEGIONX\Downloads\cases\local_deploy\deployer.py"

with open(TARGET, 'r', encoding='utf-8') as f:
    content = f.read()

func_code = """
def setup_github_repo():
    banner("PHASE 0: GITHUB REPOSITORY SETUP")
    github_token = os.environ.get("GITHUB_TOKEN", "")
    if not github_token:
        print("\\n  [i] GITHUB_TOKEN environment variable not set. Skipping automated GitHub repo creation.")
        print("      To enable this, set GITHUB_TOKEN and run again.")
        return

    repo_name = input("  Enter repository name (default: nemesis_v3): ").strip()
    if not repo_name:
        repo_name = "nemesis_v3"
        
    is_private = input("  Make repository private? (y/n, default: y): ").strip().lower() != 'n'

    step("0.1", f"Creating GitHub repository '{repo_name}'...")
    
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    data = {
        "name": repo_name,
        "private": is_private,
        "description": "NEMESIS v3 Cloudflare Deployment"
    }
    
    clone_url = ""
    try:
        req = urllib.request.Request("https://api.github.com/user/repos", data=json.dumps(data).encode('utf-8'), headers=headers, method="POST")
        with urllib.request.urlopen(req) as res:
            response_data = json.loads(res.read().decode('utf-8'))
            clone_url = response_data.get('clone_url')
            ok(f"Created repository: {clone_url}")
    except urllib.error.HTTPError as e:
        if e.code == 422: # Repo already exists
            ok(f"Repository {repo_name} already exists.")
            # Fetch existing repo URL
            req = urllib.request.Request(f"https://api.github.com/user", headers=headers)
            with urllib.request.urlopen(req) as res:
                username = json.loads(res.read().decode('utf-8')).get('login')
                clone_url = f"https://github.com/{username}/{repo_name}.git"
        else:
            print(f"  ✗ Failed to create repository: {e}")
            return
    except Exception as e:
        print(f"  ✗ Failed to create repository: {e}")
        return
        
    step("0.2", "Pushing local code to GitHub...")
    try:
        import subprocess
        subprocess.run(["git", "init"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["git", "add", "."], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["git", "commit", "-m", "Initial NEMESIS v3 commit"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["git", "branch", "-M", "main"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Remove origin if exists
        subprocess.run(["git", "remote", "remove", "origin"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Add remote with token for auth
        auth_url = clone_url.replace("https://", f"https://{github_token}@")
        subprocess.run(["git", "remote", "add", "origin", auth_url], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Push
        subprocess.run(["git", "push", "-u", "origin", "main"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Revert remote to standard URL (remove token)
        subprocess.run(["git", "remote", "set-url", "origin", clone_url], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        ok("Successfully pushed to GitHub!")
    except Exception as e:
        print(f"  ✗ Failed to push code: {e}")

def main():
"""

if "def setup_github_repo()" not in content:
    content = content.replace("def main():", func_code)
    
    main_call = """banner("NEMESIS v2 — COMPLETE CLOUDFLARE AUTO-DEPLOYMENT")
    
    # Run GitHub Automation
    setup_github_repo()
"""
    content = content.replace('banner("NEMESIS v2 — COMPLETE CLOUDFLARE AUTO-DEPLOYMENT")', main_call)
    
    with open(TARGET, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Injected GitHub automation successfully!")
else:
    print("GitHub automation already exists in deployer.py")
