import os
import re

TARGET_DIR = r"C:\Users\LEGIONX\Downloads\cases\local_deploy"

LOADER_HTML = """
<!-- GLOBAL NEMESIS AJAX LOADER -->
<div id="global-ajax-loader" style="display: none; position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; background: rgba(0,0,0,0.5); backdrop-filter: blur(5px); z-index: 99999; justify-content: center; align-items: center; flex-direction: column;">
    <img src="assets/butterfly_transparent.png" style="width: 100px; height: 100px; animation: pulse-loader 1.5s infinite; filter: drop-shadow(0 0 20px rgba(6,182,212,0.8));">
    <div style="color: #06b6d4; margin-top: 20px; font-family: monospace; font-size: 16px; font-weight: bold; text-shadow: 0 0 10px #06b6d4;">NEMESIS SINGULARITY KERNEL</div>
    <style>
        @keyframes pulse-loader {
            0% { transform: scale(1); opacity: 0.8; }
            50% { transform: scale(1.1); opacity: 1; filter: drop-shadow(0 0 30px rgba(6,182,212,1)); }
            100% { transform: scale(1); opacity: 0.8; }
        }
    </style>
</div>
<script>
    (function() {
        if (window._nemesisLoaderInitialized) return;
        window._nemesisLoaderInitialized = true;
        const originalFetch = window.fetch;
        window.fetch = async function(...args) {
            const loader = document.getElementById('global-ajax-loader');
            if (loader) loader.style.display = 'flex';
            try {
                const response = await originalFetch.apply(this, args);
                return response;
            } finally {
                if (loader) loader.style.display = 'none';
            }
        };
    })();
</script>
</body>
"""

def patch_html_files():
    for root, dirs, files in os.walk(TARGET_DIR):
        # Exclude node_modules, venv, .git, etc
        if any(x in root for x in ['node_modules', 'venv', '.git', '.wrangler', '__pycache__']):
            continue
            
        for file in files:
            if file.endswith(".html"):
                path = os.path.join(root, file)
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    # 1. Globalize Logo
                    modified = False
                    if "butterfly_v3.png" in content or "LOGO.jpeg" in content:
                        content = content.replace("butterfly_v3.png", "butterfly_transparent.png")
                        content = content.replace("LOGO.jpeg", "butterfly_transparent.png")
                        modified = True
                        
                    # 2. Inject Loader
                    if "global-ajax-loader" not in content and "</body>" in content:
                        content = content.replace("</body>", LOADER_HTML)
                        modified = True
                        
                    if modified:
                        with open(path, 'w', encoding='utf-8') as f:
                            f.write(content)
                        print(f"Patched: {path}")
                        
                except Exception as e:
                    print(f"Error processing {path}: {e}")

if __name__ == "__main__":
    patch_html_files()
    print("Globalization complete.")
