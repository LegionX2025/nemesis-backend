import os

TARGET_DIR = r"C:\Users\LEGIONX\Downloads\cases\local_deploy"

def fix_routing():
    for root, dirs, files in os.walk(TARGET_DIR):
        if any(x in root for x in ['node_modules', 'venv', '.git', '.wrangler', '__pycache__']):
            continue
            
        for file in files:
            if file.endswith(".html"):
                path = os.path.join(root, file)
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    modified = False
                    if 'href="index.html"' in content:
                        content = content.replace('href="index.html"', 'href="dashboard.html"')
                        modified = True
                    if "href='index.html'" in content:
                        content = content.replace("href='index.html'", "href='dashboard.html'")
                        modified = True
                    if 'href="/index.html"' in content:
                        content = content.replace('href="/index.html"', 'href="/dashboard.html"')
                        modified = True
                        
                    if modified:
                        with open(path, 'w', encoding='utf-8') as f:
                            f.write(content)
                        print(f"Patched routing: {path}")
                        
                except Exception as e:
                    print(f"Error processing {path}: {e}")

if __name__ == "__main__":
    fix_routing()
    print("Routing fix complete.")
