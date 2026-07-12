import os
with open("frontend/nemesis_id.html", "r", encoding="utf-8") as f:
    lines = f.readlines()
    for i, line in enumerate(lines):
        if "fetch" in line or "backendUrl" in line or "nemesis-python" in line:
            print(f"{i+1}: {line.strip()}")
