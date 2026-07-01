import os
import shutil

src_dir = r"c:\Users\LEGIONX\Downloads\cases\templates"
dest_dir = r"c:\Users\LEGIONX\Downloads\cases\cloudflare_frontend"

print(f"Syncing from {src_dir} to {dest_dir}...")

if not os.path.exists(dest_dir):
    os.makedirs(dest_dir)

# Also sync the static folder since we modified menu.js
static_src = r"c:\Users\LEGIONX\Downloads\cases\static"
static_dest = os.path.join(dest_dir, "static")
if os.path.exists(static_src):
    print(f"Syncing static assets to {static_dest}...")
    if not os.path.exists(static_dest):
        os.makedirs(static_dest)
    for item in os.listdir(static_src):
        s = os.path.join(static_src, item)
        d = os.path.join(static_dest, item)
        if os.path.isdir(s):
            if os.path.exists(d):
                shutil.rmtree(d)
            shutil.copytree(s, d)
        else:
            shutil.copy2(s, d)

# Sync all html files from templates
for item in os.listdir(src_dir):
    if item.endswith(".html"):
        s = os.path.join(src_dir, item)
        # Handle rename of index.html to nemesis_tracer.html
        if item == "index.html":
            d = os.path.join(dest_dir, "nemesis_tracer.html")
            print("Renaming index.html -> nemesis_tracer.html")
        else:
            d = os.path.join(dest_dir, item)
        shutil.copy2(s, d)
        print(f"Copied {item} -> {os.path.basename(d)}")

# For the new landing page
new_index_src = os.path.join(dest_dir, "new_index.html")
if os.path.exists(new_index_src):
    shutil.copy2(new_index_src, os.path.join(dest_dir, "index.html"))
    print("Copied new_index.html to index.html as the new landing page.")

print("Sync complete!")
