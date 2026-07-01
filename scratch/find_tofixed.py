import sys

lines = []
with open(r'C:\Users\LEGIONX\downloads\cases\templates\index.html', 'r', encoding='utf-8') as f:
    for i, line in enumerate(f):
        if '.toFixed' in line:
            lines.append(f"{i+1}: {line.strip()}")

with open(r'C:\Users\LEGIONX\downloads\cases\scratch\find_tofixed.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))
