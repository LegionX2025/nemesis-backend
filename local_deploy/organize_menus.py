import os
import glob

# Paths
templates_dir = r"C:\Users\LEGIONX\Downloads\cases\local_deploy\templates"

# 1. Rename the files to standard naming
rename_map = {
    "index.html": "nemesis_tracer.html",
    "tracer_landing.html": "nemesis_tracer_landing.html"
}

for old_name, new_name in rename_map.items():
    old_path = os.path.join(templates_dir, old_name)
    new_path = os.path.join(templates_dir, new_name)
    if os.path.exists(old_path):
        if os.path.exists(new_path):
            os.remove(new_path)
        os.rename(old_path, new_path)
        print(f"Renamed: {old_name} -> {new_name}")

# 2. Update navigation links in all HTML files
# We will standardise the href links to use the exact routes defined in main.py
html_files = glob.glob(os.path.join(templates_dir, "*.html"))

for file_path in html_files:
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content

    # Replace static html links with correct routes
    content = content.replace('href="/nemesis_id.html"', 'href="/nemesis_id"')
    content = content.replace('href="nemesis_id.html"', 'href="/nemesis_id"')
    
    # Also update any potential references to index.html to /
    content = content.replace('href="/index.html"', 'href="/"')
    content = content.replace('href="index.html"', 'href="/"')

    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated links in: {os.path.basename(file_path)}")

print("\nFile organization and Global Menu link updates complete!")
