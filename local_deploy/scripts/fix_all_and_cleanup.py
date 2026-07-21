import os
import glob
import re
import shutil

HOLOGRAPHIC_STYLE = """    <style>
        body { 
            background-color: #f8fafc !important; 
            background-image: 
                radial-gradient(circle at top right, rgba(59, 130, 246, 0.15), transparent 40%),
                radial-gradient(circle at bottom left, rgba(168, 85, 247, 0.15), transparent 40%),
                linear-gradient(135deg, #f1f5f9 0%, #ffffff 100%);
            color: #0f172a !important; 
            font-family: 'Inter', sans-serif;
        }
        
        /* Premium Glassmorphism Light */
        .glass-panel {
            background: rgba(255, 255, 255, 0.7) !important;
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            border: 1px solid rgba(255, 255, 255, 0.8) !important;
            box-shadow: 0 8px 32px rgba(30, 58, 138, 0.05);
            border-radius: 16px;
        }
        
        .nemesis-btn {
            background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
            color: white;
            border: none;
            box-shadow: 0 4px 15px rgba(59, 130, 246, 0.3);
            transition: all 0.3s ease;
            border-radius: 8px;
            padding: 8px 16px;
            cursor: pointer;
        }
        
        .nemesis-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(59, 130, 246, 0.4);
        }

        .metric-value {
            color: #0f172a;
            font-weight: 800;
            background: linear-gradient(90deg, #1e3a8a, #3b82f6);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .metric-label {
            color: #64748b;
            font-weight: 600;
        }
        
        /* Table styles */
        table {
            width: 100%;
            border-collapse: separate;
            border-spacing: 0 8px;
        }
        th {
            color: #475569;
            text-transform: uppercase;
            font-size: 0.75rem;
            letter-spacing: 0.05em;
            padding: 12px;
            border-bottom: 2px solid #e2e8f0;
        }
        td {
            background: rgba(255, 255, 255, 0.5);
            padding: 16px 12px;
            color: #1e293b;
        }
        tr td:first-child { border-top-left-radius: 8px; border-bottom-left-radius: 8px; }
        tr td:last-child { border-top-right-radius: 8px; border-bottom-right-radius: 8px; }
        
        /* Override Cytoscape Canvas Background */
        #nemesis-graph {
            background: transparent !important;
            border-radius: 16px;
        }
    </style>"""

def process_html_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    original_content = content
    style_pattern = re.compile(r'<style>.*?</style>', re.DOTALL)
    if style_pattern.search(content):
        content = style_pattern.sub(HOLOGRAPHIC_STYLE, content)
    else:
        content = content.replace('</head>', HOLOGRAPHIC_STYLE + '\n</head>')
    if '<link rel="stylesheet" href="/light-theme.css">' not in content:
        content = content.replace('</head>', '\n    <link rel="stylesheet" href="/light-theme.css">\n</head>')
    replacements = {
        r'bg-gray-900': 'bg-slate-50', r'bg-slate-900': 'bg-slate-50', r'bg-slate-800': 'glass-panel',
        r'bg-\[\#0f172a\]': 'bg-slate-50', r'bg-\[\#020617\]': 'bg-slate-50', r'text-white': 'text-slate-900',
        r'text-gray-400': 'text-slate-500', r'text-gray-300': 'text-slate-600', r'text-slate-400': 'text-slate-500',
        r'border-gray-800': 'border-slate-200', r'border-slate-700': 'border-slate-200', r'border-nemesis-border': 'border-blue-200',
        r'https://nemesis-backend\.legionxgaming2021\.workers\.dev': 'https://nemesis-api-v3.legionxgaming2021.workers.dev',
        r'https://nemesis-api\.legionxgaming2021\.workers\.dev': 'https://nemesis-api-v3.legionxgaming2021.workers.dev'
    }
    for pattern, replacement in replacements.items():
        content = re.sub(r'(?<=[\s"\'`])' + pattern + r'(?=[\s"\'`])', replacement, content)
        
    # Inject API_BASE and BACKEND_URL globally in head if missing
    if 'window.BACKEND_URL' not in content:
        url_script = """
    <script>
        const IS_LOCAL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
        window.BACKEND_URL = IS_LOCAL ? 'http://127.0.0.1:8088' : 'https://nemesis-api-v3.legionxgaming2021.workers.dev';
        window.API_BASE = window.BACKEND_URL;
    </script>
        """
        content = content.replace('</head>', url_script + '\\n</head>')
    else:
        # If API_BASE is missing, add it
        if 'window.API_BASE' not in content:
             content = re.sub(r'(window\.BACKEND_URL = .*?;)', r'\1\n        window.API_BASE = window.BACKEND_URL;', content)

    # Fix hardcoded API_BASE that isn't window.API_BASE in fetch calls
    content = content.replace('`${API_BASE}', '`${window.API_BASE}')
    content = content.replace('`${BACKEND_URL}', '`${window.BACKEND_URL}')

    content = re.sub(r"initNemesisGraph\(([^,]+),\s*([^,]+),\s*['\"]dark['\"]\)", r"initNemesisGraph(\1, \2, 'light')", content)
    
    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  [OK] Updated design in {os.path.basename(filepath)}")

def cleanup_vercel_render(root_dir):
    print("\\n[*] Removing Vercel and Render footprints...")
    to_delete_files = ["vercel.json", "render.yaml", "render.yml"]
    to_delete_dirs = [".vercel"]
    
    # Check both root and frontend dirs
    dirs_to_check = [root_dir, os.path.join(root_dir, 'frontend')]
    
    for d in dirs_to_check:
        for f in to_delete_files:
            path = os.path.join(d, f)
            if os.path.exists(path):
                os.remove(path)
                print(f"  [OK] Deleted file: {path}")
        for dp in to_delete_dirs:
            path = os.path.join(d, dp)
            if os.path.exists(path):
                shutil.rmtree(path)
                print(f"  [OK] Deleted directory: {path}")
    print("[*] Vercel and Render successfully purged.")

if __name__ == "__main__":
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    frontend_dir = os.path.join(root_dir, 'frontend')
    
    # 1. Cleanup
    cleanup_vercel_render(root_dir)
    
    # 2. Fix UI
    print("\\n[*] Applying Holographic Light Theme globally...")
    html_files = glob.glob(os.path.join(frontend_dir, '*.html'))
    for f in html_files:
        process_html_file(f)
    print("[*] Theme application complete.")
