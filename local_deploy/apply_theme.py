import os
import glob
import re

def process_html_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content

    # 1. Inject Three.js and light-theme.css in <head>
    if '<link rel="stylesheet" href="/light-theme.css">' not in content:
        # Find </head>
        head_injection = """
    <!-- Light Theme & WebGL Overrides -->
    <link rel="stylesheet" href="/light-theme.css">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
"""
        content = content.replace('</head>', head_injection + '</head>')

    # 2. Inject webgl-butterflies.js before </body>
    if '<script src="/webgl-butterflies.js"></script>' not in content:
        body_injection = """
    <!-- WebGL Butterflies Engine -->
    <script src="/webgl-butterflies.js"></script>
"""
        content = content.replace('</body>', body_injection + '</body>')

    # 3. Regex Replacements for Tailwind Dark Mode Classes
    replacements = {
        r'bg-gray-900': 'bg-white',
        r'bg-slate-900': 'bg-white',
        r'bg-slate-800': 'bg-slate-100',
        r'bg-\[\#0f172a\]': 'bg-slate-50',
        r'bg-\[\#020617\]': 'bg-white',
        r'text-white': 'text-slate-800',
        r'text-gray-400': 'text-slate-500',
        r'text-gray-300': 'text-slate-600',
        r'border-gray-800': 'border-slate-200',
        r'border-slate-700': 'border-slate-300',
        r'border-nemesis-border': 'border-blue-200'
    }

    for pattern, replacement in replacements.items():
        # Use regex to match exact class names (word boundaries)
        # We need to be careful with brackets, but \b handles standard characters.
        # Simple string replacement is safer for exact Tailwind classes to avoid breaking text.
        content = re.sub(r'(?<=[\s"\'`])' + pattern + r'(?=[\s"\'`])', replacement, content)

    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"[OK] Updated {os.path.basename(filepath)}")
    else:
        print(f"[SKIP] {os.path.basename(filepath)} already updated or no changes needed.")

if __name__ == "__main__":
    frontend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'frontend')
    print(f"Scanning frontend directory: {frontend_dir}")
    
    html_files = glob.glob(os.path.join(frontend_dir, '*.html'))
    html_files += glob.glob(os.path.join(frontend_dir, '**', '*.html'), recursive=True)
    
    html_files = list(set(html_files)) # deduplicate
    
    print(f"Found {len(html_files)} HTML files. Applying light theme...")
    for f in html_files:
        process_html_file(f)
    print("Theme application complete!")
