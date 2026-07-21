import os
import re

frontend_dir = r"C:\Users\LEGIONX\Downloads\cases\local_deploy\frontend"

def cleanup_files():
    html_files = [f for f in os.listdir(frontend_dir) if f.endswith(".html")]
    
    for filename in html_files:
        filepath = os.path.join(frontend_dir, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        original_content = content
        
        # Fix leading slashes on local files
        content = content.replace('"/global_nav.js"', '"global_nav.js"')
        content = content.replace('"/webgl-butterflies.js"', '"webgl-butterflies.js"')
        
        # Remove light theme css
        content = re.sub(r'<link[^>]+href="[^"]*light-theme\.css"[^>]*>', '', content)
        content = re.sub(r'<link[^>]+href="[^"]*nemesis-light\.css"[^>]*>', '', content)
        
        # Fix intro link in intro.html
        if filename == "intro.html":
            content = content.replace('"/index.html"', '"nemesis_apex_dashboard.html"')
            content = content.replace('butterfly_transparent.png', '../butterfly_transparent.png')
            
        # Fix broken image links
        content = content.replace('"/logo_nemesis.jpeg"', '"../logo_nemesis.jpeg"')
        
        # Fix missing graph engines
        content = content.replace('"/js/nemesis_graph_engine.js"', '"nemesis_graph_engine.js"')
        content = content.replace('"/js/graph_renderer.js"', '"nemesis_graph_engine.js"')

        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Cleaned up: {filename}")

if __name__ == "__main__":
    cleanup_files()
