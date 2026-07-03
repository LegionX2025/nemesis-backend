import os
import re
import glob

def patch_file(filepath):
    print(f"Patching API URLs in {filepath}...")
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Add global BACKEND_URL and WS_URL setup at the start of scripts
    setup_code = """
        // ==========================================
        // DYNAMIC BACKEND ROUTING FOR CLOUDFLARE/LOCAL
        // ==========================================
        const IS_LOCAL = window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1";
        window.BACKEND_URL = IS_LOCAL ? "" : "http://127.0.0.1:8000";
        
        let protocol = window.location.protocol === "https:" ? "wss://" : "ws://";
        window.WS_URL = IS_LOCAL ? (protocol + window.location.host) : "ws://127.0.0.1:8000";
        // ==========================================
"""
    if "DYNAMIC BACKEND ROUTING" not in content:
        # Find the first <script> tag and inject after it
        content = re.sub(r'(<script[^>]*>)', r'\1' + '\n' + setup_code, content, count=1)

    # 2. Patch all fetch('/api/...') -> fetch(window.BACKEND_URL + '/api/...')
    content = re.sub(r'fetch\([\'"`]\/api\/', r'fetch(window.BACKEND_URL + \'/api/', content)
    
    # 3. Patch WebSocket connections
    # Replace: new WebSocket(protocol + window.location.host + "/ws/" + traceId)
    # With: new WebSocket(window.WS_URL + "/ws/" + traceId)
    old_ws = 'ws = new WebSocket(protocol + window.location.host + "/ws/" + traceId);'
    new_ws = 'ws = new WebSocket(window.WS_URL + "/ws/" + traceId);'
    content = content.replace(old_ws, new_ws)
    
    # 4. Patch window.open('/static/templates/...') -> window.open(window.BACKEND_URL + '/static/templates/...')
    content = re.sub(r'window\.open\([\'"`]\/static\/', r'window.open(window.BACKEND_URL + \'/static/', content)
    
    # 5. Patch src="/static/..." -> src="window.BACKEND_URL/static/..." if dynamic, but wait, src is in HTML tags.
    # For HTML tags, we can't easily use window.BACKEND_URL without JS. Since Cloudflare Pages hosts the static files, 
    # `/static/...` or `/assets/...` URLs for images/CSS will work fine relative to the Cloudflare domain!
    # The only things that fail are the API and WS calls.
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Success: {filepath}")

# Find all HTML files in templates directory
templates_dir = r"C:\Users\LEGIONX\Downloads\cases\local_deploy\templates"
for filepath in glob.glob(os.path.join(templates_dir, "*.html")):
    patch_file(filepath)

print("Done patching all templates!")
