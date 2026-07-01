import os

path = r'C:\Users\LEGIONX\downloads\cases\templates\index.html'
with open(path, 'r', encoding='utf-8') as f:
    for i, line in enumerate(f):
        if 'openDeepEvidencePanel' in line:
            print(f"index.html:{i+1}:{line.strip()}")
