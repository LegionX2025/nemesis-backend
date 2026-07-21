import os
import re

os.makedirs('templates', exist_ok=True)
os.makedirs('static/css', exist_ok=True)
os.makedirs('static/js', exist_ok=True)
os.makedirs('services', exist_ok=True)

with open('index.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find HTML content
match = re.search(r'html_content\s*=\s*r"""(.*?)"""', content, re.DOTALL)
if match:
    html = match.group(1)
    
    with open('templates/index.html', 'w', encoding='utf-8') as f:
        f.write(html)
        
    print("Extracted templates/index.html successfully!")
else:
    print("Could not find html_content in index.py")
