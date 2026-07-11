import os
import glob
import re

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
frontend_dir = os.path.join(base_dir, "frontend")

if not os.path.exists(frontend_dir):
    print("Run this script AFTER moving the files into frontend/")
    exit(1)

html_files = glob.glob(os.path.join(frontend_dir, "*.html"))
for html_file in html_files:
    with open(html_file, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Replace Render URLs with the absolute Cloudflare Worker URL
    content = re.sub(r'https://nemesis-local\.onrender\.com', 'https://nemesis-python-worker.legionxgaming2021.workers.dev', content)
    
    with open(html_file, "w", encoding="utf-8") as f:
        f.write(content)

print("[OK] URLs updated to point to the Python Worker: https://nemesis-python-worker.legionxgaming2021.workers.dev")
