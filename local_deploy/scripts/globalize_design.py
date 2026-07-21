import os
import glob

FRONTEND_DIR = r"C:\Users\LEGIONX\Downloads\cases\local_deploy\frontend"

def globalize_dark_theme():
    html_files = glob.glob(os.path.join(FRONTEND_DIR, "*.html"))
    for file in html_files:
        with open(file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        orig_content = content
        
        # 1. API Endpoint Globalization
        content = content.replace("https://nemesis-api-v3.legionxgaming2021.workers.dev", "")
        
        # 2. Logo Globalization
        content = content.replace("/static/images/logo_nemesis.png", "butterfly_transparent.png")
        content = content.replace("/logo_nemesis.jpeg", "butterfly_transparent.png")
        content = content.replace("../logo_nemesis.jpeg", "butterfly_transparent.png")
        
        # 3. Specifically fix nemesis_id_new.html light theme
        if "nemesis_id_new.html" in file:
            # Body background
            content = content.replace("#f8fafc", "#020617")
            content = content.replace("#f1f5f9", "#0f172a")
            # Tailwind light classes
            content = content.replace("bg-white/80", "bg-slate-900/80")
            content = content.replace("bg-white", "bg-slate-900")
            content = content.replace("bg-slate-50", "bg-slate-800")
            content = content.replace("border-slate-200", "border-slate-700")
            content = content.replace("border-slate-300", "border-slate-600")
            content = content.replace("text-slate-900", "text-slate-100")
            content = content.replace("text-slate-800", "text-slate-200")
            content = content.replace("text-slate-700", "text-slate-300")
            content = content.replace("text-slate-600", "text-slate-400")
            # Fix hardcoded black color for layout
            content = content.replace("color: #0f172a", "color: #f8fafc")
            content = content.replace("rgba(226, 232, 240, 0.8)", "rgba(15, 23, 42, 0.8)")
            content = content.replace("rgba(241, 245, 249, 0.9)", "rgba(2, 6, 23, 0.9)")
            content = content.replace("shadow-lg shadow-black/20", "shadow-lg shadow-cyan-500/20")
            
        if content != orig_content:
            with open(file, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Patched: {os.path.basename(file)}")

if __name__ == "__main__":
    globalize_dark_theme()
