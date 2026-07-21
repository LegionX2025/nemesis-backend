import os
import re

frontend_dir = r"C:\Users\LEGIONX\Downloads\cases\local_deploy\frontend"

def audit_files():
    html_files = [f for f in os.listdir(frontend_dir) if f.endswith(".html")]
    
    missing_assets = set()
    broken_links = set()
    
    for filename in html_files:
        filepath = os.path.join(frontend_dir, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
            # Find hrefs
            hrefs = re.findall(r'href="([^"]+)"', content)
            for href in hrefs:
                if href.startswith('http') or href.startswith('#') or href.startswith('mailto:'): continue
                # Remove query params or anchors
                clean_href = href.split('?')[0].split('#')[0]
                if clean_href and not os.path.exists(os.path.join(frontend_dir, clean_href)):
                    broken_links.add(f"{filename} -> {clean_href}")
                    
            # Find srcs (scripts, imgs)
            srcs = re.findall(r'src="([^"]+)"', content)
            for src in srcs:
                if src.startswith('http') or src.startswith('data:'): continue
                clean_src = src.split('?')[0].split('#')[0]
                if clean_src and not os.path.exists(os.path.join(frontend_dir, clean_src)):
                    missing_assets.add(f"{filename} -> {clean_src}")

    print("=== AUDIT REPORT ===")
    print(f"Total HTML files checked: {len(html_files)}")
    print(f"\nMissing Assets ({len(missing_assets)}):")
    for asset in sorted(list(missing_assets)): print(f" - {asset}")
    
    print(f"\nBroken Local Links ({len(broken_links)}):")
    for link in sorted(list(broken_links)): print(f" - {link}")

if __name__ == "__main__":
    audit_files()
