import os
import shutil

def cleanup_for_cloudflare():
    # Remove python_modules which contains compiled C-extensions (like pydantic-core)
    # that break the Cloudflare Pyodide WASM runtime.
    if os.path.exists("python_modules"):
        print("Removing python_modules directory...")
        shutil.rmtree("python_modules")
    
    # Remove pyproject.toml and lock files so wrangler uses requirements.txt 
    # to resolve native Pyodide packages automatically.
    for f in ["pyproject.toml", "pylock.toml", "uv.lock"]:
        if os.path.exists(f):
            print(f"Removing {f}...")
            os.remove(f)
            
    print("Cleanup complete! Now run `npx wrangler deploy` to deploy the Python Worker.")

if __name__ == "__main__":
    cleanup_for_cloudflare()
