import os
import glob
import re

ROOT_DIR = r"C:\Users\LEGIONX\Downloads\cases\nemesis_project"
FRONTEND_DIR = os.path.join(ROOT_DIR, "frontend")

# 1. Delete Legacy Files
legacy_files = [
    os.path.join(ROOT_DIR, "render.yaml"),
    os.path.join(ROOT_DIR, "auto_deploy.py"),
]
for lf in legacy_files:
    if os.path.exists(lf):
        os.remove(lf)
        print(f"Deleted {lf}")

# 2. Replace onrender.com URLs
def replace_in_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        new_content = re.sub(r'https://nemesis-[a-zA-Z0-9-]+\.onrender\.com', '/api', content)
        
        if new_content != content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"Replaced Render URLs in {filepath}")
    except Exception as e:
        print(f"Failed processing {filepath}: {e}")

# Scan frontend files
html_files = glob.glob(os.path.join(FRONTEND_DIR, "*.html"))
js_files = glob.glob(os.path.join(FRONTEND_DIR, "**", "*.js"), recursive=True)
env_file = os.path.join(FRONTEND_DIR, ".env")
env_root = os.path.join(ROOT_DIR, ".env")

for f in html_files + js_files + [env_file, env_root]:
    if os.path.exists(f):
        replace_in_file(f)

# Move any loose HTML files to frontend
loose_htmls = glob.glob(os.path.join(ROOT_DIR, "*.html"))
for html in loose_htmls:
    # skip report
    if "Forensic_Report" in html: continue
    base = os.path.basename(html)
    dest = os.path.join(FRONTEND_DIR, base)
    os.rename(html, dest)
    print(f"Moved {base} to frontend/")

# 3. Backend Refactoring (main.py)
main_py = os.path.join(ROOT_DIR, "main.py")
if os.path.exists(main_py):
    with open(main_py, 'r', encoding='utf-8') as f:
        main_content = f.read()
    
    # Check if entrypoint already exists
    if "class Default(WorkerEntrypoint):" not in main_content:
        # Append the ASGI wrapper
        entrypoint_code = """

# --- CLOUDFLARE WORKERS V8 ISOLATE ENTRYPOINT ---
from javascript import asgi
from workers import WorkerEntrypoint

class Default(WorkerEntrypoint):
    async def fetch(self, request):
        return await asgi.fetch(app, request, self.env)
"""
        with open(main_py, 'a', encoding='utf-8') as f:
            f.write(entrypoint_code)
        print("Appended Cloudflare Worker Entrypoint to main.py")

# 4. Create wrangler.toml
wrangler_toml = os.path.join(ROOT_DIR, "wrangler.toml")
wrangler_content = """name = "nemesis-backend"
main = "main.py"
compatibility_date = "2026-07-12"
compatibility_flags = ["python_workers"]

# D1 Databases
[[d1_databases]]
binding = "DB"
database_name = "nemesis_audit_db"
database_id = "80acedab-33c2-4637-bee7-6b9a1176a463"

[[d1_databases]]
binding = "NEMESIS_DB_PRIMARY"
database_name = "nemesis"
database_id = "73ef6e7d-9499-4d59-a190-ae7220873a71"

[[d1_databases]]
binding = "NEMESIS_DB_SECONDARY"
database_name = "nemesis-db"
database_id = "860655f8-aa37-4d4f-92a9-b5ea49bc101a"

# Hyperdrive
[[hyperdrive]]
binding = "HYPERDRIVE"
id = "2bf62864eaf64708b5a349169d6efc7e"
localConnectionString = "postgresql://admin:!Nemesis2026@ep-morning-glitter-adpz0uqn-pooler.c-2.us-east-1.aws.neon.tech:5432/intelligence"
"""
with open(wrangler_toml, 'w', encoding='utf-8') as f:
    f.write(wrangler_content)
print("Created wrangler.toml")

# 5. Create pyproject.toml
pyproject_toml = os.path.join(ROOT_DIR, "pyproject.toml")
pyproject_content = """[project]
name = "nemesis-backend"
version = "1.0.0"
dependencies = [
    "fastapi",
    "pydantic",
    "google-genai",
    "aiohttp",
    "python-multipart"
]

[dependency-groups]
dev = [
    "workers-py"
]
"""
with open(pyproject_toml, 'w', encoding='utf-8') as f:
    f.write(pyproject_content)
print("Created pyproject.toml")

print("Migration script completed.")
