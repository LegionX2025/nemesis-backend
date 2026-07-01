import re
with open("templates/index.html", "r", encoding="utf-8") as f:
    content = f.read()
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if re.search(r'Matrix', line, re.IGNORECASE):
            print(f"index.html:{i+1}: {line.strip()}")
