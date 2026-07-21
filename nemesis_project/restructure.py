import os
import shutil
import glob
import re

base_dir = r"C:\Users\LEGIONX\downloads\cases\nemesis_project"
os.chdir(base_dir)

# 1. Create frontend/
frontend_dir = os.path.join(base_dir, "frontend")
os.makedirs(frontend_dir, exist_ok=True)

# 2. Move HTML files from templates/ to frontend/
templates_dir = os.path.join(base_dir, "templates")
if os.path.exists(templates_dir):
    for f in glob.glob(os.path.join(templates_dir, "*.html")):
        shutil.move(f, frontend_dir)
    print("Moved HTML files.")

# 3. Move static/ to frontend/
static_dir = os.path.join(base_dir, "static")
if os.path.exists(static_dir):
    frontend_static = os.path.join(frontend_dir, "static")
    if not os.path.exists(frontend_static):
        shutil.move(static_dir, frontend_static)
        print("Moved static directory.")

# 4. Scan and replace URLs in frontend/*.html
html_files = glob.glob(os.path.join(frontend_dir, "*.html"))
for html_file in html_files:
    with open(html_file, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Replace Render URLs with the absolute Cloudflare Worker URL
    content = re.sub(r'https://nemesis-local\.onrender\.com', 'https://nemesis-python-worker.legionxgaming2021.workers.dev', content)
    
    with open(html_file, "w", encoding="utf-8") as f:
        f.write(content)
print("Updated HTML files to point to Python Worker.")

# 5. Delete render.yaml if exists
render_yaml = os.path.join(base_dir, "render.yaml")
if os.path.exists(render_yaml):
    os.remove(render_yaml)
    print("Removed render.yaml")

# 6. Clean .env of Render keys
env_file = os.path.join(base_dir, ".env")
if os.path.exists(env_file):
    with open(env_file, "r", encoding="utf-8") as f:
        lines = f.readlines()
    with open(env_file, "w", encoding="utf-8") as f:
        for line in lines:
            if "RENDER_" not in line.upper():
                f.write(line)
    print("Cleaned .env")

# 7. Update .gitignore
gitignore_file = os.path.join(base_dir, ".gitignore")
if os.path.exists(gitignore_file):
    with open(gitignore_file, "a", encoding="utf-8") as f:
        f.write("\n.wrangler/\ncf_pages_build/\n")
    print("Updated .gitignore")

print("Restructuring complete.")
