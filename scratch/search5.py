import sys
with open("templates/index.html", "r", encoding="utf-8") as f:
    lines = f.readlines()
for i, line in enumerate(lines):
    if "openDeepEvidencePanel" in line or "deep-evidence-modal" in line or "Deep Technical Evidence" in line:
        print(f"{i+1}: {line.strip()}")
