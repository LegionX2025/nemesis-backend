import re

with open(r'C:\Users\LEGIONX\downloads\cases\templates\index.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if 'Highlight Loss Path' in line or 'Court Replay' in line or 'graph' in line.lower():
        if 'Highlight' in line or 'Court' in line:
            print(f"{i+1}: {line.strip()}")
