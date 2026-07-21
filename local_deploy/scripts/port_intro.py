import os

source_file = r"C:\Users\LEGIONX\Downloads\nemesis\tracer_scripts\public\cinematic_intro.html"
target_file = r"C:\Users\LEGIONX\Downloads\cases\local_deploy\frontend\intro.html"

with open(source_file, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Base Theme Colors (body)
content = content.replace('background-color: #f8fafc;', 'background-color: #020617;')
content = content.replace('color: #1e293b;', 'color: #f8fafc;')

# 2. #webgl-bg-container Background (Radial Gradient)
content = content.replace('background: radial-gradient(circle at center, #ffffff 0%, #fef2f2 30%, #f0fdfa 70%, #e2e8f0 100%);', 
                          'background: radial-gradient(circle at center, #0f172a 0%, #020617 100%);')

# 3. #start-screen Background & Text
content = content.replace('background: #ffffff;', 'background: #020617;')
content = content.replace('text-slate-800', 'text-slate-100')

# 4. text-sequence animations
content = content.replace('color: #0f172a;', 'color: #38bdf8;') # seq-1
content = content.replace('color: #1e293b;', 'color: #f8fafc;') # seq-2
content = content.replace('color: #be123c;', 'color: #fb7185;') # seq-3
content = content.replace('color: #475569;', 'color: #94a3b8;') # seq-3 span

# 5. #white-out to Black-out
content = content.replace('background: white;', 'background: #020617;')
content = content.replace('id="white-out"', 'id="black-out"')
content = content.replace('whiteOut', 'blackOut')

# 6. Global Nav Injection
global_header_start = content.find('<!-- GLOBAL HEADER -->')
global_header_end = content.find('</header>') + len('</header>')
if global_header_start != -1 and global_header_end != -1:
    content = content[:global_header_start] + '<!-- GLOBAL HEADER -->\n    <script src="global_nav.js"></script>' + content[global_header_end:]

# 7. Injected Whitepaper Styles
content = content.replace('background-color: #f8fafc; /* Light Theme Base */', 'background-color: #020617; /* Dark Theme Base */')
content = content.replace('color: #334155; /* Slate 700 */', 'color: #94a3b8;')

# Hero section background
content = content.replace('background: linear-gradient(135deg, #ffffff 0%, #f1f5f9 100%);', 'background: linear-gradient(135deg, #0f172a 0%, #020617 100%);')
content = content.replace('border-bottom: 1px solid #e2e8f0;', 'border-bottom: 1px solid #1e293b;')
content = content.replace('color: #64748b;', 'color: #94a3b8;') # hero subtitle

# Glass cards
content = content.replace('background: rgba(255, 255, 255, 0.8);', 'background: rgba(15, 23, 42, 0.7);')
content = content.replace('border: 1px solid rgba(226, 232, 240, 0.8);', 'border: 1px solid rgba(51, 65, 85, 0.6);')
content = content.replace('background: #ffffff;', 'background: #0f172a;') # Mermaid container
content = content.replace('border: 1px solid #e2e8f0;', 'border: 1px solid #1e293b;')
content = content.replace('background: #f0f9ff;', 'background: #0ea5e920;') # feature-icon

# Three.js Fog
content = content.replace('scene.fog = new THREE.FogExp2(0xf8fafc, 0.02);', 'scene.fog = new THREE.FogExp2(0x020617, 0.02);')

# Whitepaper Container BG
content = content.replace('background: #f8fafc;', 'background: #020617;')

# Mermaid Theme
content = content.replace("theme: 'default'", "theme: 'dark'")

# Navigation class (In-page anchor nav)
content = content.replace('bg-white/80', 'bg-slate-900/80')
content = content.replace('border-slate-200', 'border-slate-800')
content = content.replace('text-slate-500 hover:text-slate-900', 'text-slate-400 hover:text-white')

# Typography inside whitepaper
content = content.replace('text-slate-600', 'text-slate-400')
content = content.replace('text-slate-500', 'text-slate-400')
content = content.replace('border-slate-200', 'border-slate-700')
content = content.replace('text-slate-800', 'text-slate-100')
content = content.replace('text-slate-900', 'text-white')
content = content.replace('bg-slate-100', 'bg-slate-800')
content = content.replace('bg-white', 'bg-slate-900') # footer
content = content.replace('border-t border-slate-200', 'border-t border-slate-800')

with open(target_file, 'w', encoding='utf-8') as f:
    f.write(content)

print("Cinematic Intro ported and redesigned successfully.")
