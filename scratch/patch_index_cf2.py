import os
import glob

frontend_dir = r"C:\Users\LEGIONX\Downloads\cases\cloudflare_frontend"
files = glob.glob(os.path.join(frontend_dir, "*.html"))

for file in files:
    with open(file, "r", encoding="utf-8") as f:
        content = f.read()
    
    # We want to find the pattern:
    # const isLocal = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
    # const baseUrl = isLocal ? 'http://127.0.0.1:3001' : '';
    # const wsUrl = isLocal ? 'ws://127.0.0.1:3001' : ...
    
    # Replace baseUrl fallback:
    if "const baseUrl = isLocal ? 'http://127.0.0.1:3001' : '';" in content:
        content = content.replace(
            "const baseUrl = isLocal ? 'http://127.0.0.1:3001' : '';",
            "const baseUrl = isLocal ? 'http://127.0.0.1:3001' : 'https://nemesis-api.legionxgaming2021.workers.dev';"
        )
    
    if "const wsUrl = isLocal ? 'ws://127.0.0.1:3001' : (window.location.protocol === 'https:' ? 'wss://' : 'ws://') + window.location.host;" in content:
        content = content.replace(
            "const wsUrl = isLocal ? 'ws://127.0.0.1:3001' : (window.location.protocol === 'https:' ? 'wss://' : 'ws://') + window.location.host;",
            "const wsUrl = isLocal ? 'ws://127.0.0.1:3001' : 'wss://nemesis-api.legionxgaming2021.workers.dev';"
        )
        
    with open(file, "w", encoding="utf-8") as f:
        f.write(content)
        
print("Patched HTML files successfully.")
