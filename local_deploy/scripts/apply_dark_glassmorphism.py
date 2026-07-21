import os
import glob
import re

FRONTEND_DIR = r"C:\Users\LEGIONX\Downloads\cases\local_deploy\frontend"

def apply_global_dark_theme():
    html_files = glob.glob(os.path.join(FRONTEND_DIR, "*.html"))
    for file in html_files:
        with open(file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        orig_content = content
        
        # Strip all light theme variables
        content = content.replace("#f8fafc", "#020617")
        content = content.replace("#f1f5f9", "#0f172a")
        
        # Replace Tailwind generic light classes
        content = re.sub(r'\bbg-white\b', 'bg-slate-900', content)
        content = re.sub(r'\bbg-slate-50\b', 'bg-slate-800', content)
        content = re.sub(r'\bbg-slate-100\b', 'bg-slate-800', content)
        content = re.sub(r'\bbg-slate-200\b', 'bg-slate-700', content)
        content = re.sub(r'\bborder-slate-200\b', 'border-slate-700', content)
        content = re.sub(r'\bborder-slate-300\b', 'border-slate-600', content)
        
        # Replace Tailwind generic text classes
        content = re.sub(r'\btext-slate-900\b', 'text-slate-100', content)
        content = re.sub(r'\btext-slate-800\b', 'text-slate-200', content)
        content = re.sub(r'\btext-slate-700\b', 'text-slate-300', content)
        content = re.sub(r'\btext-slate-600\b', 'text-slate-400', content)
        
        # Ensure nemesis-enterprise.css is linked
        if 'nemesis-enterprise.css' not in content:
            content = content.replace('</head>', '    <link rel="stylesheet" href="nemesis-enterprise.css">\n</head>')

        if content != orig_content:
            with open(file, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Patched dark theme: {os.path.basename(file)}")

if __name__ == "__main__":
    apply_global_dark_theme()
