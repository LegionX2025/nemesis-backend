import os
import re

frontend_dir = r"C:\Users\LEGIONX\downloads\cases\nemesis_project\frontend"
includes_dir = r"C:\Users\LEGIONX\downloads\cases\nemesis_project\templates\includes"

# Read include files
includes = {}
for filename in ["head_assets.html", "global_nav.html", "footer.html"]:
    filepath = os.path.join(includes_dir, filename)
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            includes[filename] = f.read()

# Process all html files in frontend
for filename in os.listdir(frontend_dir):
    if filename.endswith(".html"):
        filepath = os.path.join(frontend_dir, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
            
        original_content = content
        
        # Replace {% include 'includes/head_assets.html' %} or similar
        content = re.sub(r"{%\s*include\s*['\"]includes/head_assets\.html['\"]\s*%}", includes.get("head_assets.html", ""), content)
        content = re.sub(r"{%\s*include\s*['\"]includes/global_nav\.html['\"]\s*%}", includes.get("global_nav.html", ""), content)
        content = re.sub(r"{%\s*include\s*['\"]includes/footer\.html['\"]\s*%}", includes.get("footer.html", ""), content)
        
        # Replace Flask url_for('static', filename='path/to/file') with 'static/path/to/file'
        content = re.sub(r"{{\s*url_for\('static',\s*filename=['\"](.*?)['\"]\)\s*}}", r"static/\1", content)
        
        if content != original_content:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"Compiled: {filename}")

print("HTML Compilation complete. All Jinja includes have been resolved statically.")
