import os
import glob

def patch_urls():
    target_dir = r"C:\Users\LEGIONX\Downloads\cases\cloudflare_frontend"
    old_url = "https://nemesis-api.legionxgaming2021.workers.dev"
    new_url = "https://nemesis-backend-rwp4.onrender.com"
    old_ws = "wss://nemesis-api.legionxgaming2021.workers.dev"
    new_ws = "wss://nemesis-backend-rwp4.onrender.com"
    
    html_files = glob.glob(os.path.join(target_dir, "*.html"))
    # Also patch js files in static/ if any
    js_files = glob.glob(os.path.join(target_dir, "static", "*.js"))
    for file_path in html_files + js_files:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        original_content = content
        content = content.replace(old_url, new_url)
        content = content.replace(old_ws, new_ws)
        
        # Patch relative API calls introduced in templates
        content = content.replace("fetch('/api/", f"fetch('{new_url}/api/")
        content = content.replace('fetch("/api/', f'fetch("{new_url}/api/')
        
        if content != original_content:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"Patched URLs in {os.path.basename(file_path)}")
            
    print("All frontend files updated to use Render Backend!")

if __name__ == "__main__":
    patch_urls()
