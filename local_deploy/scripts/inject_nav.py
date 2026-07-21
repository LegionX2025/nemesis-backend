import os

target_dir = r"C:\Users\LEGIONX\Downloads\cases\local_deploy\frontend"

def inject_global_nav():
    for filename in os.listdir(target_dir):
        if filename.endswith(".html"):
            filepath = os.path.join(target_dir, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if 'global_nav.js' not in content:
                # Find </head> and insert before it
                if '</head>' in content:
                    new_content = content.replace('</head>', '    <script src="global_nav.js"></script>\n</head>')
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    print(f"Injected into {filename}")
                else:
                    print(f"Skipped {filename} (no </head> tag)")
            else:
                print(f"Already in {filename}")

if __name__ == "__main__":
    inject_global_nav()
