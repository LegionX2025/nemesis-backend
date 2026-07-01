import re

with open(r'C:\Users\LEGIONX\downloads\cases\templates\index.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

out = []
for i, line in enumerate(lines):
    if 'Highlight Loss Path' in line or 'Court Replay' in line or 'graph' in line.lower() or 'button' in line.lower() or 'flex' in line.lower():
        if 'Highlight' in line or 'Court' in line or 'Replay' in line or 'Loss' in line:
            out.append(f"{i+1}: {line.strip()}")

with open(r'C:\Users\LEGIONX\.gemini\antigravity\brain\aadd294e-cc7f-424d-b7cc-bdcf5823b852\scratch\buttons.md', 'w', encoding='utf-8') as f:
    f.write("\n".join(out))
