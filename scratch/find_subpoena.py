import re

path = r"C:\Users\LEGIONX\downloads\cases\templates\index.html"
with open(path, "r", encoding="utf-8") as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if "doc-subpoena-table" in line or "regional-nuances-body" in line or "doc-signoff-date" in line:
        print(f"Line {i+1}: {line.strip()}")
